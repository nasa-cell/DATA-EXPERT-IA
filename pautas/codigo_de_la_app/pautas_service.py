"""Pautas de la actividad del curso, una por una, con su resultado, sus gráficos y su conclusión.

La actividad pide, sobre el dataset de semillas de trigo (7 características y la variedad):
  1. Cargar y explorar con Pandas: las 7 características y los valores nulos.
  2. Separar las características de la variable objetivo y normalizar con StandardScaler.
  3. NumPy: vectores, matrices, producto punto, norma y un sistema de ecuaciones.
  4. Media, mediana, varianza y desviación de área y perímetro (varianza y desviación de área
     también a mano, comparadas con NumPy).
  5. Valores atípicos de área con el criterio de dos desviaciones estándar.
  6. Histograma de área y dispersión de área contra perímetro, por variedad.
  7. K-Vecinos contra Árbol de Decisión, comparados por Accuracy.

Cada pauta se arma con lo que ya calculó el análisis del dataset (no se recalcula nada): si el
paso que la responde todavía no se hizo, la pauta dice cuál falta.
"""

import numpy as np
import pandas as pd

from src import statistics_service as stats

AREA = "área"
PERIMETRO = "perímetro"

# Paso del análisis que responde cada pauta (y su nombre en la pantalla).
PASOS = {
    1: ("explorar", "Explorar datos"),
    2: ("preprocesar", "Preprocesar"),
    3: ("algebra", "Álgebra lineal"),
    4: ("estadistica", "Estadística"),
    5: ("outliers", "Valores atípicos"),
    6: ("graficos", "Gráficos"),
    7: ("entrenar", "Entrenar modelo"),
}

TITULOS = {
    1: "Cargar y explorar el dataset con Pandas",
    2: "Separar la variable objetivo y normalizar con StandardScaler",
    3: "NumPy: vectores, matrices, producto punto, norma y sistema de ecuaciones",
    4: "Media, mediana, varianza y desviación de área y perímetro",
    5: "Valores atípicos de área (dos desviaciones estándar)",
    6: "Histograma de área y dispersión área contra perímetro",
    7: "K-Vecinos contra Árbol de Decisión (Accuracy)",
}


def aplica(meta: dict, df: pd.DataFrame) -> bool:
    """La sección aparece sólo en datasets con área, perímetro y una variable objetivo."""
    return bool(meta.get("objetivo")) and {AREA, PERIMETRO, meta["objetivo"]}.issubset(df.columns)


def _n(valor, decimales=3):
    """Número con coma decimal, como se escribe en español."""
    return f"{valor:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(valor):
    return _n(valor * 100, 2) + " %"


def _falta(numero):
    return {"hecha": False, "falta": PASOS[numero][1]}


def _pauta_1(df, objetivo):
    caracteristicas = [c for c in df.columns if c != objetivo]
    nulos = {c: int(v) for c, v in df.isnull().sum().items()}
    total_nulos = sum(nulos.values())
    clases = df[objetivo].value_counts().sort_index()
    detalle_clases = " · ".join(f"{k} {v}" for k, v in clases.items())
    equilibrado = clases.max() - clases.min() <= 0.1 * clases.max()
    return {
        "hecha": True,
        "resultado": f"{len(caracteristicas)} características · {total_nulos} nulos",
        "caracteristicas": caracteristicas,
        "tabla": {
            "encabezados": ["Filas", "Características", "Variable objetivo", "Valores nulos"],
            "filas": [[str(len(df)), str(len(caracteristicas)), f"{objetivo} ({detalle_clases})", str(total_nulos)]],
        },
        "conclusion": (
            f"El dataset tiene {len(df)} registros y {len(caracteristicas)} características numéricas. "
            + ("No hay valores nulos en ninguna columna. " if total_nulos == 0 else f"Hay {total_nulos} valores nulos. ")
            + (f"Está equilibrado: {detalle_clases}." if equilibrado else f"Las clases no están equilibradas: {detalle_clases}.")
        ),
    }


