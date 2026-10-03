"""Carga y metadatos de los 9 datasets incluidos y de los que sube la persona.

Mantiene en memoria el DataFrame original de cada dataset ya leído (caché simple por
nombre) para no releer el CSV en cada análisis, y guarda el análisis de cada dataset
(versión preprocesada, modelo entrenado, predicciones y lo que devolvió cada paso) en
memoria y en disco: el proyecto es de un solo usuario local, así que no hace falta una
base de datos ni sesiones por usuario para esto.
"""

import json
import os
import pickle
import re
import threading
import time
import unicodedata
import uuid
from datetime import datetime
from collections.abc import MutableMapping
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageOps

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
        "objetivo": "especie",
        "problema": "clasificacion",
        "color_a": "#c084fc", "color_b": "#ec4899",  # violeta -> rosa (floral)
    },
    "semillas": {
        "archivo": "semillas.csv",
        "nombre": "Semillas de trigo",
        "icono": "🌾",
        "imagen": "img/datasets/semillas.jpg",
        "descripcion": "Clasificación de 3 variedades de trigo (Kama, Rosa, Canadiense) según 7 medidas del grano.",
        "objetivo": "clase",
        "problema": "clasificacion",
        "color_a": "#fbbf24", "color_b": "#b45309",  # trigo: dorado -> marrón
    },
    "trigo_simulado": {
        "archivo": "trigo_simulado.csv",
        "nombre": "Trigo simulado",
        "icono": "🌾",
        "imagen": "img/datasets/trigo_simulado.jpg",
        "descripcion": "300 granos simulados con la misma forma que el trigo real: 3 variedades (Kama, Rosa, Canadiense) y 7 medidas del grano.",
        "objetivo": "clase",
        "problema": "clasificacion",
        "color_a": "#a3e635", "color_b": "#3f6212",  # trigo verde (todavía en la espiga)
    },
    "diabetes": {
        "archivo": "diabetes.csv",
        "nombre": "Diabetes",
        "icono": "❤️",
        "imagen": "img/datasets/diabetes.jpg",
        "descripcion": "Diagnóstico de diabetes a partir de indicadores clínicos.",
        "objetivo": "diabetes",
        "problema": "clasificacion",
        "color_a": "#fb7185", "color_b": "#e11d48",  # rosa -> rojo (clínico)
    },
    "viviendas": {
        "archivo": "viviendas.csv",
        "nombre": "Viviendas",
        "icono": "🏠",
        "imagen": "img/datasets/viviendas.jpg",
        "descripcion": "Predicción del precio de una vivienda según sus características.",
        "objetivo": "precio",
        "problema": "regresion",
        "color_a": "#38bdf8", "color_b": "#0ea5e9",  # celeste (cielo/hogar)
    },
    "vehiculos": {
        "archivo": "vehiculos.csv",
        "nombre": "Vehículos",
        "icono": "🚗",
        "imagen": "img/datasets/vehiculos.jpg",
        "descripcion": "Predicción del precio de un vehículo según sus especificaciones técnicas.",
        "objetivo": "precio",
        "problema": "regresion",
        "color_a": "#fb923c", "color_b": "#ea580c",  # naranja (energía/velocidad)
    },
    "clientes": {
        "archivo": "clientes.csv",
        "nombre": "Clientes",
        "icono": "🛒",
        "imagen": "img/datasets/clientes.jpg",
        "descripcion": "Segmentación de clientes según su comportamiento de compra.",
        "objetivo": "segmento",
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
        "descripcion": "Predicción de la renuncia de un empleado según su situación laboral.",
        "objetivo": "renuncia",
        "problema": "clasificacion",
        "color_a": "#64748b", "color_b": "#334155",  # gris azulado (corporativo/RRHH)
    },
    "estudiantes": {
        "archivo": "estudiantes.csv",
        "nombre": "Estudiantes",
        "icono": "🎓",
        "imagen": "img/datasets/estudiantes.jpg",
        "descripcion": "Predicción de la nota final de un estudiante según sus hábitos de estudio.",
        "objetivo": "nota_final",
        "problema": "regresion",
        "color_a": "#fbbf24", "color_b": "#d97706",  # ámbar (académico)
    },
    "prestamos": {
        "archivo": "prestamos.csv",
        "nombre": "Préstamos",
        "icono": "🏦",
        "imagen": "img/datasets/prestamos.jpg",
        "descripcion": "Predicción de aprobación de un préstamo bancario según el riesgo crediticio.",
        "objetivo": "préstamo_aprobado",
        "problema": "clasificacion",
        "color_a": "#4ade80", "color_b": "#15803d",  # verde (finanzas)
    },
}

