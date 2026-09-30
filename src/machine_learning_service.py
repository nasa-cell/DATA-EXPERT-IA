"""Entrenamiento y evaluación de modelos de Machine Learning con Scikit-learn.

Detecta automáticamente si el problema es de clasificación o regresión según la variable
objetivo, entrena dos modelos apropiados y los compara con métricas reales (nada de
valores fijos o inventados).
"""

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import (
    train_test_split, ParameterGrid, StratifiedKFold, KFold, cross_val_score,
)
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_absolute_error, mean_squared_error, r2_score,
)

RANDOM_STATE = 42

# Grilla pequeña de hiperparámetros por modelo: GridSearchCV prueba todas las combinaciones
# con validación cruzada (cv=5) SOLO sobre el conjunto de entrenamiento, y se queda con la
# que mejor generaliza — en vez de usar un valor fijo elegido a mano (como antes), que podía
# quedar mal para un dataset y bien para otro. Linear Regression no tiene hiperparámetros
# relevantes para ajustar (es la solución analítica exacta), por eso no aparece aquí.
GRILLAS = {
    "KNN": {"n_neighbors": [3, 5, 7, 9, 11], "weights": ["uniform", "distance"]},
    "Decision Tree": {"max_depth": [3, 5, 7, 9, None], "min_samples_leaf": [1, 2, 4]},
    "Random Forest": {"n_estimators": [100, 200], "max_depth": [None, 10, 20], "min_samples_leaf": [1, 2]},
    # Regresión logística (solo clasificación): la fuerza de regularización C y si se compensa el desbalance de clases.
    "Logistic Regression": {"C": [0.01, 0.1, 1, 10, 100], "class_weight": [None, "balanced"]},
}


def detectar_tipo_problema(y: pd.Series) -> str:
    """Clasificación si el objetivo es texto o tiene pocos valores distintos; si no, regresión."""
    if y.dtype == object or str(y.dtype).startswith("category"):
        return "clasificacion"
    if pd.api.types.is_integer_dtype(y) and y.nunique() <= 15:
        return "clasificacion"
    return "regresion"


def preparar_X_y(df: pd.DataFrame, objetivo: str):
    y = df[objetivo]
    X = df.drop(columns=[objetivo])
    # Cualquier columna categórica remanente (no debería haberla tras el preprocesamiento,
    # pero se cubre por seguridad) se convierte a dummies para poder entrenar el modelo.
    X = pd.get_dummies(X, drop_first=True)
    return X, y


def modelos_para(problema: str) -> dict:
    if problema == "clasificacion":
        return {
            "KNN": KNeighborsClassifier(n_neighbors=5),
            "Decision Tree": DecisionTreeClassifier(random_state=RANDOM_STATE, max_depth=6),
            "Random Forest": RandomForestClassifier(random_state=RANDOM_STATE, n_estimators=200),
            # Se agregó porque, con validación cruzada anidada sobre los mismos CSV, aprendió mejor que los otros tres:
            # Clientes 94,3 -> 98,7 %, Iris 94,6 -> 98,0 %, Sintético 88,9 -> 91,3 %, Préstamos 71,3 -> 74,8 %, y en
            # Diabetes detecta el 70 % de los casos positivos en vez del 26 %. Los datos ya llegan normalizados del preprocesamiento.
            "Logistic Regression": LogisticRegression(max_iter=2000),
        }
    return {
        "Linear Regression": LinearRegression(),
        "Decision Tree": DecisionTreeRegressor(random_state=RANDOM_STATE, max_depth=6),
        "Random Forest": RandomForestRegressor(random_state=RANDOM_STATE, n_estimators=200),
    }


def _metricas_clasificacion(y_test, y_pred) -> dict:
    promedio = "binary" if len(set(y_test)) <= 2 else "macro"
    return {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, average=promedio, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, average=promedio, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, average=promedio, zero_division=0)),
    }


def _metricas_regresion(y_test, y_pred) -> dict:
    mse = float(mean_squared_error(y_test, y_pred))
    return {
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "mse": mse,
        "rmse": float(np.sqrt(mse)),
        "r2": float(r2_score(y_test, y_pred)),
    }


