"""DataExpert IA — Plataforma de análisis matemático, estadístico y de Machine Learning.

Servidor Flask: cada botón del dashboard llama a un endpoint que ejecuta un cálculo real
(Pandas, NumPy, Scikit-learn, Matplotlib/Seaborn o ReportLab) sobre el dataset actualmente
seleccionado, sin resultados simulados ni escritos a mano. Lo que devuelve cada paso queda
guardado por dataset (ver dataset_service), así que se puede volver a verlo sin recalcular.
"""

import os
import sys
import io
import json
import re
import threading
import uuid
from collections import deque
from datetime import datetime

# Fuerza salida UTF-8 para que los emoji de los mensajes no rompan la consola de Windows
# (por defecto usa el codepage cp1252, que no incluye esos caracteres).
if sys.stdout is not None and sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr is not None and sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import pandas as pd
from flask import Flask, render_template, jsonify, request, send_file, send_from_directory, url_for, abort
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import configuracion as cfg
from src import dataset_service as ds
from src import preprocessing_service as pre
from src import statistics_service as stats
from src import linear_algebra_service as algebra_srv
from src import visualization_service as viz
from src import machine_learning_service as ml
from src import pdf_service as pdf_srv

INFORMES_DIR = str(cfg.INFORMES_DIR)
RESULTADOS_DIR = str(cfg.RESULTADOS_DIR)
HISTORIAL_PATH = str(cfg.HISTORIAL_PATH)

cfg.preparar_carpetas()

app = Flask(__name__, template_folder=str(cfg.CODIGO / "templates"), static_folder=str(cfg.CODIGO / "static"))
# Tope para cualquier archivo enviado (datasets de 5 MB y fotos de portada de 8 MB, más margen):
# así Flask corta la subida antes de leer un archivo enorme entero.
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


@app.errorhandler(RequestEntityTooLarge)
def archivo_demasiado_grande(_):
    return _error("El archivo es demasiado grande (máximo 10 MB).", 413)


@app.route("/api/salud")
def api_salud():
    """Lo usa el lanzador de Windows para saber si ya hay una copia abierta."""
    return jsonify({"ok": True, "aplicacion": "dataexpert_ia"})


@app.route("/graficos-generados/<path:ruta>")
def graficos_generados(ruta):
    """Gráficos que genera el análisis; en la versión instalada viven en la carpeta de datos, fuera del código."""
    return send_from_directory(str(cfg.GRAFICOS_DIR), ruta)


@app.route("/portada/<nombre>")
def portada_dataset(nombre):
    """Foto de portada de un dataset subido (vive en la carpeta de datos de la persona)."""
    ruta = ds.ruta_portada(nombre) if ds.es_subido(nombre) else None
    if not ruta:
        abort(404)
    return send_file(str(ruta), mimetype="image/jpeg", max_age=0)


# Cambia cada vez que arranca el servidor: los avisos ya vistos se recuerdan por arranque, porque
# la numeración de los procesos vuelve a empezar al abrir de nuevo la aplicación.
ARRANQUE = uuid.uuid4().hex[:12]


@app.context_processor
def inyectar_menu_de_datasets():
    """La lista «Datasets» de la barra superior aparece en todas las páginas."""
    return {"menu_datasets": ds.listar_datasets(), "arranque": ARRANQUE}


def _error(mensaje: str, codigo: int = 400):
    return jsonify({"ok": False, "error": mensaje}), codigo


_LOCK_HISTORIAL = threading.Lock()


