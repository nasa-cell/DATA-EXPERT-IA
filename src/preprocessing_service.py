"""Exploración y preprocesamiento real de datos: nulos, duplicados, codificación y escalado.

Todas las transformaciones se aplican de verdad sobre el DataFrame (nada se simula) y se
registra un resumen "antes/después" más la lista de transformaciones realizadas, para que
la interfaz explique qué hizo el sistema.

El DataFrame preprocesado se usa para la estadística, los valores atípicos y los gráficos.
Para entrenar se parte de los datos limpios SIN escalar ni rellenar (ver preparar_para_modelo):
esos dos pasos los repite el modelo aprendiendo solo de la parte de entrenamiento, para que
la parte de prueba no influya en nada de lo que aprende.
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


def limpiar_objetivo(df: pd.DataFrame, objetivo: str):
    """Quita las filas sin valor en el objetivo (no se puede aprender de ellas ni inventarles
    un valor) y, si el objetivo es numérico con decimales pero todos sus valores son enteros
    (típico de una columna 0/1 con huecos, que pandas lee como decimal), lo pasa a entero.
    Devuelve el DataFrame y cuántas filas se quitaron."""
    sin_objetivo = int(df[objetivo].isnull().sum())
    if sin_objetivo:
        df = df[df[objetivo].notnull()].reset_index(drop=True)
    serie = df[objetivo]
    if pd.api.types.is_float_dtype(serie) and len(serie) and np.all(np.mod(serie, 1) == 0):
        df = df.copy()
        df[objetivo] = serie.astype(int)
    return df, sin_objetivo


def _texto_filas_sin_objetivo(cantidad: int, objetivo: str) -> str:
    return (f'Se quitaron {cantidad} fila(s) sin valor en la variable objetivo "{objetivo}": el modelo no '
            "puede aprender de un caso cuyo resultado no se conoce, y rellenarlo con un promedio sería inventarlo.")


def _info_columnas(df: pd.DataFrame, objetivo: str):
    """Columnas que la persona tendrá que completar para predecir un caso nuevo."""
    numericas, categoricas = _tipos_columnas(df)
    return [
        {"columna": c, "tipo": "numerica", "categorias": None} for c in numericas if c != objetivo
    ] + [
        {"columna": c, "tipo": "categorica", "categorias": sorted(str(v) for v in df[c].dropna().unique())}
        for c in categoricas if c != objetivo
    ]


def _codificar_objetivo(serie: pd.Series):
    """LabelEncoder para un objetivo de texto; devuelve la serie codificada y el mapeo número -> categoría."""
    encoder = LabelEncoder()
    codificada = encoder.fit_transform(serie.astype(str))
    return codificada, {int(i): clase for i, clase in enumerate(encoder.classes_)}


def preprocesar(df: pd.DataFrame, objetivo: str) -> dict:
    """Preprocesa `df` de verdad: nulos, duplicados, codificación y normalización.

    Devuelve el DataFrame resultante junto con el resumen antes/después y la lista de
    transformaciones aplicadas, para mostrarlas en la interfaz.
    """
    transformaciones = []
    original = df

    # Las columnas que solo identifican a la persona (Nombre, Name...) no aportan a la
    # predicción y con un nombre distinto por fila el modelo solo memorizaría; se dejan fuera.
    columnas_nombre = [c for c in df.columns if c != objetivo and es_columna_nombre(c)]
    if columnas_nombre:
        df = df.drop(columns=columnas_nombre)
        transformaciones.append(
            f"Columna(s) {columnas_nombre} solo identifican a la persona: no se usan para entrenar el modelo."
        )

    antes = {
        "filas": int(df.shape[0]),
        "columnas": int(df.shape[1]),
        "nulos": int(df.isnull().sum().sum()),
        "duplicados": int(df.duplicated().sum()),
    }

    df, sin_objetivo = limpiar_objetivo(df, objetivo)
    if sin_objetivo:
        transformaciones.append(_texto_filas_sin_objetivo(sin_objetivo, objetivo))

    numericas, categoricas = _tipos_columnas(df)
    info_columnas_originales = _info_columnas(df, objetivo)
    resultado = df.copy()

    # --- Valores nulos: media para numéricas, moda para categóricas (nunca en el objetivo) ---
    for columna in [c for c in numericas if c != objetivo]:
        nulos = int(resultado[columna].isnull().sum())
        if nulos > 0:
            media = resultado[columna].mean()
            resultado[columna] = resultado[columna].fillna(media)
            transformaciones.append(
                f'Columna numérica "{columna}": {nulos} valor(es) nulo(s) reemplazados por la media ({media:.3f}).'
            )

    for columna in [c for c in categoricas if c != objetivo]:
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
    for columna in [c for c in categoricas if c != objetivo]:
        n_unicos = resultado[columna].nunique()
        if n_unicos <= 2:
            resultado[columna] = LabelEncoder().fit_transform(resultado[columna].astype(str))
            transformaciones.append(
                f'Columna "{columna}": sus {n_unicos} categorías se cambiaron por números (0, 1...), porque '
                "los modelos solo entienden números, no texto (técnica: LabelEncoder)."
            )
        else:
            dummies = pd.get_dummies(resultado[columna], prefix=columna, dtype=int)
            resultado = pd.concat([resultado.drop(columns=[columna]), dummies], axis=1)
            transformaciones.append(
                f'Columna "{columna}": como tiene {n_unicos} categorías (más de 2), se convirtió en '
                f"{dummies.shape[1]} columnas nuevas de sí/no (una por categoría), en vez de asignarle "
                "números que el modelo podría malinterpretar como un orden (técnica: OneHotEncoder)."
            )

    # El objetivo, si es categórico, se codifica aparte con LabelEncoder (necesario para
    # entrenar un modelo de clasificación), preservando el mapeo para poder interpretarlo.
    mapeo_objetivo = None
    if objetivo in categoricas:
        resultado[objetivo], mapeo_objetivo = _codificar_objetivo(resultado[objetivo])
        transformaciones.append(
            f'Variable objetivo "{objetivo}": sus categorías de texto se cambiaron por números para poder '
            f"entrenar el modelo, guardando a qué categoría original corresponde cada número: {mapeo_objetivo}."
        )

    # --- Normalización de las variables numéricas (sin incluir el objetivo) ---
    columnas_a_escalar = [
        c for c in resultado.select_dtypes(include=[np.number]).columns if c != objetivo
    ]
    if columnas_a_escalar:
        resultado[columnas_a_escalar] = StandardScaler().fit_transform(resultado[columnas_a_escalar])
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
        "muestra_antes": original.head(5).replace({np.nan: None}).to_dict(orient="records"),
        "muestra_despues": resultado.head(5).replace({np.nan: None}).to_dict(orient="records"),
        "info_columnas_originales": info_columnas_originales,
    }


def preparar_para_modelo(df: pd.DataFrame, objetivo: str) -> dict:
    """Datos para entrenar: los mismos pasos de limpieza que preprocesar() (columnas de nombre,
    filas sin objetivo, duplicados, objetivo de texto a números con el mismo mapeo), pero SIN
    rellenar nulos, codificar ni escalar: eso lo hace el Pipeline del modelo ajustándose solo
    con la parte de entrenamiento (ver machine_learning_service)."""
    columnas_nombre = [c for c in df.columns if c != objetivo and es_columna_nombre(c)]
    df = df.drop(columns=columnas_nombre)
    df, _ = limpiar_objetivo(df, objetivo)
    df = df.drop_duplicates().reset_index(drop=True)

    numericas, categoricas = _tipos_columnas(df)
    numericas = [c for c in numericas if c != objetivo]
    categoricas_features = [c for c in categoricas if c != objetivo]
    # Las categorías se comparan como texto, igual que las opciones que ve la persona al predecir.
    for columna in categoricas_features:
        df[columna] = df[columna].map(lambda v: v if pd.isnull(v) else str(v)).astype(object)

    mapeo_objetivo = None
    if objetivo in categoricas:
        df[objetivo], mapeo_objetivo = _codificar_objetivo(df[objetivo])

    return {"df": df, "numericas": numericas, "categoricas": categoricas_features, "mapeo_objetivo": mapeo_objetivo}


def caso_a_dataframe(valores: dict, info_columnas: list) -> pd.DataFrame:
    """Convierte los valores "crudos" de un caso nuevo (como los cargaría una persona a mano o
    vienen en un CSV) en una fila con las columnas originales. El Pipeline del modelo ya
    entrenado se encarga de codificarla y escalarla exactamente como aprendió."""
    fila = {}
    for info in info_columnas:
        columna = info["columna"]
        valor = valores.get(columna)
        if info["tipo"] == "numerica":
            try:
                numero = float(str(valor).replace(",", ".")) if isinstance(valor, str) else float(valor)
            except (TypeError, ValueError):
                raise ValueError(f'"{columna}" debe ser un número.')
            if np.isnan(numero):
                raise ValueError(f'Falta el valor de "{columna}".')
            fila[columna] = numero
        else:
            texto = "" if valor is None or (isinstance(valor, float) and np.isnan(valor)) else str(valor)
            if texto not in info["categorias"]:
                opciones = ", ".join(info["categorias"])
                raise ValueError(f'Valor "{texto}" no reconocido para "{columna}". Opciones válidas: {opciones}.')
            fila[columna] = texto
    return pd.DataFrame([fila], columns=[i["columna"] for i in info_columnas])