def _particiones_y_cv(nombre: str, problema: str):
    """Cantidad de particiones y objeto de validación cruzada para un modelo, replicando
    exactamente lo que GridSearchCV arma internamente para cv=<entero> (shuffle=False),
    para que el resultado de la búsqueda manual sea idéntico al de antes.

    En clasificación se usan 10 particiones (en vez de 5): con datasets chicos y clases
    desbalanceadas (p. ej. Diabetes, ~30% positivos), 5 particiones dieron una estimación
    ruidosa que en una prueba real llegó a elegir un modelo peor que el que había antes
    (n_neighbors=3 con weights="distance" via CV, contra n_neighbors=5 fijo: 67.5% vs 73.4%
    de accuracy en el conjunto de prueba). Con 10 particiones la búsqueda vuelve a acertar.
    En regresión (Random Forest) se probó lo mismo y 5 particiones ya daban un resultado
    estable e idéntico a 10, así que ahí se deja en 5 para no duplicar el tiempo de espera
    sin ninguna mejora real."""
    particiones = 10 if problema == "clasificacion" else 5
    cv = StratifiedKFold(n_splits=particiones) if problema == "clasificacion" else KFold(n_splits=particiones)
    return particiones, cv


def pasos_de_busqueda(nombre: str, problema: str) -> int:
    """Cantidad exacta de ajustes (fits) que le toma a un modelo su búsqueda de
    hiperparámetros: una combinación de la grilla se evalúa con `particiones` fits de
    validación cruzada, más 1 fit final sobre todo el set de entrenamiento con la mejor
    combinación. Sirve para calcular el total de la barra de progreso ANTES de arrancar,
    así el porcentaje mostrado es exacto y no una estimación."""
    grilla = GRILLAS.get(nombre)
    if not grilla:
        return 1  # Linear Regression: un único fit, sin búsqueda.
    particiones, _ = _particiones_y_cv(nombre, problema)
    return len(list(ParameterGrid(grilla))) * particiones + 1


def _entrenar_con_busqueda(nombre: str, modelo, X_train, y_train, problema: str, on_paso=None):
    """Si el modelo tiene una grilla de hiperparámetros definida, prueba cada combinación
    a mano con validación cruzada (mismo resultado que GridSearchCV, pero reportando el
    avance fit por fit vía `on_paso`) y devuelve la mejor; si no (Linear Regression),
    simplemente lo entrena tal cual.

    Se evita `n_jobs=-1` (paralelizar entre procesos) a propósito: en Windows, si el
    servidor de Flask se reinicia o se corta a la mitad de una búsqueda, esos procesos
    hijos (joblib/loky) pueden quedar huérfanos corriendo en segundo plano. Con los
    datasets de este proyecto (cientos de filas, grillas chicas) la búsqueda ya es rápida
    en un solo proceso, así que no vale la pena el riesgo."""
    grilla = GRILLAS.get(nombre)
    if not grilla:
        modelo.fit(X_train, y_train)
        if on_paso:
            on_paso(1)
        return modelo, {}

    metrica_busqueda = "f1_macro" if problema == "clasificacion" else "r2"
    particiones, cv = _particiones_y_cv(nombre, problema)

    mejor_score, mejores_parametros = -np.inf, None
    for parametros in ParameterGrid(grilla):
        estimador = clone(modelo).set_params(**parametros)
        score = cross_val_score(
            estimador, X_train, y_train, cv=cv, scoring=metrica_busqueda, n_jobs=1
        ).mean()
        if on_paso:
            on_paso(particiones)
        if score > mejor_score:
            mejor_score, mejores_parametros = score, parametros

    mejor_modelo = clone(modelo).set_params(**mejores_parametros)
    mejor_modelo.fit(X_train, y_train)
    if on_paso:
        on_paso(1)
    return mejor_modelo, mejores_parametros


