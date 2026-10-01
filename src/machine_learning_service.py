"""Entrenamiento y evaluación de modelos de Machine Learning con Scikit-learn.

Detecta automáticamente si el problema es de clasificación o regresión según la variable
objetivo, entrena varios modelos apropiados y los compara con métricas reales (nada de
valores fijos o inventados).

Cada modelo es un Pipeline: rellenar nulos, codificar categorías y escalar se ajustan SOLO
con la parte de entrenamiento (y dentro de cada partición de la validación cruzada), así la
parte de prueba nunca influye en lo que el modelo aprende. El mejor modelo se elige por su
puntuación de validación cruzada, no por el resultado en la prueba, que queda como una
medida honesta de cómo le iría con datos nuevos.
"""

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import (
    train_test_split, ParameterGrid, StratifiedKFold, KFold, cross_val_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_absolute_error, mean_squared_error, r2_score,
)

RANDOM_STATE = 42

# Grilla pequeña de hiperparámetros por modelo: se prueban todas las combinaciones con
# validación cruzada SOLO sobre el conjunto de entrenamiento, y se queda con la que mejor
# generaliza — en vez de usar un valor fijo elegido a mano, que podía quedar mal para un
# dataset y bien para otro. Linear Regression no tiene hiperparámetros relevantes para
# ajustar (es la solución analítica exacta), por eso no aparece aquí.
GRILLAS = {
    "KNN": {"n_neighbors": [3, 5, 7, 9, 11], "weights": ["uniform", "distance"]},
    "Decision Tree": {"max_depth": [3, 5, 7, 9, None], "min_samples_leaf": [1, 2, 4]},
    "Random Forest": {"n_estimators": [100, 200], "max_depth": [None, 10, 20], "min_samples_leaf": [1, 2]},
    # Regresión logística (solo clasificación): la fuerza de regularización C y si se compensa el desbalance de clases.
    "Logistic Regression": {"C": [0.01, 0.1, 1, 10, 100], "class_weight": [None, "balanced"]},
}


def detectar_tipo_problema(y: pd.Series) -> str:
    """Clasificación si el objetivo es texto o tiene pocos valores distintos (enteros, aunque
    pandas los haya leído como decimales por tener huecos); si no, regresión."""
    y = y.dropna()
    if not pd.api.types.is_numeric_dtype(y) or pd.api.types.is_bool_dtype(y):
        return "clasificacion"
    son_enteros = pd.api.types.is_integer_dtype(y) or (len(y) > 0 and bool(np.all(np.mod(y, 1) == 0)))
    if son_enteros and y.nunique() <= 15:
        return "clasificacion"
    return "regresion"


def modelos_para(problema: str) -> dict:
    if problema == "clasificacion":
        return {
            "KNN": KNeighborsClassifier(n_neighbors=5),
            "Decision Tree": DecisionTreeClassifier(random_state=RANDOM_STATE, max_depth=6),
            "Random Forest": RandomForestClassifier(random_state=RANDOM_STATE, n_estimators=200),
            # Se agregó porque, con validación cruzada anidada sobre los mismos CSV, aprendió mejor que los otros tres:
            # Clientes 94,3 -> 98,7 %, Iris 94,6 -> 98,0 %, Sintético 88,9 -> 91,3 %, Préstamos 71,3 -> 74,8 %, y en
            # Diabetes detecta el 70 % de los casos positivos en vez del 26 %.
            "Logistic Regression": LogisticRegression(max_iter=2000),
        }
    return {
        "Linear Regression": LinearRegression(),
        "Decision Tree": DecisionTreeRegressor(random_state=RANDOM_STATE, max_depth=6),
        "Random Forest": RandomForestRegressor(random_state=RANDOM_STATE, n_estimators=200),
    }


def construir_pipeline(modelo, numericas: list, categoricas: list) -> Pipeline:
    """Preparación de los datos + modelo en un solo objeto: al entrenarlo, la media para
    rellenar, las categorías y la escala se aprenden solo de los datos que recibe."""
    partes = []
    if numericas:
        partes.append(("num", Pipeline([
            ("rellenar", SimpleImputer(strategy="mean")), ("escalar", StandardScaler()),
        ]), numericas))
    if categoricas:
        partes.append(("cat", Pipeline([
            ("rellenar", SimpleImputer(strategy="most_frequent")),
            ("codificar", OneHotEncoder(handle_unknown="ignore", drop="if_binary", sparse_output=False)),
            ("escalar", StandardScaler()),
        ]), categoricas))
    preparar = ColumnTransformer(partes, verbose_feature_names_out=False)
    return Pipeline([("preparar", preparar), ("modelo", modelo)])


def nombres_variables(pipeline: Pipeline) -> list:
    return [str(n) for n in pipeline.named_steps["preparar"].get_feature_names_out()]


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


