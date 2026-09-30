"""Estadística descriptiva: medidas de tendencia central, dispersión y valores atípicos.

Incluye implementaciones manuales de varianza y desviación estándar (sin usar NumPy en el
cálculo en sí) para compararlas con el resultado de NumPy, tal como pide el caso práctico.
"""

import math
import numpy as np
import pandas as pd


def varianza_manual(datos) -> float:
    """Varianza poblacional calculada a mano: promedio de (x - media)^2, sin usar np.var()."""
    valores = [float(x) for x in datos if not (isinstance(x, float) and math.isnan(x))]
    n = len(valores)
    if n == 0:
        return float("nan")
    media = sum(valores) / n
    return sum((x - media) ** 2 for x in valores) / n


def desviacion_estandar_manual(datos) -> float:
    """Desviación estándar manual: raíz cuadrada de la varianza manual."""
    return math.sqrt(varianza_manual(datos))


def columnas_numericas(df: pd.DataFrame):
    return df.select_dtypes(include=[np.number]).columns.tolist()


def columnas_categoricas(df: pd.DataFrame):
    return df.select_dtypes(exclude=[np.number]).columns.tolist()


def calcular_estadisticas(df: pd.DataFrame) -> dict:
    """Media, mediana, moda, mínimo, máximo, rango, varianza y desviación estándar por
    columna numérica, calculadas tanto con NumPy como manualmente para comparar."""
    filas = []
    for columna in columnas_numericas(df):
        serie = df[columna].dropna()
        if serie.empty:
            continue

        valores = serie.to_numpy(dtype=float)
        var_np = float(np.var(valores))
        std_np = float(np.std(valores))
        var_manual = varianza_manual(valores)
        std_manual = desviacion_estandar_manual(valores)

        moda_serie = serie.mode()
        moda = float(moda_serie.iloc[0]) if not moda_serie.empty else None

        filas.append({
            "columna": columna,
            "media": float(np.mean(valores)),
            "mediana": float(np.median(valores)),
            "moda": moda,
            "minimo": float(np.min(valores)),
            "maximo": float(np.max(valores)),
            "rango": float(np.max(valores) - np.min(valores)),
            "varianza_numpy": var_np,
            "desviacion_numpy": std_np,
            "varianza_manual": var_manual,
            "desviacion_manual": std_manual,
            "diferencia_varianza": abs(var_np - var_manual),
            "diferencia_desviacion": abs(std_np - std_manual),
        })

    return {"columnas": filas}


def detectar_outliers(df: pd.DataFrame, k: float = 2.0) -> dict:
    """Valores atípicos por columna numérica: fuera de media ± k * desviación estándar."""
    resultado = []
    for columna in columnas_numericas(df):
        serie = df[columna].dropna()
        if serie.empty:
            continue

        media = float(serie.mean())
        std = float(serie.std(ddof=0))
        limite_inferior = media - k * std
        limite_superior = media + k * std

        atipicos = serie[(serie < limite_inferior) | (serie > limite_superior)]

        resultado.append({
            "columna": columna,
            "media": media,
            "desviacion_estandar": std,
            "limite_inferior": limite_inferior,
            "limite_superior": limite_superior,
            "cantidad_outliers": int(atipicos.shape[0]),
            "valores": [float(v) for v in atipicos.head(15).tolist()],
        })

    return {"k": k, "columnas": resultado}
