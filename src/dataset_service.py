"""Carga y metadatos de los 6 datasets incluidos en el proyecto.

Mantiene en memoria el DataFrame original de cada dataset ya leído (caché simple por
nombre) para no releer el CSV en cada análisis, y guarda el estado del análisis en curso
(dataset seleccionado, versión preprocesada, modelo entrenado, predicciones) en un
diccionario global: el proyecto es de un solo usuario local, así que no hace falta una
base de datos ni sesiones por usuario para esto.
"""

import os
import numpy as np
import pandas as pd

from src import configuracion as cfg

DATA_DIR = str(cfg.CODIGO / "data")

# Metadatos de cada dataset: descripción, columna objetivo y tipo de problema esperado.
# El tipo de problema también se detecta automáticamente en machine_learning_service.py;
# aquí se documenta para mostrarlo en la interfaz.
DATASETS = {
    "iris": {
        "archivo": "iris.csv",
        "nombre": "Iris",
        "icono": "🌸",
        "imagen": "img/datasets/iris.jpg",
        "descripcion": "Clasificación de especies de flores según medidas de sépalos y pétalos.",
        "objetivo": "species",
        "problema": "clasificacion",
        "color_a": "#c084fc", "color_b": "#ec4899",  # violeta -> rosa (floral)
    },
    "diabetes": {
        "archivo": "diabetes.csv",
        "nombre": "Diabetes",
        "icono": "❤️",
        "imagen": "img/datasets/diabetes.jpg",
        "descripcion": "Diagnóstico de diabetes a partir de indicadores clínicos.",
        "objetivo": "Outcome",
        "problema": "clasificacion",
        "color_a": "#fb7185", "color_b": "#e11d48",  # rosa -> rojo (clínico)
    },
    "viviendas": {
        "archivo": "viviendas.csv",
        "nombre": "Viviendas",
        "icono": "🏠",
        "imagen": "img/datasets/viviendas.jpg",
        "descripcion": "Predicción del precio de una vivienda según sus características.",
        "objetivo": "price",
        "problema": "regresion",
        "color_a": "#38bdf8", "color_b": "#0ea5e9",  # celeste (cielo/hogar)
    },
    "vehiculos": {
        "archivo": "vehiculos.csv",
        "nombre": "Vehículos",
        "icono": "🚗",
        "imagen": "img/datasets/vehiculos.jpg",
        "descripcion": "Predicción del precio de un vehículo según sus especificaciones técnicas.",
        "objetivo": "price",
        "problema": "regresion",
        "color_a": "#fb923c", "color_b": "#ea580c",  # naranja (energía/velocidad)
    },
    "clientes": {
        "archivo": "clientes.csv",
        "nombre": "Clientes",
        "icono": "🛒",
        "imagen": "img/datasets/clientes.jpg",
        "descripcion": "Segmentación de clientes según su comportamiento de compra.",
        "objetivo": "segment",
        "problema": "clasificacion",
        "color_a": "#34d399", "color_b": "#0d9488",  # esmeralda -> teal (comercio)
    },
    "sintetico": {
        "archivo": "sintetico.csv",
        "nombre": "Sintético",
        "icono": "🧪",
        "imagen": "img/datasets/sintetico.jpg",
        "descripcion": "Dataset generado con NumPy y Pandas para demostrar el preprocesamiento.",
        "objetivo": "objetivo",
        "problema": "clasificacion",
        "color_a": "#818cf8", "color_b": "#6366f1",  # índigo (tecnología/datos)
    },
    "empleados": {
        "archivo": "empleados.csv",
        "nombre": "Empleados",
        "icono": "💼",
        "imagen": "img/datasets/empleados.jpg",
        "descripcion": "Predicción de renuncia (attrition) de un empleado según su situación laboral.",
        "objetivo": "attrition",
        "problema": "clasificacion",
        "color_a": "#64748b", "color_b": "#334155",  # gris azulado (corporativo/RRHH)
    },
    "estudiantes": {
        "archivo": "estudiantes.csv",
        "nombre": "Estudiantes",
        "icono": "🎓",
        "imagen": "img/datasets/estudiantes.jpg",
        "descripcion": "Predicción de la nota final de un estudiante según sus hábitos de estudio.",
        "objetivo": "final_score",
        "problema": "regresion",
        "color_a": "#fbbf24", "color_b": "#d97706",  # ámbar (académico)
    },
    "prestamos": {
        "archivo": "prestamos.csv",
        "nombre": "Préstamos",
        "icono": "🏦",
        "imagen": "img/datasets/prestamos.jpg",
        "descripcion": "Predicción de aprobación de un préstamo bancario según el riesgo crediticio.",
        "objetivo": "loan_approved",
        "problema": "clasificacion",
        "color_a": "#4ade80", "color_b": "#15803d",  # verde (finanzas)
    },
}