def _pauta_2(df, objetivo, estado):
    procesado = estado.get("df_procesado")
    if procesado is None or AREA not in procesado.columns:
        return _falta(2)
    X = df.drop(columns=[objetivo])
    y = df[objetivo]
    antes_media, antes_std = float(df[AREA].mean()), float(df[AREA].std(ddof=0))
    despues_media, despues_std = float(procesado[AREA].mean()), float(procesado[AREA].std(ddof=0))
    return {
        "hecha": True,
        "resultado": f"X: {X.shape[0]}×{X.shape[1]} · y: {len(y)}",
        "tabla": {
            "encabezados": [AREA, "Antes (valores reales)", "Después de StandardScaler"],
            "filas": [
                ["Media", _n(antes_media), _n(abs(despues_media) if abs(despues_media) < 5e-4 else despues_media)],
                ["Desviación estándar", _n(antes_std), _n(despues_std)],
            ],
        },
        "conclusion": (
            f"Se separaron las {X.shape[1]} características (X) de la variable «{objetivo}» (y). Después de "
            f"StandardScaler cada característica queda con media 0 y desviación 1 (área pasó de media "
            f"{_n(antes_media, 2)} a {_n(despues_media if abs(despues_media) >= 5e-4 else 0, 2)}): así ninguna pesa "
            "más que otra al entrenar, algo importante para K-Vecinos, que compara distancias."
        ),
    }


def _pauta_3(estado):
    algebra = estado.get("algebra")
    if not algebra:
        return _falta(3)
    c = algebra.get("con_dataset")
    if not c:
        filas = [
            ["Producto punto v1 · v2", _n(algebra["producto_punto"])],
            ["Norma de v1", _n(algebra["normas"]["norma_v1"])],
            ["Solución del sistema", f'x = {_n(algebra["sistema_ecuaciones"]["solucion"]["x"])}, '
                                     f'y = {_n(algebra["sistema_ecuaciones"]["solucion"]["y"])}'],
        ]
        return {"hecha": True, "resultado": f'v1 · v2 = {_n(algebra["producto_punto"], 2)}',
                "tabla": {"encabezados": ["Operación", "Resultado"], "filas": filas},
                "conclusion": "Las operaciones con vectores y matrices y el sistema de ecuaciones se resolvieron con NumPy."}
    pesos = "; ".join(_n(w) for w in c["solucion"])
    exacta = np.allclose(c["verificacion"], c["vector_b"])
    return {
        "hecha": True,
        "resultado": f'v1 · v2 = {_n(c["producto_punto"], 2)}',
        "tabla": {
            "encabezados": [f'Operación (registros {c["filas"][0]} y {c["filas"][1]})', "Resultado"],
            "filas": [
                ["Producto punto v1 · v2 (np.dot)", _n(c["producto_punto"])],
                ["Norma de v1 (np.linalg.norm)", _n(c["norma_v1"])],
                ["Norma de v2", _n(c["norma_v2"])],
                ["Distancia entre v1 y v2", _n(c["distancia"])],
                ["Matriz A (3 registros × 3 medidas) y su transpuesta", "A × transpuesta de A, calculada"],
                [f'Sistema A · w = b, con b = {c["columna_b"]} (np.linalg.solve)', f"w = [{pesos}]"],
            ],
        },
        "conclusion": (
            f'Cada grano es un vector con sus medidas. Los dos primeros están a una distancia de '
            f'{_n(c["distancia"])}: es la cuenta que usa K-Vecinos para saber cuáles se parecen. '
            + ("Al multiplicar A por la solución se vuelve a obtener b, así que el sistema está bien resuelto."
               if exacta else "La verificación del sistema no coincide con b.")
        ),
    }