def _particiones(problema: str, y_train) -> int:
    """En clasificación 10 particiones (con datasets chicos y clases desbalanceadas, como
    Diabetes, 5 daban una estimación ruidosa que llegó a elegir un modelo peor); en regresión
    5 ya daban un resultado estable e idéntico a 10. Con archivos subidos muy chicos se baja
    para que cada partición tenga al menos un caso de cada clase."""
    if problema == "clasificacion":
        return int(max(2, min(10, pd.Series(y_train).value_counts().min())))
    return int(max(2, min(5, len(y_train) // 2)))


def _grilla_valida(nombre: str, filas_por_particion: int) -> dict:
    """KNN no puede pedir más vecinos que filas tiene cada partición de entrenamiento."""
    grilla = dict(GRILLAS.get(nombre) or {})
    if "n_neighbors" in grilla:
        grilla["n_neighbors"] = [k for k in grilla["n_neighbors"] if k <= filas_por_particion] or [1]
    return grilla


def _validar_clases(y: pd.Series, objetivo: str, mapeo_objetivo: dict = None):
    conteo = y.value_counts()
    if len(conteo) < 2:
        raise ValueError(f'La variable objetivo "{objetivo}" tiene un solo valor: no hay nada que predecir.')
    raras = conteo[conteo < 2]
    if len(raras):
        etiquetas = ", ".join(f'"{mapeo_objetivo.get(int(c), c) if mapeo_objetivo else c}"' for c in raras.index)
        raise ValueError(
            f'En "{objetivo}", la categoría {etiquetas} aparece en una sola fila. Hacen falta al menos 2 filas de '
            "cada categoría para separar datos de entrenamiento y de prueba. Agrega más casos de esa categoría "
            "o quita esa fila del archivo."
        )


def entrenar(datos: dict, objetivo: str, on_progreso=None) -> dict:
    """Entrena los modelos apropiados según el tipo de problema detectado, ajustando los
    hiperparámetros de cada uno por validación cruzada y eligiendo el mejor por esa misma
    puntuación. `datos` es lo que devuelve preprocessing_service.preparar_para_modelo().

    `on_progreso(hecho, total)`, si se pasa, se llama después de cada ajuste (fit) con la
    cantidad de pasos completados y el total, para que la interfaz muestre un porcentaje exacto.

    Se evita `n_jobs=-1` a propósito: en Windows, si el servidor se corta a mitad de una
    búsqueda, esos procesos hijos pueden quedar huérfanos en segundo plano. Con los datasets
    de este proyecto la búsqueda ya es rápida en un solo proceso."""
    df = datos["df"]
    numericas, categoricas = datos["numericas"], datos["categoricas"]
    if not numericas and not categoricas:
        raise ValueError("No queda ninguna columna para predecir: elige al menos una además del objetivo.")

    y = df[objetivo]
    X = df[numericas + categoricas]
    problema = detectar_tipo_problema(y)
    if len(df) < 10:
        raise ValueError(f"Hay solo {len(df)} filas útiles: hacen falta al menos 10 para entrenar y probar un modelo.")
    if problema == "clasificacion":
        _validar_clases(y, objetivo, datos.get("mapeo_objetivo"))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE,
        stratify=y if problema == "clasificacion" else None,
    )

    particiones = _particiones(problema, y_train)
    cv = StratifiedKFold(n_splits=particiones) if problema == "clasificacion" else KFold(n_splits=particiones)
    metrica_cv = "f1_macro" if problema == "clasificacion" else "r2"
    filas_por_particion = len(X_train) - int(np.ceil(len(X_train) / particiones))

    candidatos = modelos_para(problema)
    grillas = {nombre: _grilla_valida(nombre, filas_por_particion) for nombre in candidatos}
    total_pasos = sum((len(ParameterGrid(g)) if g else 1) * particiones + 1 for g in grillas.values())
    pasos_hechos = 0

    def _avanzar(cantidad):
        nonlocal pasos_hechos
        pasos_hechos += cantidad
        if on_progreso:
            on_progreso(pasos_hechos, total_pasos)

    _avanzar(0)
    comparacion, parametros_por_modelo, modelos_entrenados, y_pred_por_modelo = {}, {}, {}, {}
    mejor_nombre, mejor_cv = None, -np.inf

    for nombre, modelo in candidatos.items():
        base = construir_pipeline(modelo, numericas, categoricas)
        grilla = grillas[nombre]
        # Si todas las combinaciones fallaran en la validación, se entrena con la configuración por defecto.
        mejor_score, mejores_parametros = -np.inf, {}
        for parametros in (ParameterGrid(grilla) if grilla else [{}]):
            estimador = clone(base).set_params(**{f"modelo__{k}": v for k, v in parametros.items()})
            puntajes = cross_val_score(estimador, X_train, y_train, cv=cv, scoring=metrica_cv, n_jobs=1, error_score=np.nan)
            score = -np.inf if np.all(np.isnan(puntajes)) else float(np.nanmean(puntajes))
            _avanzar(particiones)
            if score > mejor_score:
                mejor_score, mejores_parametros = score, parametros

        final = clone(base).set_params(**{f"modelo__{k}": v for k, v in mejores_parametros.items()})
        final.fit(X_train, y_train)
        _avanzar(1)

        y_pred = final.predict(X_test)
        metricas = _metricas_clasificacion(y_test, y_pred) if problema == "clasificacion" else _metricas_regresion(y_test, y_pred)
        metricas["cv"] = None if mejor_score == -np.inf else mejor_score
        comparacion[nombre] = metricas
        parametros_por_modelo[nombre] = dict(mejores_parametros)
        modelos_entrenados[nombre] = final
        y_pred_por_modelo[nombre] = y_pred

        if mejor_nombre is None or mejor_score > mejor_cv:
            mejor_nombre, mejor_cv = nombre, mejor_score

    mejor = modelos_entrenados[mejor_nombre]
    return {
        "problema": problema,
        "columnas_features": nombres_variables(mejor),
        "X_train": X_train, "X_test": X_test, "y_train": y_train, "y_test": y_test,
        "modelos_entrenados": modelos_entrenados,
        "comparacion": comparacion,
        "parametros": parametros_por_modelo,
        "particiones": particiones,
        "mejor_modelo_nombre": mejor_nombre,
        "mejor_modelo": mejor,
        "y_pred": y_pred_por_modelo[mejor_nombre],
        "y_pred_por_modelo": y_pred_por_modelo,
    }


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
