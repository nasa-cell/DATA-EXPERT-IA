"""Operaciones fundamentales de álgebra lineal aplicadas a IA, con NumPy.

Esta sección es educativa e independiente del dataset seleccionado: usa vectores y
matrices fijos (pero variados) para demostrar cada operación de forma clara y verificable.
"""

import numpy as np


def ejecutar_algebra_lineal() -> dict:
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
    }