def _cargar_historial():
    if os.path.isfile(HISTORIAL_PATH):
        try:
            with open(HISTORIAL_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _guardar_en_historial(entrada: dict):
    with _LOCK_HISTORIAL:
        historial = _cargar_historial()
        historial.insert(0, entrada)
        with open(HISTORIAL_PATH, "w", encoding="utf-8") as f:
            json.dump(historial[:25], f, ensure_ascii=False, indent=2)


def _ruta_pdf(nombre: str) -> str:
    return os.path.join(INFORMES_DIR, f"Informe_{nombre}.pdf")


# ============================================================
# PÁGINAS
# ============================================================

@app.route("/")
def inicio():
    return render_template("index.html", datasets=ds.listar_datasets())


@app.route("/dataset/<nombre>")
def seleccionar_dataset_pagina(nombre):
    try:
        meta = ds.obtener_metadata(nombre)
        ds.seleccionar_dataset(nombre)
    except (ValueError, FileNotFoundError) as exc:
        return render_template("index.html", datasets=ds.listar_datasets(), error=str(exc))
    return render_template("dashboard.html", meta=meta, colores_tema=ds.COLORES_TEMA)


@app.route("/subir")
def subir_pagina():
    return render_template("subir.html")


# ============================================================
# API — SUBIDA DE DATASET PROPIO (CSV / Excel) Y SU PORTADA
# ============================================================

EXTENSIONES_PERMITIDAS_SUBIDA = {".csv", ".xlsx", ".xls"}


def _leer_archivo_subido(archivo, minimo_columnas: int = 2):
    """Valida y parsea el archivo subido (nombre, tamaño, tipo, contenido). Nunca confía en la
    extensión sola: si pandas no logra leerlo como tabla (por ejemplo, alguien subió un PDF con
    extensión cambiada a .csv), lo rechaza con un mensaje claro en vez de romper el servidor."""
    nombre = archivo.filename or ""
    extension = os.path.splitext(nombre)[1].lower()
    if extension not in EXTENSIONES_PERMITIDAS_SUBIDA:
        raise ValueError(
            "Formato no soportado. Sube un archivo de datos en formato .csv o Excel (.xlsx), "
            "no un PDF, imagen u otro tipo de documento."
        )

    archivo.stream.seek(0, os.SEEK_END)
    tamano_mb = archivo.stream.tell() / (1024 * 1024)
    archivo.stream.seek(0)
    if tamano_mb > ds.LIMITE_MB_SUBIDA:
        raise ValueError(f"El archivo pesa {tamano_mb:.1f} MB; el máximo permitido es {ds.LIMITE_MB_SUBIDA} MB.")

    try:
        if extension == ".csv":
            # sep=None + engine="python": detecta sola si el separador es coma o punto y coma
            # (Excel en español exporta CSV con ";", muy común que alguien suba eso sin saberlo).
            df = pd.read_csv(archivo.stream, sep=None, engine="python")
        else:
            df = pd.read_excel(archivo.stream)
    except Exception:
        raise ValueError(
            "No se pudo leer el archivo como datos de tabla. Verificá que sea un CSV o Excel "
            "válido (no un PDF, imagen u otro tipo de archivo)."
        )

    _validar_tabla(df, minimo_columnas)
    return df, _nombre_visible(nombre)


def _nombre_visible(nombre_archivo: str) -> str:
    """Nombre del archivo tal como lo ve la persona (con espacios y tildes), sin la extensión
    ni caracteres que pudieran romper el HTML o el PDF. La carpeta en disco usa otro nombre seguro."""
    base = os.path.splitext(os.path.basename(nombre_archivo.replace("\\", "/")))[0]
    base = " ".join(re.sub(r"[<>&\"'`\x00-\x1f]", " ", base).split())
    return base[:80] or "Dataset subido"


def _validar_tabla(df, minimo_columnas: int):
    if df.shape[1] < minimo_columnas:
        raise ValueError(f"El archivo debe tener al menos {minimo_columnas} columnas para poder analizarlo.")
    if df.shape[0] == 0:
        raise ValueError("El archivo no tiene filas de datos.")
    if df.shape[0] > ds.LIMITE_FILAS_SUBIDA:
        raise ValueError(f"El archivo tiene {df.shape[0]} filas; el máximo permitido es {ds.LIMITE_FILAS_SUBIDA}.")


@app.route("/api/subir-dataset", methods=["POST"])
def api_subir_dataset():
    try:
        archivo = request.files.get("archivo")
        if not archivo or not archivo.filename:
            return _error("No se recibió ningún archivo.")

        df, nombre_archivo = _leer_archivo_subido(archivo)
        resultado = ds.analizar_archivo_subido(df, nombre_archivo)
        return jsonify({"ok": True, **resultado})
    except ValueError as exc:
        return _error(str(exc))
    except Exception as exc:
        return _error(f"No se pudo procesar el archivo: {exc}")


@app.route("/api/subir-dataset/confirmar", methods=["POST"])
def api_subir_dataset_confirmar():
    try:
        if ds.DATASET_SUBIDO["df"] is None:
            return _error("No hay ningún archivo subido todavía. Sube uno primero.")

        datos = request.get_json(silent=True) or {}
        objetivo = datos.get("objetivo")
        columnas_features = datos.get("columnas_features") or []

        if not objetivo:
            return _error("Elige cuál columna es el objetivo (lo que quieres predecir).")

        df = ds.DATASET_SUBIDO["df"]
        if objetivo not in df.columns:
            return _error(f'La columna objetivo "{objetivo}" no existe en el archivo.')

        columnas_features = [c for c in columnas_features if c in df.columns and c != objetivo]
        if not columnas_features:
            return _error("Elige al menos una columna (distinta del objetivo) para usar en la predicción.")

        df_final = df[columnas_features + [objetivo]].copy()
        if df_final[objetivo].notnull().sum() == 0:
            return _error(f'La columna objetivo "{objetivo}" está vacía.')
        problema = ml.detectar_tipo_problema(df_final[objetivo])

        nombre = ds.registrar_dataset_subido(df_final, objetivo, problema, ds.DATASET_SUBIDO["nombre_archivo"])
        ds.DATASET_SUBIDO.update({"df": None, "nombre_archivo": None})

        return jsonify({"ok": True, "dataset": nombre,
                        "redirect": url_for("seleccionar_dataset_pagina", nombre=nombre)})
    except Exception as exc:
        return _error(str(exc))


@app.route("/api/dataset/<nombre>/portada", methods=["POST"])
def api_portada(nombre):
    try:
        archivo = request.files.get("portada")
        if not archivo or not archivo.filename:
            return _error("No se recibió ninguna imagen.")
        aviso = ds.guardar_portada(nombre, archivo)
        # El informe PDF ya generado llevaba la portada anterior.
        with ds.BLOQUEO:
            ds.estado_de(nombre)["respuestas"].pop("pdf", None)
            ds.guardar_estado(nombre)
        meta = ds.obtener_metadata(nombre)
        return jsonify({"ok": True, "imagen_url": meta["imagen_url"], "ajuste": meta.get("portada_ajuste", "cubrir"), "aviso": aviso})
    except ValueError as exc:
        return _error(str(exc))
    except Exception as exc:
        return _error(f"No se pudo guardar la portada: {exc}")


@app.route("/api/dataset/<nombre>/color", methods=["POST"])
def api_color(nombre):
    try:
        color_a, color_b = ds.guardar_color(nombre, (request.get_json(silent=True) or {}).get("color"))
        # El informe PDF ya generado llevaba el color anterior.
        with ds.BLOQUEO:
            ds.estado_de(nombre)["respuestas"].pop("pdf", None)
            ds.guardar_estado(nombre)
        return jsonify({"ok": True, "color_a": color_a, "color_b": color_b})
    except ValueError as exc:
        return _error(str(exc))
    except Exception as exc:
        return _error(f"No se pudo guardar el color: {exc}")


# ============================================================
# ACTIVIDAD: pasos que siguen calculando aunque la persona cambie de página
# ============================================================
# El servidor termina cada paso aunque el navegador se vaya a otra página, y lo guarda en el
# análisis de su dataset. Aquí se anota qué está corriendo y qué terminó, para que cualquier
# página pueda avisar «terminó X» y el dashboard retome lo que estaba en curso.

_LOCK_ACTIVIDAD = threading.Lock()
ACTIVIDAD = {"secuencia": 0, "activos": {}, "terminados": deque(maxlen=30)}


def _registrar_inicio(nombre: str, accion: str) -> int:
    with _LOCK_ACTIVIDAD:
        ACTIVIDAD["secuencia"] += 1
        numero = ACTIVIDAD["secuencia"]
        ACTIVIDAD["activos"][numero] = {"id": numero, "dataset": nombre, "accion": accion}
        return numero


def _registrar_fin(numero: int, error: str = None) -> int:
    with _LOCK_ACTIVIDAD:
        proceso = ACTIVIDAD["activos"].pop(numero, None)
        ACTIVIDAD["secuencia"] += 1
        if proceso:
            ACTIVIDAD["terminados"].append({**proceso, "secuencia": ACTIVIDAD["secuencia"], "ok": error is None, "error": error})
        return ACTIVIDAD["secuencia"]


def _en_curso(nombre: str) -> list:
    with _LOCK_ACTIVIDAD:
        return [p["accion"] for p in ACTIVIDAD["activos"].values() if p["dataset"] == nombre]


@app.route("/api/actividad")
def api_actividad():
    with _LOCK_ACTIVIDAD:
        activos = [dict(p) for p in ACTIVIDAD["activos"].values()]
        terminados = [dict(t) for t in ACTIVIDAD["terminados"]]
        secuencia = ACTIVIDAD["secuencia"]
    for proceso in activos + terminados:
        proceso["nombre_dataset"] = ds.DATASETS.get(proceso["dataset"], {}).get("nombre", proceso["dataset"])
        proceso["url"] = url_for("seleccionar_dataset_pagina", nombre=proceso["dataset"])
    with _LOCK_ENTRENAMIENTO:
        for proceso in activos:
            if proceso["accion"] == "entrenar" and ENTRENAMIENTO["total"]:
                proceso["pct"] = round(ENTRENAMIENTO["hecho"] / ENTRENAMIENTO["total"] * 100)
    return jsonify({"ok": True, "secuencia": secuencia, "activos": activos, "terminados": terminados})


@app.route("/api/estado")
def api_estado():
    """Lo ya calculado para el dataset abierto, para mostrarlo sin recalcular al volver a la página."""
    try:
        nombre = ds.dataset_actual()
        return jsonify({"ok": True, "dataset": nombre, "respuestas": ds.estado_de(nombre)["respuestas"],
                        "en_curso": _en_curso(nombre)})
    except Exception as exc:
        return _error(str(exc))


@app.route("/api/reiniciar", methods=["POST"])
def api_reiniciar():
    """Borra todo lo calculado para el dataset abierto y deja el flujo como al principio."""
    try:
        nombre = ds.dataset_actual()
        if _en_curso(nombre):
            return _error("⚠ Espera a que termine el paso que se está calculando antes de reiniciar.")
        ds.reiniciar_analisis(nombre)
        if os.path.isfile(_ruta_pdf(nombre)):
            os.remove(_ruta_pdf(nombre))
        return jsonify({"ok": True})
    except Exception as exc:
        return _error(str(exc))


def _ejecutar_paso(accion: str, calcular):
    """Corre un paso sobre el dataset abierto: `calcular(nombre, meta, estado)` devuelve
    (respuesta, cambios). El cálculo va fuera del cerrojo general (se puede navegar mientras
    tanto) y el resultado se guarda en el análisis de ESE dataset, aunque ya se haya abierto otro."""
    try:
        with ds.BLOQUEO:
            nombre = ds.dataset_actual()
            estado = ds.estado_de(nombre)
            meta = ds.obtener_metadata(nombre)
    except Exception as exc:
        return _error(str(exc))

    numero = _registrar_inicio(nombre, accion)
    try:
        respuesta, cambios = calcular(nombre, meta, estado)
        respuesta = {"ok": True, **respuesta}
        with ds.BLOQUEO:
            estado = ds.estado_de(nombre)
            ds.guardar_respuesta(accion, respuesta, estado)
            estado.update(cambios)
            ds.guardar_estado(nombre)
        respuesta["secuencia"] = _registrar_fin(numero)
        return jsonify(respuesta)
    except PasoRechazado as exc:
        _registrar_fin(numero, str(exc))
        return _error(str(exc))
    except Exception as exc:
        _registrar_fin(numero, str(exc))
        return _error(str(exc))


class PasoRechazado(Exception):
    """Un paso que no se puede ejecutar todavía (falta un paso anterior, etc.)."""


def _entrenando_este_dataset(nombre: str) -> bool:
    with _LOCK_ENTRENAMIENTO:
        return ENTRENAMIENTO["activo"] and ENTRENAMIENTO["dataset"] == nombre


def _fuente_datos(estado) -> str:
    """Indica si el análisis corre sobre el dataset original o el ya preprocesado
    (normalizado/codificado), para que la interfaz lo aclare y no confunda al usuario."""
    return "preprocesado" if estado.get("df_procesado") is not None else "original"


# ============================================================
# API — EXPLORACIÓN Y PREPROCESAMIENTO
# ============================================================

@app.route("/api/explorar")
def api_explorar():
    def calcular(nombre, meta, estado):
        # Siempre el dataset original: describe el punto de partida del análisis.
        return pre.explorar_dataset(ds.cargar_dataset(nombre), objetivo=meta["objetivo"]), {}
    return _ejecutar_paso("explorar", calcular)


@app.route("/api/preprocesar")
def api_preprocesar():
    def calcular(nombre, meta, estado):
        df = ds.cargar_dataset(nombre)
        if meta["objetivo"] not in df.columns:
            raise PasoRechazado("⚠ No se puede preprocesar: no existe una variable objetivo válida en este dataset.")
        if _entrenando_este_dataset(nombre):
            raise PasoRechazado("⚠ Espera a que termine el entrenamiento en curso antes de volver a preprocesar.")
        resultado = pre.preprocesar(df, objetivo=meta["objetivo"])
        cambios = {
            "df_procesado": resultado["df"], "transformaciones": resultado["transformaciones"],
            "mapeo_objetivo": resultado["mapeo_objetivo"], "info_columnas_originales": resultado["info_columnas_originales"],
        }
        return {k: v for k, v in resultado.items() if k != "df"}, cambios
    return _ejecutar_paso("preprocesar", calcular)


# ============================================================
# API — ÁLGEBRA LINEAL Y ESTADÍSTICA
# ============================================================

@app.route("/api/algebra")
def api_algebra():
    def calcular(nombre, meta, estado):
        resultado = algebra_srv.ejecutar_algebra_lineal()
        return resultado, {"algebra": resultado}
    return _ejecutar_paso("algebra", calcular)


@app.route("/api/estadistica")
def api_estadistica():
    def calcular(nombre, meta, estado):
        resultado = stats.calcular_estadisticas(ds.df_de(estado))
        resultado["fuente_datos"] = _fuente_datos(estado)
        return resultado, {"estadistica": resultado}
    return _ejecutar_paso("estadistica", calcular)


@app.route("/api/outliers")
def api_outliers():
    def calcular(nombre, meta, estado):
        df = ds.df_de(estado)
        resultado = stats.detectar_outliers(df)
        resultado["fuente_datos"] = _fuente_datos(estado)
        with viz.BLOQUEO:
            boxplots = viz.generar_boxplots(df, dataset=nombre, objetivo=meta["objetivo"])
        resultado["boxplots_url"] = boxplots["url"]
        resultado["boxplots_explicacion"] = boxplots["explicacion"]
        return resultado, {"outliers": resultado}
    return _ejecutar_paso("outliers", calcular)


# ============================================================
# API — GRÁFICOS
# ============================================================

@app.route("/api/graficos")
def api_graficos():
    def calcular(nombre, meta, estado):
        with viz.BLOQUEO:
            resultado = viz.generar_graficos(
                ds.df_de(estado), dataset=nombre, objetivo=meta["objetivo"], mapeo_objetivo=estado.get("mapeo_objetivo")
            )
        resultado["fuente_datos"] = _fuente_datos(estado)
        return resultado, {"graficos": resultado}
    return _ejecutar_paso("graficos", calcular)


# ============================================================
# API — MACHINE LEARNING
# ============================================================

# El entrenamiento (búsqueda de hiperparámetros) corre en un hilo aparte para que la
# interfaz pueda seguir preguntando "¿cuánto falta?" mientras tanto. Es una app de un solo
# usuario local: se entrena un dataset a la vez, y el resultado se guarda en el análisis de
# ESE dataset aunque la persona haya abierto otro mientras tanto.
ENTRENAMIENTO = {"activo": False, "dataset": None, "hecho": 0, "total": 0, "listo": False,
                 "resultado": None, "error": None, "proceso": None}
_LOCK_ENTRENAMIENTO = threading.Lock()


def _entrenar_en_segundo_plano(nombre: str, meta: dict, datos: dict, info_columnas: list, numero: int):
    def _reportar_progreso(hecho, total):
        with _LOCK_ENTRENAMIENTO:
            ENTRENAMIENTO["hecho"] = hecho
            ENTRENAMIENTO["total"] = total

    try:
        resultado = ml.entrenar(datos, objetivo=meta["objetivo"], on_progreso=_reportar_progreso)
        mejor_nombre = resultado["mejor_modelo_nombre"]
        metricas_mejor = resultado["comparacion"][mejor_nombre]

        with viz.BLOQUEO:
            comparacion_chart = viz.generar_comparacion_modelos_chart(
                resultado["comparacion"], resultado["problema"], dataset=nombre
            )
            importancia = viz.generar_importancia_variables(
                resultado["mejor_modelo"].named_steps["modelo"], resultado["columnas_features"], dataset=nombre
            )

        payload = {
            "ok": True, "problema": resultado["problema"],
            "mejor_modelo": mejor_nombre,
            "modelos_disponibles": list(resultado["comparacion"].keys()),
            "comparacion": resultado["comparacion"],
            "parametros": resultado["parametros"],
            "particiones": resultado["particiones"],
            "columnas_features": resultado["columnas_features"],
            "filas_entrenamiento": int(resultado["X_train"].shape[0]),
            "filas_prueba": int(resultado["X_test"].shape[0]),
            "comparacion_chart_url": comparacion_chart["url"],
            "comparacion_chart_explicacion": comparacion_chart["explicacion"],
            "importancia_url": importancia["url"],
            "importancia_explicacion": importancia["explicacion"],
            "importancia_disponible": importancia["disponible"],
            "info_columnas_originales": info_columnas,
            "objetivo": str(meta["objetivo"]),
        }

        with ds.BLOQUEO:
            estado = ds.estado_de(nombre)
            ds.guardar_respuesta("entrenar", payload, estado)
            estado.update({
                "problema": resultado["problema"],
                "X_train": resultado["X_train"], "X_test": resultado["X_test"],
                "y_train": resultado["y_train"], "y_test": resultado["y_test"],
                "modelo": resultado["mejor_modelo"], "nombre_modelo": mejor_nombre,
                "modelos_entrenados": resultado["modelos_entrenados"],
                "predicciones_por_modelo": resultado["y_pred_por_modelo"],
                "y_pred": resultado["y_pred"], "comparacion_modelos": resultado["comparacion"],
                "columnas_features": resultado["columnas_features"],
                "parametros_modelos": resultado["parametros"],
                "particiones": resultado["particiones"],
                "mapeo_objetivo": datos["mapeo_objetivo"],
                "metricas": metricas_mejor,
                "comparacion_chart_url": comparacion_chart["url"],
                "comparacion_chart_explicacion": comparacion_chart["explicacion"],
                "importancia_url": importancia["url"],
                "importancia_explicacion": importancia["explicacion"],
                "importancia_disponible": importancia["disponible"],
            })
            ds.guardar_estado(nombre)

        _guardar_en_historial({
            "dataset": meta["nombre"], "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "modelo": mejor_nombre, "problema": resultado["problema"],
            "metrica_principal": (
                f"Accuracy {metricas_mejor['accuracy']*100:.2f}%" if resultado["problema"] == "clasificacion"
                else f"R² {metricas_mejor['r2']:.3f}"
            ),
            "estado": "Completado",
        })

        payload["secuencia"] = _registrar_fin(numero)
        with _LOCK_ENTRENAMIENTO:
            ENTRENAMIENTO.update({"resultado": payload, "listo": True, "activo": False})
    except Exception as exc:
        _registrar_fin(numero, str(exc))
        with _LOCK_ENTRENAMIENTO:
            ENTRENAMIENTO.update({"error": str(exc), "listo": True, "activo": False})


@app.route("/api/entrenar/iniciar")
def api_entrenar_iniciar():
    try:
        with ds.BLOQUEO, _LOCK_ENTRENAMIENTO:
            nombre = ds.dataset_actual()
            if ENTRENAMIENTO["activo"]:
                if ENTRENAMIENTO["dataset"] == nombre:
                    return jsonify({"ok": True, "iniciado": False, "en_curso": True})
                otro = ds.obtener_metadata(ENTRENAMIENTO["dataset"])["nombre"]
                return _error(f'⚠ Se está entrenando el dataset "{otro}". Espera a que termine para entrenar este.')

            meta = ds.obtener_metadata(nombre)
            estado = ds.estado_de(nombre)
            if estado["df_procesado"] is None:
                return _error('⚠ Preprocesa el dataset antes de entrenar el modelo (botón "Preprocesar").')
            if "preprocesar" in _en_curso(nombre):
                return _error("⚠ Espera a que termine el preprocesamiento.")
            df = ds.cargar_dataset(nombre)
            if meta["objetivo"] not in df.columns:
                return _error("⚠ No se puede entrenar el modelo porque no existe una variable objetivo.")

            datos = pre.preparar_para_modelo(df, meta["objetivo"])
            info_columnas = estado["info_columnas_originales"]
            numero = _registrar_inicio(nombre, "entrenar")
            ENTRENAMIENTO.update({
                "activo": True, "dataset": nombre, "hecho": 0, "total": 0,
                "listo": False, "resultado": None, "error": None, "proceso": numero,
            })

        hilo = threading.Thread(
            target=_entrenar_en_segundo_plano, args=(nombre, meta, datos, info_columnas, numero), daemon=True
        )
        hilo.start()
        return jsonify({"ok": True, "iniciado": True})
    except Exception as exc:
        return _error(str(exc))


@app.route("/api/entrenar/progreso")
def api_entrenar_progreso():
    with _LOCK_ENTRENAMIENTO:
        copia = dict(ENTRENAMIENTO)

    pct = round((copia["hecho"] / copia["total"]) * 100, 1) if copia["total"] else 0.0
    if copia["error"]:
        return _error(copia["error"])

    respuesta = {"ok": True, "dataset": copia["dataset"], "hecho": copia["hecho"], "total": copia["total"],
                 "pct": pct, "listo": copia["listo"]}
    if copia["listo"] and copia["resultado"]:
        respuesta.update(copia["resultado"])
    return jsonify(respuesta)


def _modelo_pedido(estado, nombre_pedido):
    modelos_entrenados = estado.get("modelos_entrenados") or {}
    nombre_modelo = nombre_pedido or estado["nombre_modelo"]
    if nombre_modelo not in modelos_entrenados:
        nombre_modelo = estado["nombre_modelo"]
    return nombre_modelo, modelos_entrenados[nombre_modelo]


def _etiqueta(valor, mapeo):
    return mapeo.get(int(valor), str(valor)) if mapeo else str(valor)


def _evaluacion(nombre, estado, nombre_modelo):
    problema = estado["problema"]
    y_test = estado["y_test"]
    y_pred = estado["predicciones_por_modelo"][nombre_modelo]
    mapeo = estado.get("mapeo_objetivo")

    respuesta = {
        "problema": problema, "metricas": estado["comparacion_modelos"][nombre_modelo],
        "modelo": nombre_modelo, "es_mejor_modelo": nombre_modelo == estado["nombre_modelo"],
        "modelos_disponibles": list(estado["modelos_entrenados"].keys()), "mejor_modelo": estado["nombre_modelo"],
    }
    with viz.BLOQUEO:
        if problema == "clasificacion":
            clases = sorted(mapeo) if mapeo else sorted(set(pd.Series(y_test).tolist()) | set(pd.Series(y_pred).tolist()))
            respuesta["matriz_confusion_url"] = viz.generar_matriz_confusion(
                y_test, y_pred, clases, [_etiqueta(c, mapeo) for c in clases], dataset=nombre, modelo=nombre_modelo
            )
        else:
            respuesta["real_vs_prediccion_url"] = viz.generar_comparacion_regresion(
                y_test.to_numpy(), y_pred, dataset=nombre, modelo=nombre_modelo
            )
    respuesta["predicciones"] = ml.tabla_predicciones(y_test, y_pred, problema, mapeo_objetivo=mapeo)
    return respuesta


@app.route("/api/evaluar")
def api_evaluar():
    """Sin parámetros evalúa el mejor modelo (el paso "Evaluar", que se guarda y va al PDF). El
    menú de la interfaz puede pedir cualquier otro con ?modelo=...: eso solo se muestra."""
    pedido = request.args.get("modelo")
    try:
        with ds.BLOQUEO:
            estado = ds.estado_de(ds.dataset_actual())
            if estado["modelo"] is None:
                return _error('⚠ Entrena un modelo antes de evaluarlo (botón "Entrenar Modelo").')
            if pedido and pedido != estado["nombre_modelo"]:
                nombre_modelo, _ = _modelo_pedido(estado, pedido)
                return jsonify({"ok": True, **_evaluacion(estado["dataset"], estado, nombre_modelo)})
    except Exception as exc:
        return _error(str(exc))

    def calcular(nombre, meta, estado):
        if estado["modelo"] is None:
            raise PasoRechazado('⚠ Entrena un modelo antes de evaluarlo (botón "Entrenar Modelo").')
        respuesta = _evaluacion(nombre, estado, estado["nombre_modelo"])
        pd.DataFrame(respuesta["predicciones"]).to_csv(os.path.join(RESULTADOS_DIR, "predicciones.csv"), index=False)
        return respuesta, {
            "predicciones": respuesta["predicciones"],
            "matriz_confusion_url": respuesta.get("matriz_confusion_url"),
            "real_vs_prediccion_url": respuesta.get("real_vs_prediccion_url"),
        }
    return _ejecutar_paso("evaluar", calcular)


def _formatear_prediccion(cruda, problema, mapeo):
    if problema == "clasificacion":
        return _etiqueta(cruda, mapeo)
    return round(float(cruda), 3)


@app.route("/api/predecir", methods=["POST"])
def api_predecir():
    """Predice un caso nuevo cargado a mano (no del dataset) con el modelo ya entrenado: su
    Pipeline prepara el caso exactamente como aprendió, sin reentrenar nada."""
    try:
        with ds.BLOQUEO:
            nombre = ds.dataset_actual()
            estado = ds.estado_de(nombre)
            if estado.get("modelo") is None:
                return _error('⚠ Entrena un modelo antes de predecir un caso nuevo.')

            datos = request.get_json(silent=True) or {}
            nombre_modelo, modelo = _modelo_pedido(estado, datos.get("modelo"))
            try:
                fila = pre.caso_a_dataframe(datos.get("valores") or {}, estado["info_columnas_originales"])
            except ValueError as exc:
                return _error(str(exc))

            problema = estado["problema"]
            mapeo = estado.get("mapeo_objetivo")
            respuesta = {
                "ok": True, "problema": problema, "modelo": nombre_modelo,
                "objetivo": ds.obtener_metadata(nombre)["objetivo"],
                "prediccion": _formatear_prediccion(modelo.predict(fila)[0], problema, mapeo),
            }
            if problema == "clasificacion" and hasattr(modelo, "predict_proba"):
                proba = modelo.predict_proba(fila)[0]
                respuesta["probabilidades"] = {_etiqueta(c, mapeo): float(p) for c, p in zip(modelo.classes_, proba)}
            return jsonify(respuesta)
    except Exception as exc:
        return _error(str(exc))


@app.route("/api/predecir-lote", methods=["POST"])
def api_predecir_lote():
    """Predice todos los casos de un archivo subido (p. ej. 30 casos nuevos) con el modelo ya
    entrenado, sin reentrenar."""
    try:
        with ds.BLOQUEO:
            nombre = ds.dataset_actual()
            estado = ds.estado_de(nombre)
            if estado.get("modelo") is None:
                return _error('⚠ Entrena un modelo antes de predecir.')

            archivo = request.files.get("archivo")
            if archivo is None or not archivo.filename:
                return _error("Sube un archivo CSV o Excel con los casos nuevos.")
            df, _ = _leer_archivo_subido(archivo, minimo_columnas=1)
            df.columns = [str(c) for c in df.columns]

            nombre_modelo, modelo = _modelo_pedido(estado, request.form.get("modelo"))
            problema = estado["problema"]
            mapeo = estado.get("mapeo_objetivo")

            casos = []
            for i, registro in enumerate(df.to_dict(orient="records"), start=1):
                try:
                    casos.append(pre.caso_a_dataframe(registro, estado["info_columnas_originales"]))
                except ValueError as exc:
                    return _error(f"Fila {i}: {exc}")
            crudas = modelo.predict(pd.concat(casos, ignore_index=True))
            filas = [{"fila": i, "prediccion": _formatear_prediccion(c, problema, mapeo)} for i, c in enumerate(crudas, start=1)]

            pd.concat([df.reset_index(drop=True), pd.DataFrame(filas).drop(columns="fila")], axis=1).to_csv(
                os.path.join(RESULTADOS_DIR, "predicciones_lote.csv"), index=False
            )
            return jsonify({
                "ok": True, "problema": problema, "modelo": nombre_modelo,
                "objetivo": ds.obtener_metadata(nombre)["objetivo"], "total": len(filas), "filas": filas,
            })
    except ValueError as exc:
        return _error(str(exc))
    except Exception as exc:
        return _error(str(exc))


# ============================================================
# API — RESUMEN Y HISTORIAL
# ============================================================

@app.route("/api/resumen")
def api_resumen():
    try:
        with ds.BLOQUEO:
            nombre = ds.dataset_actual()
            meta = ds.obtener_metadata(nombre)
            estado = ds.estado_de(nombre)
            df = ds.cargar_dataset(nombre)
            outliers_total = None
            if estado.get("outliers"):
                outliers_total = sum(c["cantidad_outliers"] for c in estado["outliers"]["columnas"])

            return jsonify({
                "ok": True,
                "dataset": meta["nombre"],
                "registros": int(df.shape[0]),
                "variables": int(df.shape[1]),
                "nulos": int(df.isnull().sum().sum()),
                "outliers": outliers_total,
                "modelo": estado.get("nombre_modelo"),
                "metricas": estado.get("metricas"),
                "problema": estado.get("problema"),
            })
    except Exception as exc:
        return _error(str(exc))


@app.route("/api/historial")
def api_historial():
    return jsonify({"ok": True, "historial": _cargar_historial()})


# ============================================================
# PDF
# ============================================================

def _resumen_basico(df):
    info = pre.explorar_dataset(df)
    return {"filas": info["filas"], "columnas": info["columnas"], "nulos": info["total_nulos"], "duplicados": info["duplicados"]}


_LOCK_PDF = threading.Lock()


@app.route("/generar-pdf")
def generar_pdf():
    def calcular(nombre, meta, estado):
        original = ds.cargar_dataset(nombre)
        resultado = {
            "dataset_meta": meta,
            # Siempre el dataset ORIGINAL (nunca el ya preprocesado): esta sección describe el
            # punto de partida del análisis, y debe coincidir con la columna "Antes" de la
            # sección de Preprocesamiento, sin importar si ya se preprocesó antes de pedir el PDF.
            "exploracion": pre.explorar_dataset(original, objetivo=meta["objetivo"]),
            "preprocesamiento": None,
            "algebra": estado.get("algebra"),
            "estadistica": estado.get("estadistica"),
            "outliers": estado.get("outliers"),
            "graficos": estado.get("graficos"),
            "entrenamiento": None,
            "comparacion": estado.get("comparacion_modelos"),
            "parametros_modelos": estado.get("parametros_modelos"),
            "metrica_principal": estado.get("metricas"),
            "matriz_confusion_url": estado.get("matriz_confusion_url"),
            "real_vs_prediccion_url": estado.get("real_vs_prediccion_url"),
            "predicciones": estado.get("predicciones"),
            "comparacion_chart_url": estado.get("comparacion_chart_url"),
            "comparacion_chart_explicacion": estado.get("comparacion_chart_explicacion"),
            "importancia_url": estado.get("importancia_url"),
            "importancia_explicacion": estado.get("importancia_explicacion"),
            "importancia_disponible": estado.get("importancia_disponible"),
            "filas_prueba": int(estado["X_test"].shape[0]) if estado.get("X_test") is not None else None,
        }
        if estado.get("df_procesado") is not None:
            resultado["preprocesamiento"] = {
                "antes": _resumen_basico(original),
                "despues": _resumen_basico(estado["df_procesado"]),
                "transformaciones": estado.get("transformaciones") or [],
            }
        if estado.get("modelo") is not None:
            resultado["entrenamiento"] = {
                "problema": estado["problema"],
                "mejor_modelo_nombre": estado["nombre_modelo"],
                "particiones": estado.get("particiones"),
            }

        ruta_pdf = _ruta_pdf(nombre)
        # El tema de colores del PDF es global dentro de pdf_service: un informe a la vez.
        with _LOCK_PDF:
            pdf_srv.generar_pdf(resultado, ruta_pdf)
        marca = int(os.path.getmtime(ruta_pdf))
        return {
            "mensaje": "✅ Informe PDF generado correctamente",
            "ver_url": url_for("ver_pdf", nombre=nombre, v=marca),
            "descargar_url": url_for("descargar_pdf", nombre=nombre, v=marca),
        }, {}
    return _ejecutar_paso("pdf", calcular)


def _enviar_pdf(nombre: str, descargar: bool):
    if nombre not in ds.DATASETS:
        return _error("Ese dataset no existe.", 404)
    ruta_pdf = _ruta_pdf(nombre)
    if not os.path.isfile(ruta_pdf):
        return _error("Todavía no se ha generado el informe de este dataset.", 404)
    nombre_descarga = f"DataExpert_IA_{secure_filename(ds.DATASETS[nombre]['nombre']) or nombre}.pdf"
    respuesta = send_file(ruta_pdf, mimetype="application/pdf", as_attachment=descargar,
                          download_name=nombre_descarga, max_age=0)
    # Cada informe tiene su propia dirección y no se guarda en caché: así el navegador nunca
    # muestra el PDF de otro dataset ni una versión anterior.
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


@app.route("/ver-pdf/<nombre>")
def ver_pdf(nombre):
    return _enviar_pdf(nombre, descargar=False)


@app.route("/descargar-pdf/<nombre>")
def descargar_pdf(nombre):
    return _enviar_pdf(nombre, descargar=True)


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5050))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"\n🚀 DataExpert IA corriendo en http://{host}:{port}\n")
    app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)
