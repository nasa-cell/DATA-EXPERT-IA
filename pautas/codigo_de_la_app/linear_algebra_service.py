"""Operaciones fundamentales de álgebra lineal aplicadas a IA, con NumPy.

Primero con vectores y matrices fijos, para ver cada operación de forma clara y verificable, y
después las mismas operaciones con registros reales del dataset elegido (ver _con_dataset).
"""

import numpy as np
import pandas as pd


def _con_dataset(df: pd.DataFrame, objetivo: str = None):
    """Las mismas operaciones con datos reales: cada fila del dataset es un vector.

    - Producto punto, norma y distancia entre los dos primeros registros (la distancia es lo que
      usa K-Vecinos para decidir qué registros se parecen).
    - Una matriz con 3 registros × 3 variables, su transpuesta y su producto.
    - Un sistema de ecuaciones: qué pesos w combinan las 3 primeras variables para dar la cuarta
      en 3 registros reales (A · w = b), resuelto con np.linalg.solve.
    """
    numericas = [c for c in df.select_dtypes(include=[np.number]).columns if c != objetivo]
    datos = df[numericas].dropna()
    if len(numericas) < 4 or len(datos) < 3:
        return None
    columnas = numericas[:3]
    columna_b = numericas[3]

    v1 = datos[columnas].iloc[0].to_numpy(dtype=float)
    v2 = datos[columnas].iloc[1].to_numpy(dtype=float)
    producto = float(np.dot(v1, v2))
    norma_v1 = float(np.linalg.norm(v1))
    norma_v2 = float(np.linalg.norm(v2))

    # Tres registros seguidos con los que el sistema tenga una única solución (determinante ≠ 0).
    for inicio in range(0, min(len(datos) - 2, 60)):
        A = datos[columnas].iloc[inicio:inicio + 3].to_numpy(dtype=float)
        if abs(np.linalg.det(A)) > 1e-6:
            break
    else:
        return None
    b = datos[columna_b].iloc[inicio:inicio + 3].to_numpy(dtype=float)
    w = np.linalg.solve(A, b)

    return {
        "columnas": columnas,
        "columna_b": columna_b,
        "filas": [int(i) + 1 for i in datos.index[:2]],
        "v1": v1.tolist(),
        "v2": v2.tolist(),
        "producto_punto": producto,
        "norma_v1": norma_v1,
        "norma_v2": norma_v2,
        "distancia": float(np.linalg.norm(v1 - v2)),
        "coseno": producto / (norma_v1 * norma_v2) if norma_v1 and norma_v2 else 0.0,
        "matriz": A.tolist(),
        "filas_matriz": [int(i) + 1 for i in datos.index[inicio:inicio + 3]],
        "transpuesta": A.T.tolist(),
        "producto_matriz": (A @ A.T).tolist(),
        "vector_b": b.tolist(),
        "solucion": w.tolist(),
        "verificacion": (A @ w).tolist(),
    }


def ejecutar_algebra_lineal(df: pd.DataFrame = None, objetivo: str = None) -> dict:
    # --- Vectores ---
    v1 = np.array([4.0, -2.0, 7.0])
    v2 = np.array([1.0, 5.0, 3.0])

    suma_vectores = (v1 + v2).tolist()
    resta_vectores = (v1 - v2).tolist()
    escalar = 3.0
    multiplicacion_escalar = (v1 * escalar).tolist()

    producto_punto = float(np.dot(v1, v2))
    norma_v1 = float(np.linalg.norm(v1))
    norma_v2 = float(np.linalg.norm(v2))

    # --- Matrices ---
    A = np.array([[2.0, 1.0], [0.0, 3.0]])
    B = np.array([[1.0, 4.0], [2.0, 1.0]])

    suma_matrices = (A + B).tolist()
    resta_matrices = (A - B).tolist()
    multiplicacion_matrices = (A @ B).tolist()
    transpuesta_A = A.T.tolist()

    # --- Sistema de ecuaciones lineales ---
    # 2x +  y = 5
    #  x + 3y = 6
    A_sistema = np.array([[2.0, 1.0], [1.0, 3.0]])
    b_sistema = np.array([5.0, 6.0])
    solucion = np.linalg.solve(A_sistema, b_sistema)
    verificacion = (A_sistema @ solucion).tolist()

    return {
        "vectores": {
            "v1": v1.tolist(),
            "v2": v2.tolist(),
            "suma": suma_vectores,
            "resta": resta_vectores,
            "escalar": escalar,
            "multiplicacion_escalar": multiplicacion_escalar,
        },
        "producto_punto": producto_punto,
        "normas": {"norma_v1": norma_v1, "norma_v2": norma_v2},
        "matrices": {
            "A": A.tolist(),
            "B": B.tolist(),
            "suma": suma_matrices,
            "resta": resta_matrices,
            "multiplicacion": multiplicacion_matrices,
            "transpuesta_A": transpuesta_A,
        },
        "sistema_ecuaciones": {
            "descripcion": ["2x + y = 5", "x + 3y = 6"],
            "matriz_A": A_sistema.tolist(),
            "vector_b": b_sistema.tolist(),
            "solucion": {"x": float(solucion[0]), "y": float(solucion[1])},
            "verificacion": verificacion,
        },
        "con_dataset": _con_dataset(df, objetivo) if df is not None else None,
    }