# Datasets incluidos con la aplicación; los demás de DATASETS son los que sube la persona.
INCLUIDOS = frozenset(DATASETS)

_CACHE_DATAFRAMES = {}

# Último archivo subido (CSV o Excel) ANTES de que la persona elija qué columnas usar y cuál es
# el objetivo. Al confirmar se guarda en disco como un dataset más (ver registrar_dataset_subido).
# Archivos recién subidos que todavía no se confirmaron (se pueden subir varios a la vez): cada
# uno con su número, hasta que la persona elige las columnas y lo agrega. Se olvidan a la hora.
SUBIDAS_PENDIENTES = {}
_LOCK_SUBIDAS = threading.Lock()
MAX_SUBIDAS_PENDIENTES = 20
VIDA_SUBIDA_SEGUNDOS = 60 * 60

MIN_FILAS_CONFIABLE = 50
LIMITE_FILAS_SUBIDA = 20000
LIMITE_MB_SUBIDA = 5
LIMITE_MB_PORTADA = 8
EXTENSIONES_PORTADA = {".jpg", ".jpeg", ".png", ".webp"}

# Colores que se van turnando entre los datasets subidos, para que cada tarjeta se distinga.
COLORES_SUBIDOS = [
    ("#f472b6", "#db2777"), ("#a78bfa", "#7c3aed"), ("#2dd4bf", "#0f766e"),
    ("#60a5fa", "#2563eb"), ("#facc15", "#ca8a04"), ("#94a3b8", "#64748b"),
]


def _es_columna_identificadora(nombre_columna: str, serie) -> bool:
    """Detecta columnas que probablemente sean un identificador (N°, ID, nombre propio) y no
    una variable útil para predecir: o bien todos sus valores son distintos entre sí (no hay
    ningún patrón que repetir), o su nombre es uno de los típicos de una columna de este tipo."""
    nombre_normalizado = str(nombre_columna).strip().lower()
    palabras_clave = {"id", "n", "n°", "no", "nro", "número", "numero", "nombre", "apellido",
                       "index", "índice", "indice", "codigo", "código"}
    if nombre_normalizado in palabras_clave:
        return True
    if len(serie) > 1 and serie.nunique() == len(serie):
        return True
    return False