_CACHE_DATAFRAMES = {}

# Fila cruda del último archivo subido por el usuario (CSV o Excel), ANTES de que elija qué
# columnas usar y cuál es el objetivo. Solo hay un dataset subido a la vez: esta app es de un
# solo usuario local, así que no hace falta guardar un historial de archivos subidos.
DATASET_SUBIDO = {"df": None, "nombre_archivo": None}

MIN_FILAS_CONFIABLE = 50
LIMITE_FILAS_SUBIDA = 20000
LIMITE_MB_SUBIDA = 5


def _es_columna_identificadora(nombre_columna: str, serie) -> bool:
    """Detecta columnas que probablemente sean un identificador (N°, ID, nombre propio) y no
    una variable útil para predecir: o bien todos sus valores son distintos entre sí (no hay
    ningún patrón que repetir), o su nombre es uno de los típicos de una columna de este tipo."""
    nombre_normalizado = nombre_columna.strip().lower()
    palabras_clave = {"id", "n", "n°", "no", "nro", "número", "numero", "nombre", "apellido",
                       "index", "índice", "indice", "codigo", "código"}
    if nombre_normalizado in palabras_clave:
        return True
    if len(serie) > 1 and serie.nunique() == len(serie):
        return True
    return False


def analizar_archivo_subido(df, nombre_archivo: str) -> dict:
    """Guarda el DataFrame recién subido (todavía sin confirmar) y arma la información que la
    pantalla de subida necesita para mostrar la vista previa: columnas disponibles, cuáles
    sugerir excluir (parecen identificador) y si hay pocas filas para un resultado confiable."""
    DATASET_SUBIDO["df"] = df
    DATASET_SUBIDO["nombre_archivo"] = nombre_archivo

    columnas = df.columns.tolist()
    sugeridas_excluir = [c for c in columnas if _es_columna_identificadora(c, df[c])]

    return {
        "nombre_archivo": nombre_archivo,
        "filas": int(df.shape[0]),
        "columnas": columnas,
        "sugeridas_excluir": sugeridas_excluir,
        # .replace() (no .where()): en una columna numérica, .where(cond, None) hace que pandas
        # vuelva a convertir ese None a NaN para mantener el tipo float — y un NaN literal en el
        # JSON de respuesta rompe el fetch() del navegador (NaN no es JSON válido, a diferencia
        # de Python). .replace() sí cambia la columna a tipo genérico y deja el None real.
        "preview": df.head(8).replace({np.nan: None}).to_dict(orient="records"),
        "pocas_filas": df.shape[0] < MIN_FILAS_CONFIABLE,
    }


def registrar_dataset_subido(df, objetivo: str, problema: str, nombre_archivo: str):
    """Da de alta el dataset ya confirmado (columnas elegidas + objetivo) como un dataset más
    del sistema, con la clave fija "subido": a partir de acá se analiza exactamente igual que
    cualquiera de los datasets incluidos (mismo cargar_dataset/seleccionar_dataset/ESTADO)."""
    DATASETS["subido"] = {
        "archivo": None,
        "nombre": nombre_archivo,
        "icono": "📁",
        "imagen": None,
        "descripcion": f'Dataset subido por el usuario ("{nombre_archivo}").',
        "objetivo": objetivo,
        "problema": problema,
        "color_a": "#94a3b8", "color_b": "#64748b",
    }
    _CACHE_DATAFRAMES["subido"] = df.copy()