def _media_contra_mediana(c):
    media, mediana = c["media"], c["mediana"]
    if abs(media - mediana) <= 0.01 * abs(mediana):
        return f"La media de área ({_n(media, 2)}) y su mediana ({_n(mediana, 2)}) casi coinciden: la distribución es pareja. "
    if media > mediana:
        return (f"La media de área ({_n(media, 2)}) es mayor que su mediana ({_n(mediana, 2)}): hay algunos granos "
                "grandes que tiran el promedio para arriba. ")
    return (f"La media de área ({_n(media, 2)}) es menor que su mediana ({_n(mediana, 2)}): hay algunos granos "
            "chicos que tiran el promedio para abajo. ")


def _pauta_4(estado):
    estadistica = estado.get("estadistica")
    if not estadistica:
        return _falta(4)
    por_columna = {c["columna"]: c for c in estadistica.get("columnas", [])}
    if AREA not in por_columna or PERIMETRO not in por_columna:
        return _falta(4)
    a, p = por_columna[AREA], por_columna[PERIMETRO]
    filas = [
        [c["columna"], _n(c["media"]), _n(c["mediana"]), _n(c["varianza_numpy"]), _n(c["varianza_manual"]),
         _n(c["desviacion_numpy"]), _n(c["desviacion_manual"])]
        for c in (a, p)
    ]
    iguales = a["diferencia_varianza"] < 1e-9 and a["diferencia_desviacion"] < 1e-9
    mas_dispersa = AREA if a["desviacion_numpy"] / a["media"] > p["desviacion_numpy"] / p["media"] else PERIMETRO
    return {
        "hecha": True,
        "resultado": f'{AREA}: media {_n(a["media"], 2)}',
        "tabla": {
            "encabezados": ["Variable", "Media", "Mediana", "Varianza NumPy", "Varianza manual",
                            "Desviación NumPy", "Desviación manual"],
            "filas": filas,
        },
        "conclusion": (
            _media_contra_mediana(a)
            + ("La varianza y la desviación de área calculadas a mano dan exactamente lo mismo que NumPy. "
               if iguales else "La varianza manual y la de NumPy no coinciden. ")
            + f"Comparada con su propio promedio, {mas_dispersa} es la que más varía."
        ),
    }


def _pauta_5(df):
    resultado = stats.detectar_outliers(df[[AREA]], k=2.0)
    c = resultado["columnas"][0]
    valores = sorted(c["valores"])
    arriba = sum(v > c["limite_superior"] for v in valores)
    texto_valores = " · ".join(_n(v, 2) for v in valores) if valores else "ninguno"
    return {
        "resultado": f'{c["cantidad_outliers"]} atípicos',
        "tabla": {
            "encabezados": ["Media − 2σ", "Media + 2σ", "Cantidad", "Valores atípicos"],
            "filas": [[_n(c["limite_inferior"], 2), _n(c["limite_superior"], 2), str(c["cantidad_outliers"]), texto_valores]],
        },
        "conclusion": (
            f'Con el criterio de dos desviaciones estándar, {c["cantidad_outliers"]} de {len(df)} granos '
            f'({_n(c["cantidad_outliers"] / len(df) * 100, 1)} %) quedan fuera del rango '
            f'[{_n(c["limite_inferior"], 2)}; {_n(c["limite_superior"], 2)}]'
            + (", todos por encima: son granos muy grandes, no errores de medición." if valores and arriba == len(valores)
               else ".")
        ),
    }


def _pauta_6(df, objetivo, estado):
    graficos = (estado.get("graficos") or {}).get("graficos", [])
    histograma = next((g for g in graficos if g["titulo"].startswith("Histograma") and g["titulo"].endswith(AREA)), None)
    dispersion = next((g for g in graficos if g["titulo"] == f"Dispersión: {AREA} vs {PERIMETRO}"), None)
    if not histograma or not dispersion:
        return _falta(6)
    medias = df.groupby(objetivo)[AREA].mean().sort_values()
    correlacion = float(df[AREA].corr(df[PERIMETRO]))
    return {
        "hecha": True,
        "resultado": "2 gráficos",
        "graficos": [histograma["url"], dispersion["url"]],
        "conclusion": (
            f"Área y perímetro van casi juntos (correlación {_n(correlacion, 2)}). En la dispersión se ven "
            f"las {len(medias)} variedades: " + _orden_tamanos(list(medias.index))
        ),
    }