def analizar_archivo_subido(df, nombre_archivo: str, formato: str = "csv") -> dict:
    """Guarda el DataFrame recién subido (todavía sin confirmar) y arma la información que la
    pantalla de subida necesita para mostrar la vista previa: cuántas columnas y filas se
    detectaron, columnas disponibles, cuáles sugerir excluir (parecen identificador), columnas
    vacías o repetidas y si hay pocas filas para un resultado confiable."""
    df.columns = [str(c) for c in df.columns]
    token = uuid.uuid4().hex
    ahora = time.time()
    with _LOCK_SUBIDAS:
        for clave in [c for c, v in SUBIDAS_PENDIENTES.items() if ahora - v["creado"] > VIDA_SUBIDA_SEGUNDOS]:
            del SUBIDAS_PENDIENTES[clave]
        while len(SUBIDAS_PENDIENTES) >= MAX_SUBIDAS_PENDIENTES:
            del SUBIDAS_PENDIENTES[min(SUBIDAS_PENDIENTES, key=lambda c: SUBIDAS_PENDIENTES[c]["creado"])]
        SUBIDAS_PENDIENTES[token] = {"df": df, "nombre_archivo": nombre_archivo, "formato": formato, "creado": ahora}

    columnas = df.columns.tolist()
    sugeridas_excluir = [c for c in columnas if _es_columna_identificadora(c, df[c])]
    # pandas renombra los encabezados repetidos como «nota.1», «nota.2»…
    repetidas = [c for c in columnas if re.fullmatch(r"(.+)\.\d+", c) and re.fullmatch(r"(.+)\.\d+", c).group(1) in columnas]

    return {
        "token": token,
        "formato": formato,
        "total_columnas": len(columnas),
        "columnas_vacias": [c for c in columnas if df[c].isnull().all()],
        "columnas_repetidas": repetidas,
        "nombre_archivo": nombre_archivo,
        "filas": int(df.shape[0]),
        "columnas": columnas,
        "sugeridas_excluir": sugeridas_excluir,
        # .replace() (no .where()): en una columna numérica, .where(cond, None) hace que pandas
        # vuelva a convertir ese None a NaN para mantener el tipo float — y un NaN literal en el
        # JSON de respuesta rompe el fetch() del navegador (NaN no es JSON válido, a diferencia
        # de Python). .replace() sí cambia la columna a tipo genérico y deja el None real.
        "preview": df.head(8).replace({np.nan: None}).to_dict(orient="records"),
        "filas_vista_previa": int(min(8, df.shape[0])),
        "pocas_filas": df.shape[0] < MIN_FILAS_CONFIABLE,
    }


# ============================================================
# DATASETS SUBIDOS (guardados en disco, cada uno en su carpeta)
# ============================================================

# ============================================================
# COLOR DE CADA DATASET (lo puede elegir la persona; se usa en la página y en el PDF)
# ============================================================

# Colores sugeridos: todos lo bastante claros para que el texto oscuro se lea encima.
COLORES_TEMA = [
    "#ffd23f", "#fbbf24", "#fb923c", "#fb7185", "#f472b6", "#c084fc",
    "#a78bfa", "#818cf8", "#60a5fa", "#38bdf8", "#2dd4bf", "#34d399",
    "#4ade80", "#a3e635", "#94a3b8", "#d6a77a",
]


def _ruta_colores() -> Path:
    return cfg.RAIZ / "colores_datasets.json"


def _luminancia(hex_color: str) -> float:
    canales = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lineales = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
    return 0.2126 * lineales[0] + 0.7152 * lineales[1] + 0.0722 * lineales[2]


def _oscurecer(hex_color: str, factor: float = 0.8) -> str:
    return "#" + "".join(f"{round(int(hex_color[i:i + 2], 16) * factor):02x}" for i in (1, 3, 5))


def _cargar_colores():
    """Colores elegidos para los datasets incluidos (los de los subidos van en su info.json)."""
    try:
        with open(_ruta_colores(), encoding="utf-8") as f:
            elegidos = json.load(f)
    except (OSError, ValueError):
        return
    for nombre, color in elegidos.items():
        if nombre in INCLUIDOS and re.fullmatch(r"#[0-9a-fA-F]{6}", str(color)):
            DATASETS[nombre].update(color_a=color, color_b=_oscurecer(color))


def guardar_color(nombre: str, color: str):
    if nombre not in DATASETS:
        raise ValueError(f'Dataset "{nombre}" no existe.')
    color = str(color or "").strip().lower()
    if not re.fullmatch(r"#[0-9a-f]{6}", color):
        raise ValueError("Color no válido.")
    if _luminancia(color) < 0.2:
        raise ValueError("Ese color es muy oscuro: el texto no se leería bien encima. Elige uno más claro.")
    color_b = _oscurecer(color)
    with BLOQUEO:
        if es_subido(nombre):
            info = {k: v for k, v in DATASETS[nombre].items() if k not in ("archivo", "imagen")}
            info.update(color_a=color, color_b=color_b)
            _guardar_info(nombre, info)
        else:
            try:
                with open(_ruta_colores(), encoding="utf-8") as f:
                    elegidos = json.load(f)
            except (OSError, ValueError):
                elegidos = {}
            elegidos[nombre] = color
            temporal = _ruta_colores().with_suffix(".tmp")
            with open(temporal, "w", encoding="utf-8") as f:
                json.dump(elegidos, f, ensure_ascii=False, indent=2)
            os.replace(temporal, _ruta_colores())
        DATASETS[nombre].update(color_a=color, color_b=color_b)
    return color, color_b