# Estado del análisis actualmente en curso (se reinicia al seleccionar un nuevo dataset).
ESTADO = {
    "dataset": None,
    "df_procesado": None,
    "transformaciones": [],
    "transformadores": None,
    "info_columnas_originales": None,
    "X": None,
    "y": None,
    "columnas_features": None,
    "columnas_numericas": None,
    "columnas_categoricas": None,
    "X_train": None,
    "X_test": None,
    "y_train": None,
    "y_test": None,
    "modelo": None,
    "nombre_modelo": None,
    "modelos_entrenados": None,
    "predicciones_por_modelo": None,
    "problema": None,
    "y_pred": None,
    "metricas": None,
    "comparacion_modelos": None,
    "parametros_modelos": None,
    "algebra": None,
    "estadistica": None,
    "outliers": None,
    "graficos": None,
    "matriz_confusion_url": None,
    "real_vs_prediccion_url": None,
    "predicciones": None,
    "comparacion_chart_url": None,
    "comparacion_chart_explicacion": None,
    "importancia_url": None,
    "importancia_explicacion": None,
    "importancia_disponible": None,
}

HISTORIAL = []


def listar_datasets():
    """Devuelve la lista de datasets disponibles con sus metadatos, para las tarjetas de inicio."""
    return [{"id": clave, **valor} for clave, valor in DATASETS.items()]


def obtener_metadata(nombre: str):
    if nombre not in DATASETS:
        raise ValueError(f'Dataset "{nombre}" no existe.')
    return DATASETS[nombre]


def cargar_dataset(nombre: str) -> pd.DataFrame:
    """Carga el CSV del dataset (con caché) y devuelve una copia para no mutar el original."""
    if nombre not in DATASETS:
        raise ValueError(f'Dataset "{nombre}" no existe.')

    if nombre not in _CACHE_DATAFRAMES:
        ruta = os.path.join(DATA_DIR, DATASETS[nombre]["archivo"])
        if not os.path.isfile(ruta):
            raise FileNotFoundError(
                f'No se encontró {ruta}. Ejecuta "python generar_datasets.py" primero.'
            )
        _CACHE_DATAFRAMES[nombre] = pd.read_csv(ruta)

    return _CACHE_DATAFRAMES[nombre].copy()


def seleccionar_dataset(nombre: str) -> pd.DataFrame:
    """Selecciona un dataset como el actual, reiniciando el estado del análisis en curso."""
    df = cargar_dataset(nombre)
    ESTADO.update({
        "dataset": nombre,
        "df_procesado": None,
        "transformaciones": [],
        "transformadores": None,
        "info_columnas_originales": None,
        "X": None,
        "y": None,
        "columnas_features": None,
        "columnas_numericas": None,
        "columnas_categoricas": None,
        "X_train": None,
        "X_test": None,
        "y_train": None,
        "y_test": None,
        "modelo": None,
        "nombre_modelo": None,
        "modelos_entrenados": None,
        "predicciones_por_modelo": None,
        "problema": DATASETS[nombre]["problema"],
        "y_pred": None,
        "metricas": None,
        "comparacion_modelos": None,
        "parametros_modelos": None,
        "algebra": None,
        "estadistica": None,
        "outliers": None,
        "graficos": None,
        "matriz_confusion_url": None,
        "real_vs_prediccion_url": None,
        "predicciones": None,
        "comparacion_chart_url": None,
        "comparacion_chart_explicacion": None,
        "importancia_url": None,
        "importancia_explicacion": None,
        "importancia_disponible": None,
    })
    return df


def dataset_actual() -> str:
    if not ESTADO["dataset"]:
        raise ValueError("No hay un dataset seleccionado. Selecciona uno primero.")
    return ESTADO["dataset"]


def df_actual() -> pd.DataFrame:
    """DataFrame a usar para el análisis: el preprocesado si ya existe, si no el original."""
    if ESTADO["df_procesado"] is not None:
        return ESTADO["df_procesado"]
    return cargar_dataset(dataset_actual())


def registrar_en_historial(entrada: dict):
    HISTORIAL.insert(0, entrada)
    del HISTORIAL[20:]  # conserva solo las 20 entradas más recientes