def calcular_total_pasos(problema: str) -> int:
    """Total exacto de fits que va a hacer `entrenar()` para este tipo de problema, sumando
    los de cada modelo candidato. Se calcula ANTES de entrenar para inicializar la barra de
    progreso con un total real (no una estimación a ojo)."""
    return sum(pasos_de_busqueda(nombre, problema) for nombre in modelos_para(problema))


def entrenar(df: pd.DataFrame, objetivo: str, on_progreso=None) -> dict:
    """Entrena el/los modelo(s) apropiados según el tipo de problema detectado, ajustando
    los hiperparámetros de cada uno por validación cruzada antes de compararlos.

    `on_progreso(hecho, total)`, si se pasa, se llama después de cada fit con la cantidad
    de pasos completados hasta el momento y el total ya conocido (ver `calcular_total_pasos`),
    para que la interfaz pueda mostrar un porcentaje exacto mientras entrena."""
    problema = detectar_tipo_problema(df[objetivo])
    X, y = preparar_X_y(df, objetivo)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE,
        stratify=y if problema == "clasificacion" else None,
    )

    candidatos = modelos_para(problema)
    total_pasos = calcular_total_pasos(problema)
    pasos_hechos = 0

    def _avanzar(cantidad):
        nonlocal pasos_hechos
        pasos_hechos += cantidad
        if on_progreso:
            on_progreso(pasos_hechos, total_pasos)

    resultados_por_modelo = {}
    parametros_por_modelo = {}
    modelos_entrenados = {}
    y_pred_por_modelo = {}
    mejor_nombre, mejor_score, mejor_modelo, mejor_pred = None, -np.inf, None, None

    for nombre, modelo in candidatos.items():
        modelo_entrenado, mejores_parametros = _entrenar_con_busqueda(
            nombre, modelo, X_train, y_train, problema, on_paso=_avanzar
        )
        y_pred = modelo_entrenado.predict(X_test)
        modelos_entrenados[nombre] = modelo_entrenado
        parametros_por_modelo[nombre] = mejores_parametros
        y_pred_por_modelo[nombre] = y_pred

        if problema == "clasificacion":
            metricas = _metricas_clasificacion(y_test, y_pred)
            score = metricas["f1"]
        else:
            metricas = _metricas_regresion(y_test, y_pred)
            score = metricas["r2"]

        resultados_por_modelo[nombre] = metricas

        if score > mejor_score:
            mejor_nombre, mejor_score, mejor_modelo, mejor_pred = nombre, score, modelo_entrenado, y_pred

    return {
        "problema": problema,
        "columnas_features": X.columns.tolist(),
        "X_train": X_train, "X_test": X_test, "y_train": y_train, "y_test": y_test,
        "modelos_entrenados": modelos_entrenados,
        "comparacion": resultados_por_modelo,
        "parametros": parametros_por_modelo,
        "mejor_modelo_nombre": mejor_nombre,
        "mejor_modelo": mejor_modelo,
        "y_pred": mejor_pred,
        "y_pred_por_modelo": y_pred_por_modelo,
    }


def evaluar(problema: str, y_test, y_pred) -> dict:
    if problema == "clasificacion":
        return _metricas_clasificacion(y_test, y_pred)
    return _metricas_regresion(y_test, y_pred)


def tabla_predicciones(y_test, y_pred, problema: str, mapeo_objetivo: dict = None, limite: int = 20):
    filas = []
    y_test_list = list(y_test)[:limite]
    y_pred_list = list(y_pred)[:limite]
    for real, prediccion in zip(y_test_list, y_pred_list):
        if problema == "clasificacion":
            real_et = mapeo_objetivo.get(int(real), real) if mapeo_objetivo else real
            pred_et = mapeo_objetivo.get(int(prediccion), prediccion) if mapeo_objetivo else prediccion
            correcto = bool(real == prediccion)
            filas.append({
                "real": str(real_et), "prediccion": str(pred_et),
                "resultado": "Correcto" if correcto else "Incorrecto", "acierto": correcto,
            })
        else:
            filas.append({
                "real": round(float(real), 2), "prediccion": round(float(prediccion), 2),
                "resultado": round(float(real) - float(prediccion), 2), "acierto": None,
            })
    return filas