def _slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")
    return texto[:40].strip("-") or "dataset"


def _carpeta_subido(nombre: str) -> Path:
    return cfg.SUBIDOS_DIR / nombre


def es_subido(nombre: str) -> bool:
    return nombre in DATASETS and nombre not in INCLUIDOS


def _guardar_info(nombre: str, info: dict):
    ruta = _carpeta_subido(nombre) / "info.json"
    temporal = ruta.with_suffix(".tmp")
    with open(temporal, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    os.replace(temporal, ruta)


def _cargar_subidos():
    """Da de alta los datasets que la persona subió en sesiones anteriores."""
    if not cfg.SUBIDOS_DIR.is_dir():
        return
    encontrados = []
    for carpeta in cfg.SUBIDOS_DIR.iterdir():
        if not ((carpeta / "info.json").is_file() and (carpeta / "datos.csv").is_file()):
            continue
        try:
            with open(carpeta / "info.json", encoding="utf-8") as f:
                info = json.load(f)
            encontrados.append((info.get("fecha", ""), carpeta.name, info))
        except Exception as exc:
            print(f"No se pudo leer el dataset subido {carpeta.name}: {exc}")
    for _, nombre, info in sorted(encontrados):
        DATASETS[nombre] = {"archivo": None, "imagen": None, **info}


def subida_pendiente(token):
    """El archivo subido que espera confirmación, o None si ya no está."""
    with _LOCK_SUBIDAS:
        return SUBIDAS_PENDIENTES.get(token) if token else None


def quitar_subida_pendiente(token):
    with _LOCK_SUBIDAS:
        SUBIDAS_PENDIENTES.pop(token, None)


def registrar_dataset_subido(df, objetivo: str, problema: str, nombre_archivo: str, formato: str = "csv") -> str:
    """Guarda en disco el dataset ya confirmado (columnas elegidas + objetivo) y lo da de alta
    como un dataset más: a partir de acá se analiza igual que los incluidos y sigue disponible
    aunque se cierre la aplicación. Devuelve su identificador."""
    nombre = f"{_slug(os.path.splitext(nombre_archivo)[0])}-{uuid.uuid4().hex[:6]}"
    carpeta = _carpeta_subido(nombre)
    carpeta.mkdir(parents=True, exist_ok=False)
    df.to_csv(carpeta / "datos.csv", index=False, encoding="utf-8")

    cantidad_subidos = sum(1 for n in DATASETS if n not in INCLUIDOS)
    color_a, color_b = COLORES_SUBIDOS[cantidad_subidos % len(COLORES_SUBIDOS)]
    info = {
        "nombre": nombre_archivo,
        "icono": "📁",
        "descripcion": f"Dataset subido por el usuario: {nombre_archivo}.",
        "objetivo": objetivo,
        "problema": problema,
        "color_a": color_a, "color_b": color_b,
        "portada": None,
        "formato": formato,
        "fecha": datetime.now().isoformat(timespec="seconds"),
    }
    _guardar_info(nombre, info)
    DATASETS[nombre] = {"archivo": None, "imagen": None, **info}
    _CACHE_DATAFRAMES[nombre] = pd.read_csv(carpeta / "datos.csv")
    return nombre


def guardar_portada(nombre: str, archivo):
    """Guarda la foto de portada de un dataset subido (se usa en la página y en el informe PDF).
    Se abre con Pillow para comprobar que de verdad es una imagen, se endereza según la
    orientación de la cámara y se guarda como JPG de tamaño moderado."""
    if not es_subido(nombre):
        raise ValueError("Solo los datasets subidos pueden cambiar su portada.")
    extension = os.path.splitext(archivo.filename or "")[1].lower()
    if extension not in EXTENSIONES_PORTADA:
        raise ValueError("La portada debe ser una imagen .jpg, .png o .webp.")
    archivo.stream.seek(0, os.SEEK_END)
    tamano_mb = archivo.stream.tell() / (1024 * 1024)
    archivo.stream.seek(0)
    if tamano_mb > LIMITE_MB_PORTADA:
        raise ValueError(f"La imagen pesa {tamano_mb:.1f} MB; el máximo es {LIMITE_MB_PORTADA} MB.")

    try:
        imagen = Image.open(archivo.stream)
        imagen = ImageOps.exif_transpose(imagen).convert("RGB")
    except Exception:
        raise ValueError("No se pudo abrir el archivo como imagen. Prueba con otra foto (.jpg o .png).")
    imagen.thumbnail((1600, 1600))
    # Una foto normal (de 3:4 a 2:1) llena el marco; una muy alargada se muestra entera con un
    # fondo difuminado de la misma foto, para no recortar casi toda la imagen.
    proporcion = imagen.width / imagen.height
    ajuste = "cubrir" if 0.75 <= proporcion <= 2.0 else "contener"
    carpeta = _carpeta_subido(nombre)
    temporal = carpeta / "portada.tmp"
    imagen.save(temporal, format="JPEG", quality=88)
    os.replace(temporal, carpeta / "portada.jpg")

    info = {k: v for k, v in DATASETS[nombre].items() if k not in ("archivo", "imagen")}
    info["portada"] = "portada.jpg"
    info["portada_ajuste"] = ajuste
    info["portada_version"] = int(time.time() * 1000)
    _guardar_info(nombre, info)
    DATASETS[nombre].update(info)
    if min(imagen.width, imagen.height) < 400:
        return (f"La foto es pequeña ({imagen.width}×{imagen.height} píxeles): se guardó, pero puede verse "
                "borrosa. Si tienes una más grande, se verá mejor.")
    return None


def ruta_portada(nombre: str):
    """Ruta del archivo de portada de un dataset (incluido o subido), o None si no tiene."""
    meta = DATASETS.get(nombre) or {}
    if es_subido(nombre):
        ruta = _carpeta_subido(nombre) / "portada.jpg"
        return ruta if meta.get("portada") and ruta.is_file() else None
    if meta.get("imagen"):
        ruta = cfg.CODIGO / "static" / meta["imagen"]
        return ruta if ruta.is_file() else None
    return None


def _url_portada(nombre: str):
    meta = DATASETS[nombre]
    if es_subido(nombre):
        return f"/portada/{nombre}?v={meta.get('portada_version', 0)}" if ruta_portada(nombre) else None
    return f"/static/{meta['imagen']}" if meta.get("imagen") else None


def listar_datasets():
    """Devuelve la lista de datasets disponibles con sus metadatos, para las tarjetas de inicio."""
    return [obtener_metadata(clave) for clave in DATASETS]


def obtener_metadata(nombre: str):
    if nombre not in DATASETS:
        raise ValueError(f'Dataset "{nombre}" no existe.')
    ruta = ruta_portada(nombre)
    return {
        **DATASETS[nombre], "id": nombre, "subido": es_subido(nombre),
        "imagen_url": _url_portada(nombre), "imagen_ruta": str(ruta) if ruta else None,
    }


def cargar_dataset(nombre: str) -> pd.DataFrame:
    """Carga el CSV del dataset (con caché) y devuelve una copia para no mutar el original."""
    if nombre not in DATASETS:
        raise ValueError(f'Dataset "{nombre}" no existe.')

    if nombre not in _CACHE_DATAFRAMES:
        if es_subido(nombre):
            ruta = str(_carpeta_subido(nombre) / "datos.csv")
        else:
            ruta = os.path.join(DATA_DIR, DATASETS[nombre]["archivo"])
        if not os.path.isfile(ruta):
            raise FileNotFoundError(f"No se encontró el archivo de datos {ruta}.")
        _CACHE_DATAFRAMES[nombre] = pd.read_csv(ruta)

    return _CACHE_DATAFRAMES[nombre].copy()


# ============================================================
# ESTADO DEL ANÁLISIS (uno por dataset, guardado en disco)
# ============================================================
# Cada dataset tiene su propio análisis en _ESTADOS (y en disco, en analisis_guardados/), así
# que cambiar de página, de dataset o cerrar la aplicación no pierde lo ya calculado. ESTADO
# apunta siempre al del dataset abierto ahora. "respuestas" guarda lo que devolvió cada paso
# para volver a mostrarlo sin recalcular. Un paso que sigue calculando después de que la
# persona abrió otro dataset escribe en el análisis de SU dataset (ver estado_de).

_CLAVES_ANALISIS = [
    "df_procesado", "info_columnas_originales", "mapeo_objetivo", "columnas_features",
    "X_train", "X_test", "y_train", "y_test", "modelo", "nombre_modelo", "modelos_entrenados",
    "predicciones_por_modelo", "y_pred", "metricas", "comparacion_modelos", "parametros_modelos",
    "particiones", "metrica_cv", "algebra", "estadistica", "outliers", "graficos", "matriz_confusion_url",
    "real_vs_prediccion_url", "predicciones", "comparacion_chart_url", "comparacion_chart_explicacion",
    "importancia_url", "importancia_explicacion", "importancia_disponible",
]

# Qué queda desactualizado cuando se vuelve a ejecutar un paso: (pasos a descartar, claves a vaciar).
_CLAVES_ENTRENAMIENTO = [
    "columnas_features", "X_train", "X_test", "y_train", "y_test", "modelo", "nombre_modelo",
    "modelos_entrenados", "predicciones_por_modelo", "y_pred", "metricas", "comparacion_modelos",
    "parametros_modelos", "particiones", "metrica_cv", "comparacion_chart_url", "comparacion_chart_explicacion",
    "importancia_url", "importancia_explicacion", "importancia_disponible",
]
_CLAVES_EVALUACION = ["matriz_confusion_url", "real_vs_prediccion_url", "predicciones"]
_INVALIDA = {
    "explorar": ([], []),
    "algebra": (["pdf"], []),
    # La estadística, los atípicos y los gráficos usan los datos originales (ver df_original):
    # volver a preprocesar no los cambia, así que no se descartan.
    "preprocesar": (["entrenar", "evaluar", "pdf"], _CLAVES_ENTRENAMIENTO + _CLAVES_EVALUACION),
    "entrenar": (["evaluar", "pdf"], _CLAVES_EVALUACION),
    "pdf": ([], []),
}

VERSION_ESTADO = 2
# Sube cuando cambian los nombres de las columnas de los datasets incluidos (la 2 los pasó al
# español): un análisis guardado con los nombres anteriores ya no sirve y se empieza de nuevo.
# Los datasets subidos por la persona no se ven afectados.
VERSION_COLUMNAS_INCLUIDOS = 2
BLOQUEO = threading.RLock()


def estado_vacio(nombre=None) -> dict:
    estado = {clave: None for clave in _CLAVES_ANALISIS}
    estado.update({
        "dataset": nombre, "transformaciones": [], "respuestas": {},
        "problema": DATASETS[nombre]["problema"] if nombre in DATASETS else None,
    })
    return estado


_ESTADOS = {}
_ACTUAL = {"nombre": None}
_SIN_DATASET = estado_vacio()


class _EstadoActual(MutableMapping):
    """El análisis del dataset abierto ahora (se usa como un diccionario normal)."""

    def _datos(self):
        return _ESTADOS[_ACTUAL["nombre"]] if _ACTUAL["nombre"] else _SIN_DATASET

    def __getitem__(self, clave):
        return self._datos()[clave]

    def __setitem__(self, clave, valor):
        self._datos()[clave] = valor

    def __delitem__(self, clave):
        del self._datos()[clave]

    def __iter__(self):
        return iter(self._datos())

    def __len__(self):
        return len(self._datos())


ESTADO = _EstadoActual()


def _ruta_estado(nombre: str) -> Path:
    return cfg.ESTADOS_DIR / f"{nombre}.pkl"


def _leer_estado(nombre: str):
    ruta = _ruta_estado(nombre)
    if not ruta.is_file():
        return None
    try:
        with open(ruta, "rb") as f:
            datos = pickle.load(f)
        columnas_al_dia = nombre not in INCLUIDOS or datos.get("columnas") == VERSION_COLUMNAS_INCLUIDOS
        if datos.get("version") == VERSION_ESTADO and datos["estado"].get("dataset") == nombre and columnas_al_dia:
            return {**estado_vacio(nombre), **datos["estado"]}
    except Exception as exc:
        print(f"No se pudo leer el análisis guardado de {nombre}: {exc}")
    return None


def estado_de(nombre: str) -> dict:
    """Análisis de un dataset (esté abierto o no). Quien vaya a modificarlo desde otro hilo
    debe hacerlo dentro de `with BLOQUEO:`."""
    with BLOQUEO:
        if nombre not in _ESTADOS:
            _ESTADOS[nombre] = _leer_estado(nombre) or estado_vacio(nombre)
        return _ESTADOS[nombre]


def guardar_estado(nombre: str = None):
    """Guarda en disco el análisis de un dataset. Si falla, el análisis sigue en memoria."""
    with BLOQUEO:
        nombre = nombre or ESTADO["dataset"]
        if not nombre:
            return
        estado = estado_de(nombre)
        ruta = _ruta_estado(nombre)
        try:
            temporal = ruta.with_suffix(".tmp")
            with open(temporal, "wb") as f:
                pickle.dump({"version": VERSION_ESTADO, "columnas": VERSION_COLUMNAS_INCLUIDOS, "estado": estado},
                            f, protocol=pickle.HIGHEST_PROTOCOL)
            os.replace(temporal, ruta)
        except Exception as exc:
            print(f"No se pudo guardar el análisis de {nombre}: {exc}")


def guardar_respuesta(accion: str, respuesta: dict, estado: dict = None):
    """Guarda lo que devolvió un paso y descarta lo que ese paso deja desactualizado."""
    with BLOQUEO:
        estado = estado if estado is not None else ESTADO
        pasos, claves = _INVALIDA.get(accion, (["pdf"], []))
        for paso in pasos:
            estado["respuestas"].pop(paso, None)
        for clave in claves:
            estado[clave] = None
        estado["respuestas"][accion] = respuesta


def seleccionar_dataset(nombre: str):
    """Abre un dataset. Si ya tenía un análisis (en memoria o guardado) se recupera tal cual."""
    with BLOQUEO:
        cargar_dataset(nombre)
        estado_de(nombre)
        _ACTUAL["nombre"] = nombre


def reiniciar_analisis(nombre: str):
    """Borra todo lo calculado para un dataset (el dataset en sí no se toca)."""
    with BLOQUEO:
        _ESTADOS[nombre] = estado_vacio(nombre)
        try:
            _ruta_estado(nombre).unlink(missing_ok=True)
        except OSError as exc:
            print(f"No se pudo borrar el análisis guardado de {nombre}: {exc}")


def dataset_actual() -> str:
    if not ESTADO["dataset"]:
        raise ValueError("No hay un dataset seleccionado. Selecciona uno primero.")
    return ESTADO["dataset"]


def df_original(estado: dict) -> pd.DataFrame:
    """El dataset tal como es, sin normalizar ni codificar: la estadística, los valores atípicos y
    los gráficos se calculan siempre sobre los valores reales (p. ej. la media de «Area» en cm²,
    no ~0 como quedaría después de StandardScaler)."""
    return cargar_dataset(estado["dataset"])


def df_de(estado: dict) -> pd.DataFrame:
    """DataFrame a usar para el análisis: el preprocesado si ya existe, si no el original."""
    if estado["df_procesado"] is not None:
        return estado["df_procesado"]
    return cargar_dataset(estado["dataset"])


_cargar_subidos()
_cargar_colores()
