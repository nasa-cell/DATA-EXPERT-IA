"""Exploración y preprocesamiento real de datos: nulos, duplicados, codificación y escalado.

Todas las transformaciones se aplican de verdad sobre el DataFrame (nada se simula) y se
registra un resumen "antes/después" más la lista de transformaciones realizadas, para que
la interfaz explique qué hizo el sistema.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler


def _tipos_columnas(df: pd.DataFrame):
    numericas = df.select_dtypes(include=[np.number]).columns.tolist()
    categoricas = df.select_dtypes(exclude=[np.number]).columns.tolist()
    return numericas, categoricas


def explorar_dataset(df: pd.DataFrame, objetivo: str = None) -> dict:
    """Exploración con Pandas: head, tail, shape, tipos, nulos, duplicados y describe."""
    numericas, categoricas = _tipos_columnas(df)

    describe = df.describe(include="all").fillna("").to_dict()
    describe_por_columna = {
        columna: {estadistico: valor for estadistico, valor in valores.items()}
        for columna, valores in describe.items()
    }

    return {
        "filas": int(df.shape[0]),
        "columnas": int(df.shape[1]),
        "nombres_columnas": df.columns.tolist(),
        "tipos_datos": {c: str(t) for c, t in df.dtypes.items()},
        "columnas_numericas": numericas,
        "columnas_categoricas": categoricas,
        "objetivo": objetivo,
        "nulos_por_columna": {c: int(v) for c, v in df.isnull().sum().items()},
        "total_nulos": int(df.isnull().sum().sum()),
        "duplicados": int(df.duplicated().sum()),
        "head": df.head(5).replace({np.nan: None}).to_dict(orient="records"),
        "tail": df.tail(5).replace({np.nan: None}).to_dict(orient="records"),
        "describe": describe_por_columna,
    }


def es_columna_nombre(columna) -> bool:
    return str(columna).strip().lower() in ("nombre", "nombres", "name", "alumno", "estudiante")


def preprocesar(df: pd.DataFrame, objetivo: str) -> dict:
    """Preprocesa `df` de verdad: nulos, duplicados, codificación y normalización.

    Devuelve el DataFrame resultante junto con el resumen antes/después y la lista de
    transformaciones aplicadas, para mostrarlas en la interfaz.
    """
    transformaciones = []

    # Las columnas que solo identifican a la persona (Nombre, Name...) no aportan a la
    # predicción y con un nombre distinto por fila el modelo solo memorizaría; se dejan fuera.
    columnas_nombre = [c for c in df.columns if c != objetivo and es_columna_nombre(c)]
    if columnas_nombre:
        df = df.drop(columns=columnas_nombre)
        transformaciones.append(
            f"Columna(s) {columnas_nombre} solo identifican a la persona: no se usan para entrenar el modelo."
        )
    numericas, categoricas = _tipos_columnas(df)

    # Se van guardando los objetos ya ajustados (encoders, scaler) y qué columna es cada cosa,
    # para poder transformar un caso nuevo (cargado a mano) EXACTAMENTE igual que se transformó
    # el dataset de entrenamiento — ver transformar_caso_nuevo() más abajo.
    categoricas_features_orig = [c for c in categoricas if c != objetivo]
    info_columnas_originales = [
        {"columna": c, "tipo": "numerica", "categorias": None} for c in numericas if c != objetivo
    ] + [
        {"columna": c, "tipo": "categorica", "categorias": sorted(str(v) for v in df[c].dropna().unique())}
        for c in categoricas_features_orig
    ]
    encoders_binarios = {}
    columnas_onehot = {}

    antes = {
        "filas": int(df.shape[0]),
        "columnas": int(df.shape[1]),
        "nulos": int(df.isnull().sum().sum()),
        "duplicados": int(df.duplicated().sum()),
    }

    resultado = df.copy()

    # --- Valores nulos: media para numéricas, moda para categóricas ---
    for columna in numericas:
        nulos = int(resultado[columna].isnull().sum())
        if nulos > 0:
            media = resultado[columna].mean()
            resultado[columna] = resultado[columna].fillna(media)
            transformaciones.append(
                f'Columna numérica "{columna}": {nulos} valor(es) nulo(s) reemplazados por la media ({media:.3f}).'
            )

    for columna in categoricas:
        nulos = int(resultado[columna].isnull().sum())
        if nulos > 0:
            moda = resultado[columna].mode().iloc[0]
            resultado[columna] = resultado[columna].fillna(moda)
            transformaciones.append(
                f'Columna categórica "{columna}": {nulos} valor(es) nulo(s) reemplazados por la moda ("{moda}").'
            )

    # --- Duplicados ---
    duplicados_antes = int(resultado.duplicated().sum())
    if duplicados_antes > 0:
        resultado = resultado.drop_duplicates().reset_index(drop=True)
        transformaciones.append(f"Se eliminaron {duplicados_antes} fila(s) duplicada(s).")

    # --- Codificación de variables categóricas (excepto el objetivo) ---
    categoricas_features = [c for c in categoricas if c != objetivo]
    for columna in categoricas_features:
        n_unicos = resultado[columna].nunique()
        if n_unicos <= 2:
            encoder = LabelEncoder()
            resultado[columna] = encoder.fit_transform(resultado[columna])
            encoders_binarios[columna] = encoder
            transformaciones.append(
                f'Columna "{columna}": sus {n_unicos} categorías se cambiaron por números (0, 1...), porque '
                "los modelos solo entienden números, no texto (técnica: LabelEncoder)."
            )
        else:
            dummies = pd.get_dummies(resultado[columna], prefix=columna, dtype=int)
            resultado = pd.concat([resultado.drop(columns=[columna]), dummies], axis=1)
            columnas_onehot[columna] = dummies.columns.tolist()
            transformaciones.append(
                f'Columna "{columna}": como tiene {n_unicos} categorías (más de 2), se convirtió en '
                f"{dummies.shape[1]} columnas nuevas de sí/no (una por categoría), en vez de asignarle "
                "números que el modelo podría malinterpretar como un orden (técnica: OneHotEncoder)."
            )

    # El objetivo, si es categórico, se codifica aparte con LabelEncoder (necesario para
    # entrenar un modelo de clasificación), preservando el mapeo para poder interpretarlo.
    mapeo_objetivo = None
    if objetivo in categoricas:
        encoder_objetivo = LabelEncoder()
        resultado[objetivo] = encoder_objetivo.fit_transform(resultado[objetivo])
        mapeo_objetivo = {int(i): clase for i, clase in enumerate(encoder_objetivo.classes_)}
        transformaciones.append(
            f'Variable objetivo "{objetivo}": sus categorías de texto se cambiaron por números para poder '
            f"entrenar el modelo, guardando a qué categoría original corresponde cada número: {mapeo_objetivo}."
        )

    # --- Normalización de las variables numéricas (sin incluir el objetivo) ---
    columnas_a_escalar = [
        c for c in resultado.select_dtypes(include=[np.number]).columns if c != objetivo
    ]
    scaler = None
    if columnas_a_escalar:
        scaler = StandardScaler()
        resultado[columnas_a_escalar] = scaler.fit_transform(resultado[columnas_a_escalar])
        transformaciones.append(
            f"Se pusieron {len(columnas_a_escalar)} columna(s) numérica(s) en una misma escala común "
            "(promedio 0, dispersión 1), para que una variable con números grandes (como un sueldo) no "
            "pese más que otra con números chicos (como una edad) solo por su tamaño (técnica: StandardScaler)."
        )

    despues = {
        "filas": int(resultado.shape[0]),
        "columnas": int(resultado.shape[1]),
        "nulos": int(resultado.isnull().sum().sum()),
        "duplicados": int(resultado.duplicated().sum()),
    }

    return {
        "df": resultado,
        "antes": antes,
        "despues": despues,
        "transformaciones": transformaciones,
        "mapeo_objetivo": mapeo_objetivo,
        "muestra_antes": df.head(5).replace({np.nan: None}).to_dict(orient="records"),
        "muestra_despues": resultado.head(5).replace({np.nan: None}).to_dict(orient="records"),
        "info_columnas_originales": info_columnas_originales,
        # Objetos ya ajustados: se usan para transformar un caso nuevo después de entrenar
        # (ver transformar_caso_nuevo), nunca se mandan al navegador como JSON.
        "transformadores": {
            "encoders_binarios": encoders_binarios,
            "columnas_onehot": columnas_onehot,
            "columnas_numericas_originales": [c for c in numericas if c != objetivo],
            "scaler": scaler,
            "columnas_escaladas": columnas_a_escalar,
        },
    }


def transformar_caso_nuevo(valores: dict, transformadores: dict, columnas_features: list) -> pd.DataFrame:
    """Convierte un único caso nuevo (valores "crudos", como los cargaría una persona a mano)
    aplicando EXACTAMENTE los mismos pasos y objetos ya ajustados que se usaron al preprocesar
    el dataset de entrenamiento (mismos encoders, mismo scaler), para que el modelo lo reciba en
    el formato que espera. Nunca se ajusta un encoder/scaler nuevo acá: si no, la codificación o
    la escala no coincidirían con las que aprendió el modelo."""
    fila = {}

    for columna, encoder in transformadores["encoders_binarios"].items():
        valor_crudo = valores.get(columna)
        try:
            fila[columna] = int(encoder.transform([valor_crudo])[0])
        except ValueError:
            categorias = ", ".join(str(c) for c in encoder.classes_)
            raise ValueError(f'Valor "{valor_crudo}" no reconocido para "{columna}". Opciones válidas: {categorias}.')

    for columna, columnas_dummy in transformadores["columnas_onehot"].items():
        valor_crudo = str(valores.get(columna))
        for nombre_dummy in columnas_dummy:
            categoria = nombre_dummy[len(columna) + 1:]  # "columna_categoria" -> "categoria"
            fila[nombre_dummy] = 1 if categoria == valor_crudo else 0

    for columna in transformadores["columnas_numericas_originales"]:
        valor_crudo = valores.get(columna)
        try:
            fila[columna] = float(valor_crudo)
        except (TypeError, ValueError):
            raise ValueError(f'"{columna}" debe ser un número.')

    df_fila = pd.DataFrame([fila])

    scaler = transformadores.get("scaler")
    columnas_escaladas = [c for c in (transformadores.get("columnas_escaladas") or []) if c in df_fila.columns]
    if scaler is not None and columnas_escaladas:
        df_fila[columnas_escaladas] = scaler.transform(df_fila[columnas_escaladas])

    # Reordena y completa con 0 cualquier columna dummy que no haya aparecido en este caso
    # puntual, para que coincida exactamente con las columnas que vio el modelo al entrenar.
    return df_fila.reindex(columns=columnas_features, fill_value=0)