def _orden_tamanos(variedades):
    """Variedades ordenadas de la más chica a la más grande (por área media), dicho en palabras."""
    if len(variedades) == 2:
        return f"los granos de {variedades[1]} son más grandes que los de {variedades[0]}."
    if len(variedades) == 3:
        return (f"los granos de {variedades[2]} son los más grandes, los de {variedades[0]} los más chicos "
                f"y los de {variedades[1]} quedan en el medio.")
    return f"los granos más grandes son los de {variedades[-1]} y los más chicos, los de {variedades[0]}."


def _pauta_7(estado):
    comparacion = estado.get("comparacion_modelos") or {}
    knn, arbol = comparacion.get("KNN"), comparacion.get("Decision Tree")
    if not knn or not arbol or "accuracy" not in knn:
        return _falta(7)
    a_knn, a_arbol = knn["accuracy"], arbol["accuracy"]
    if abs(a_knn - a_arbol) < 1e-9:
        veredicto = "Los dos aciertan lo mismo"
    else:
        ganador = "K-Vecinos" if a_knn > a_arbol else "el Árbol de Decisión"
        veredicto = f"Gana {ganador} por {_n(abs(a_knn - a_arbol) * 100, 2)} puntos"
    return {
        "hecha": True,
        "resultado": f"K-Vecinos {_pct(a_knn)} · Árbol {_pct(a_arbol)}",
        "tabla": {
            "encabezados": ["Modelo", "Accuracy"],
            "filas": [["K-Vecinos (KNeighborsClassifier)", _pct(a_knn)],
                      ["Árbol de Decisión (DecisionTreeClassifier)", _pct(a_arbol)]],
        },
        "barras": [["K-Vecinos", a_knn], ["Árbol de Decisión", a_arbol]],
        "conclusion": (
            f"{veredicto}: aciertan alrededor de {_n(max(a_knn, a_arbol) * 10, 0)} de cada 10 granos del "
            "grupo de prueba, que no se usó para entrenar."
        ),
    }


def armar_pautas(df: pd.DataFrame, meta: dict, estado: dict) -> dict:
    """Las 7 pautas con su resultado. `df` es el dataset original (sin normalizar)."""
    objetivo = meta["objetivo"]
    hechos = set((estado.get("respuestas") or {}).keys())
    armadas = {
        1: _pauta_1(df, objetivo),
        2: _pauta_2(df, objetivo, estado),
        3: _pauta_3(estado),
        4: _pauta_4(estado),
        5: _pauta_5(df) if PASOS[5][0] in hechos else _falta(5),
        6: _pauta_6(df, objetivo, estado),
        7: _pauta_7(estado),
    }
    if PASOS[1][0] not in hechos:
        armadas[1] = _falta(1)
    pautas = []
    for numero in range(1, 8):
        pauta = {"numero": numero, "titulo": TITULOS[numero], "hecha": True}
        pauta.update(armadas[numero])
        pautas.append(pauta)
    cumplidas = sum(p["hecha"] for p in pautas)

    conclusion = None
    if cumplidas == 7:
        p7 = armadas[7]
        variedades = df[objetivo].nunique()
        nulos = int(df.isnull().sum().sum())
        conclusion = (
            ("El dataset está completo" if nulos == 0 else f"El dataset tiene {nulos} valores nulos")
            + f"; área y perímetro ayudan a separar las {variedades} variedades, y los dos modelos las "
            f"clasifican con buen acierto ({p7['resultado']})."
        )
    return {"cumplidas": cumplidas, "total": 7, "pautas": pautas, "conclusion_general": conclusion}
