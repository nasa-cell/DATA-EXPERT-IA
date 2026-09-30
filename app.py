"""DataExpert IA — Plataforma de análisis matemático, estadístico y de Machine Learning.

Servidor Flask: cada botón del dashboard llama a un endpoint que ejecuta un cálculo real
(Pandas, NumPy, Scikit-learn, Matplotlib/Seaborn o ReportLab) sobre el dataset actualmente
seleccionado, sin resultados simulados ni escritos a mano.
"""

import os
import sys
import io
import json
import threading
from datetime import datetime

# Fuerza salida UTF-8 para que los emoji de los mensajes no rompan la consola de Windows
# (por defecto usa el codepage cp1252, que no incluye esos caracteres).
if sys.stdout is not None and sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr is not None and sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import pandas as pd
from flask import Flask, render_template, jsonify, request, send_file, send_from_directory, url_for
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

BASE_DIR = str(cfg.CODIGO)
INFORMES_DIR = str(cfg.INFORMES_DIR)
RESULTADOS_DIR = str(cfg.RESULTADOS_DIR)
HISTORIAL_PATH = str(cfg.HISTORIAL_PATH)

cfg.preparar_carpetas()

app = Flask(__name__, template_folder=str(cfg.CODIGO / "templates"), static_folder=str(cfg.CODIGO / "static"))


@app.route("/api/salud")
def api_salud():
    """Lo usa el lanzador de Windows para saber si ya hay una copia abierta."""
    return jsonify({"ok": True, "aplicacion": "dataexpert_ia"})


@app.route("/graficos-generados/<path:ruta>")
def graficos_generados(ruta):
    """Gráficos que genera el análisis; en la versión instalada viven en la carpeta de datos, fuera del código."""
    return send_from_directory(str(cfg.GRAFICOS_DIR), ruta)


@app.context_processor
def inyectar_menu_de_datasets():
    """La lista «Datasets» de la barra superior aparece en todas las páginas."""
    return {"menu_datasets": [d for d in ds.listar_datasets() if d["id"] != "subido"]}


def _error(mensaje: str, codigo: int = 400):
    return jsonify({"ok": False, "error": mensaje}), codigo


def _cargar_historial():
    if os.path.isfile(HISTORIAL_PATH):
        try:
            with open(HISTORIAL_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _guardar_en_historial(entrada: dict):
    historial = _cargar_historial()
    historial.insert(0, entrada)
    with open(HISTORIAL_PATH, "w", encoding="utf-8") as f:
        json.dump(historial[:25], f, ensure_ascii=False, indent=2)


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
    except ValueError:
        return render_template("index.html", datasets=ds.listar_datasets(),
                                error=f'El dataset "{nombre}" no existe.')

    ds.seleccionar_dataset(nombre)
    return render_template("dashboard.html", meta={"id": nombre, **meta})


@app.route("/subir")
def subir_pagina():
    return render_template("subir.html")


# ============================================================
# API — SUBIDA DE DATASET PROPIO (CSV / Excel)
# ============================================================

EXTENSIONES_PERMITIDAS_SUBIDA = {".csv", ".xlsx", ".xls"}


def _leer_archivo_subido(archivo):
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

    _validar_tabla(df)
    nombre_seguro = secure_filename(nombre) or "dataset_subido"
    return df, nombre_seguro


def _validar_tabla(df):
    if df.shape[1] < 2:
        raise ValueError("El archivo debe tener al menos 2 columnas para poder analizarlo.")
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
        problema = ml.detectar_tipo_problema(df_final[objetivo])

        ds.registrar_dataset_subido(df_final, objetivo, problema, ds.DATASET_SUBIDO["nombre_archivo"])
        ds.seleccionar_dataset("subido")

        return jsonify({"ok": True, "redirect": url_for("seleccionar_dataset_pagina", nombre="subido")})
    except Exception as exc:
        return _error(str(exc))


# ============================================================
# API — EXPLORACIÓN Y PREPROCESAMIENTO
# ============================================================

@app.route("/api/explorar")
def api_explorar():
    try:
        nombre = ds.dataset_actual()
        meta = ds.obtener_metadata(nombre)
        df = ds.df_actual()
        resultado = pre.explorar_dataset(df, objetivo=meta["objetivo"])
        return jsonify({"ok": True, **resultado})
    except Exception as exc:
        return _error(str(exc))


@app.route("/api/preprocesar")
def api_preprocesar():
    try:
        nombre = ds.dataset_actual()
        meta = ds.obtener_metadata(nombre)
        df = ds.cargar_dataset(nombre)

        if meta["objetivo"] not in df.columns:
            return _error("⚠ No se puede preprocesar: no existe una variable objetivo válida en este dataset.")

        resultado = pre.preprocesar(df, objetivo=meta["objetivo"])
        ds.ESTADO["df_procesado"] = resultado["df"]
        ds.ESTADO["transformaciones"] = resultado["transformaciones"]
        ds.ESTADO["mapeo_objetivo"] = resultado["mapeo_objetivo"]
        # Objetos ya ajustados (encoders, scaler): quedan en memoria para poder transformar un
        # caso nuevo más tarde (ver /api/predecir), nunca se mandan al navegador como JSON.
        ds.ESTADO["transformadores"] = resultado["transformadores"]
        ds.ESTADO["info_columnas_originales"] = resultado["info_columnas_originales"]

        respuesta = {k: v for k, v in resultado.items() if k not in ("df", "transformadores")}
        return jsonify({"ok": True, **respuesta})
    except Exception as exc:
        return _error(str(exc))


# ============================================================
# API — ÁLGEBRA LINEAL Y ESTADÍSTICA
# ============================================================

@app.route("/api/algebra")
def api_algebra():
    try:
        resultado = algebra_srv.ejecutar_algebra_lineal()
        ds.ESTADO["algebra"] = resultado
        return jsonify({"ok": True, **resultado})
    except Exception as exc:
        return _error(str(exc))


def _fuente_datos() -> str:
    """Indica si el análisis actual corre sobre el dataset original o el ya preprocesado
    (normalizado/codificado), para que la interfaz lo aclare y no confunda al usuario."""
    return "preprocesado" if ds.ESTADO.get("df_procesado") is not None else "original"


@app.route("/api/estadistica")
def api_estadistica():
    try:
        df = ds.df_actual()
        resultado = stats.calcular_estadisticas(df)
        resultado["fuente_datos"] = _fuente_datos()
        ds.ESTADO["estadistica"] = resultado
        return jsonify({"ok": True, **resultado})
    except Exception as exc:
        return _error(str(exc))


@app.route("/api/outliers")
def api_outliers():
    try:
        nombre = ds.dataset_actual()
        meta = ds.obtener_metadata(nombre)
        df = ds.df_actual()
        resultado = stats.detectar_outliers(df)
        resultado["fuente_datos"] = _fuente_datos()

        boxplots = viz.generar_boxplots(df, dataset=nombre, objetivo=meta["objetivo"])
        resultado["boxplots_url"] = boxplots["url"]
        resultado["boxplots_explicacion"] = boxplots["explicacion"]

        ds.ESTADO["outliers"] = resultado
        return jsonify({"ok": True, **resultado})
    except Exception as exc:
        return _error(str(exc))


# ============================================================
# API — GRÁFICOS
# ============================================================

@app.route("/api/graficos")
def api_graficos():
    try:
        nombre = ds.dataset_actual()
        meta = ds.obtener_metadata(nombre)
        df = ds.df_actual()
        resultado = viz.generar_graficos(
            df, dataset=nombre, objetivo=meta["objetivo"], mapeo_objetivo=ds.ESTADO.get("mapeo_objetivo")
        )
        resultado["fuente_datos"] = _fuente_datos()
        ds.ESTADO["graficos"] = resultado
        return jsonify({"ok": True, **resultado})
    except Exception as exc:
        return _error(str(exc))


# ============================================================
# API — MACHINE LEARNING
# ============================================================

# El entrenamiento (búsqueda de hiperparámetros) corre en un hilo aparte para que la
# interfaz pueda seguir preguntando "¿cuánto falta?" mientras tanto. Al ser una app de un
# solo usuario local, un único diccionario global alcanza (no hace falta manejar varias
# sesiones ni una cola de trabajos).
ENTRENAMIENTO = {"activo": False, "hecho": 0, "total": 0, "listo": False, "resultado": None, "error": None}
_LOCK_ENTRENAMIENTO = threading.Lock()


def _entrenar_en_segundo_plano(nombre: str, meta: dict, df):
    def _reportar_progreso(hecho, total):
        ENTRENAMIENTO["hecho"] = hecho
        ENTRENAMIENTO["total"] = total

    try:
        resultado = ml.entrenar(df, objetivo=meta["objetivo"], on_progreso=_reportar_progreso)

        ds.ESTADO.update({
            "problema": resultado["problema"],
            "X_train": resultado["X_train"], "X_test": resultado["X_test"],
            "y_train": resultado["y_train"], "y_test": resultado["y_test"],
            "modelo": resultado["mejor_modelo"], "nombre_modelo": resultado["mejor_modelo_nombre"],
            "modelos_entrenados": resultado["modelos_entrenados"],
            "predicciones_por_modelo": resultado["y_pred_por_modelo"],
            "y_pred": resultado["y_pred"], "comparacion_modelos": resultado["comparacion"],
            "columnas_features": resultado["columnas_features"],
        })
        ds.ESTADO["parametros_modelos"] = resultado["parametros"]

        metricas_mejor = resultado["comparacion"][resultado["mejor_modelo_nombre"]]
        ds.ESTADO["metricas"] = metricas_mejor

        comparacion_chart = viz.generar_comparacion_modelos_chart(
            resultado["comparacion"], resultado["problema"], dataset=nombre
        )
        importancia = viz.generar_importancia_variables(
            resultado["mejor_modelo"], resultado["columnas_features"], dataset=nombre
        )
        ds.ESTADO["comparacion_chart_url"] = comparacion_chart["url"]
        ds.ESTADO["comparacion_chart_explicacion"] = comparacion_chart["explicacion"]
        ds.ESTADO["importancia_url"] = importancia["url"]
        ds.ESTADO["importancia_explicacion"] = importancia["explicacion"]
        ds.ESTADO["importancia_disponible"] = importancia["disponible"]

        _guardar_en_historial({
            "dataset": meta["nombre"], "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "modelo": resultado["mejor_modelo_nombre"], "problema": resultado["problema"],
            "metrica_principal": (
                f"Accuracy {metricas_mejor['accuracy']*100:.2f}%" if resultado["problema"] == "clasificacion"
                else f"R² {metricas_mejor['r2']:.3f}"
            ),
            "estado": "Completado",
        })

        payload = {
            "ok": True, "problema": resultado["problema"],
            "mejor_modelo": resultado["mejor_modelo_nombre"],
            "modelos_disponibles": list(resultado["comparacion"].keys()),
            "comparacion": resultado["comparacion"],
            "parametros": resultado["parametros"],
            "columnas_features": resultado["columnas_features"],
            "filas_entrenamiento": int(resultado["X_train"].shape[0]),
            "filas_prueba": int(resultado["X_test"].shape[0]),
            "comparacion_chart_url": comparacion_chart["url"],
            "comparacion_chart_explicacion": comparacion_chart["explicacion"],
            "importancia_url": importancia["url"],
            "importancia_explicacion": importancia["explicacion"],
            "importancia_disponible": importancia["disponible"],
            "info_columnas_originales": ds.ESTADO.get("info_columnas_originales"),
            "objetivo": str(meta["objetivo"]),
        }
        with _LOCK_ENTRENAMIENTO:
            ENTRENAMIENTO["resultado"] = payload
            ENTRENAMIENTO["listo"] = True
            ENTRENAMIENTO["activo"] = False
    except Exception as exc:
        with _LOCK_ENTRENAMIENTO:
            ENTRENAMIENTO["error"] = str(exc)
            ENTRENAMIENTO["listo"] = True
            ENTRENAMIENTO["activo"] = False


@app.route("/api/entrenar/iniciar")
def api_entrenar_iniciar():
    try:
        with _LOCK_ENTRENAMIENTO:
            if ENTRENAMIENTO["activo"]:
                return _error("⚠ Ya hay un entrenamiento en curso para este dataset.")

            nombre = ds.dataset_actual()
            meta = ds.obtener_metadata(nombre)
            df = ds.ESTADO["df_procesado"]
            if df is None:
                return _error('⚠ Preprocesa el dataset antes de entrenar el modelo (botón "Preprocesar").')
            if meta["objetivo"] not in df.columns:
                return _error("⚠ No se puede entrenar el modelo porque no existe una variable objetivo.")

            problema = ml.detectar_tipo_problema(df[meta["objetivo"]])
            total = ml.calcular_total_pasos(problema)

            ENTRENAMIENTO.update({
                "activo": True, "hecho": 0, "total": total,
                "listo": False, "resultado": None, "error": None,
            })

        hilo = threading.Thread(
            target=_entrenar_en_segundo_plano, args=(nombre, meta, df), daemon=True
        )
        hilo.start()

        return jsonify({"ok": True, "iniciado": True, "total": total})
    except Exception as exc:
        return _error(str(exc))


@app.route("/api/entrenar/progreso")
def api_entrenar_progreso():
    with _LOCK_ENTRENAMIENTO:
        hecho, total = ENTRENAMIENTO["hecho"], ENTRENAMIENTO["total"]
        listo, error, resultado = ENTRENAMIENTO["listo"], ENTRENAMIENTO["error"], ENTRENAMIENTO["resultado"]

    pct = round((hecho / total) * 100, 1) if total else 0.0
    if error:
        return _error(error)

    respuesta = {"ok": True, "hecho": hecho, "total": total, "pct": pct, "listo": listo}
    if listo and resultado:
        respuesta.update(resultado)
    return jsonify(respuesta)


@app.route("/api/evaluar")
def api_evaluar():
    try:
        if ds.ESTADO["modelo"] is None:
            return _error('⚠ Entrena un modelo antes de evaluarlo (botón "Entrenar Modelo").')

        nombre = ds.dataset_actual()
        problema = ds.ESTADO["problema"]

        # Por defecto se evalúa el mejor modelo, pero el menú de la interfaz permite pedir
        # cualquiera de los modelos entrenados por su nombre (?modelo=Random Forest, etc.).
        modelos_entrenados = ds.ESTADO.get("modelos_entrenados") or {}
        nombre_modelo = request.args.get("modelo") or ds.ESTADO["nombre_modelo"]
        if nombre_modelo not in modelos_entrenados:
            nombre_modelo = ds.ESTADO["nombre_modelo"]

        y_test = ds.ESTADO["y_test"]
        y_pred = ds.ESTADO["predicciones_por_modelo"][nombre_modelo]
        metricas = ds.ESTADO["comparacion_modelos"][nombre_modelo]

        respuesta = {
            "ok": True, "problema": problema, "metricas": metricas,
            "modelo": nombre_modelo, "es_mejor_modelo": nombre_modelo == ds.ESTADO["nombre_modelo"],
            "modelos_disponibles": list(modelos_entrenados.keys()), "mejor_modelo": ds.ESTADO["nombre_modelo"],
        }

        if problema == "clasificacion":
            mapeo = ds.ESTADO.get("mapeo_objetivo")
            etiquetas = [mapeo[i] for i in sorted(mapeo)] if mapeo else sorted(set(y_test) | set(y_pred))
            url_matriz = viz.generar_matriz_confusion(y_test, y_pred, etiquetas, dataset=nombre)
            respuesta["matriz_confusion_url"] = url_matriz
        else:
            url_comparacion = viz.generar_comparacion_regresion(y_test.to_numpy(), y_pred, dataset=nombre)
            respuesta["real_vs_prediccion_url"] = url_comparacion

        predicciones = ml.tabla_predicciones(
            y_test, y_pred, problema, mapeo_objetivo=ds.ESTADO.get("mapeo_objetivo")
        )

        # El informe PDF siempre describe el mejor modelo: si el usuario está mirando otro
        # modelo desde el menú de comparación, no se pisa ese estado "oficial" guardado para el PDF.
        if respuesta["es_mejor_modelo"]:
            ds.ESTADO["predicciones"] = predicciones
            ds.ESTADO["matriz_confusion_url"] = respuesta.get("matriz_confusion_url")
            ds.ESTADO["real_vs_prediccion_url"] = respuesta.get("real_vs_prediccion_url")

            pd.DataFrame(predicciones).to_csv(
                os.path.join(RESULTADOS_DIR, "predicciones.csv"), index=False
            )

        respuesta["predicciones"] = predicciones
        return jsonify(respuesta)
    except Exception as exc:
        return _error(str(exc))


@app.route("/api/predecir", methods=["POST"])
def api_predecir():
    """Predice un caso nuevo cargado a mano (no del dataset), usando el modelo ya entrenado y
    los mismos encoders/scaler ya ajustados durante el preprocesamiento — nunca se reentrena
    nada acá, solo se transforma el caso nuevo igual que se transformó el de entrenamiento."""
    try:
        if ds.ESTADO.get("modelo") is None:
            return _error('⚠ Entrena un modelo antes de predecir un caso nuevo.')
        transformadores = ds.ESTADO.get("transformadores")
        if not transformadores:
            return _error('⚠ Preprocesa el dataset antes de predecir un caso nuevo.')

        datos = request.get_json(silent=True) or {}
        valores = datos.get("valores") or {}

        modelos_entrenados = ds.ESTADO.get("modelos_entrenados") or {}
        nombre_modelo = datos.get("modelo") or ds.ESTADO["nombre_modelo"]
        if nombre_modelo not in modelos_entrenados:
            nombre_modelo = ds.ESTADO["nombre_modelo"]
        modelo = modelos_entrenados[nombre_modelo]

        try:
            fila = pre.transformar_caso_nuevo(valores, transformadores, ds.ESTADO["columnas_features"])
        except ValueError as exc:
            return _error(str(exc))

        problema = ds.ESTADO["problema"]
        prediccion_cruda = modelo.predict(fila)[0]
        mapeo = ds.ESTADO.get("mapeo_objetivo")

        if problema == "clasificacion":
            etiqueta = mapeo[int(prediccion_cruda)] if mapeo else str(prediccion_cruda)
            respuesta = {"ok": True, "problema": problema, "modelo": nombre_modelo, "prediccion": etiqueta}
            if hasattr(modelo, "predict_proba"):
                proba = modelo.predict_proba(fila)[0]
                respuesta["probabilidades"] = {
                    (mapeo[int(clase)] if mapeo else str(clase)): float(p)
                    for clase, p in zip(modelo.classes_, proba)
                }
        else:
            respuesta = {
                "ok": True, "problema": problema, "modelo": nombre_modelo,
                "prediccion": round(float(prediccion_cruda), 3),
            }

        return jsonify(respuesta)
    except Exception as exc:
        return _error(str(exc))


@app.route("/api/predecir-lote", methods=["POST"])
def api_predecir_lote():
    """Predice todos los casos de un archivo subido (p. ej. 30 casos nuevos) con el modelo ya
    entrenado, sin reentrenar."""
    try:
        if ds.ESTADO.get("modelo") is None:
            return _error('⚠ Entrena un modelo antes de predecir.')
        transformadores = ds.ESTADO.get("transformadores")
        if not transformadores:
            return _error('⚠ Preprocesa el dataset antes de predecir.')

        archivo = request.files.get("archivo")
        if archivo is None or not archivo.filename:
            return _error("Sube un archivo CSV o Excel con los casos nuevos.")
        df, _ = _leer_archivo_subido(archivo)

        modelos_entrenados = ds.ESTADO.get("modelos_entrenados") or {}
        nombre_modelo = request.form.get("modelo") or ds.ESTADO["nombre_modelo"]
        if nombre_modelo not in modelos_entrenados:
            nombre_modelo = ds.ESTADO["nombre_modelo"]
        modelo = modelos_entrenados[nombre_modelo]

        problema = ds.ESTADO["problema"]
        mapeo = ds.ESTADO.get("mapeo_objetivo")
        columnas_features = ds.ESTADO["columnas_features"]

        filas = []
        for i, registro in enumerate(df.to_dict(orient="records"), start=1):
            try:
                fila = pre.transformar_caso_nuevo(registro, transformadores, columnas_features)
            except ValueError as exc:
                return _error(f"Fila {i}: {exc}")
            cruda = modelo.predict(fila)[0]
            if problema == "clasificacion":
                filas.append({"fila": i, "prediccion": mapeo[int(cruda)] if mapeo else str(cruda)})
            else:
                filas.append({"fila": i, "prediccion": round(float(cruda), 3)})

        pd.concat([df.reset_index(drop=True), pd.DataFrame(filas).drop(columns="fila")], axis=1).to_csv(
            os.path.join(RESULTADOS_DIR, "predicciones_lote.csv"), index=False
        )
        return jsonify({
            "ok": True, "problema": problema, "modelo": nombre_modelo,
            "objetivo": ds.obtener_metadata(ds.dataset_actual())["objetivo"], "total": len(filas), "filas": filas,
        })
    except Exception as exc:
        return _error(str(exc))


# ============================================================
# API — RESUMEN Y HISTORIAL
# ============================================================

@app.route("/api/resumen")
def api_resumen():
    try:
        nombre = ds.dataset_actual()
        meta = ds.obtener_metadata(nombre)
        df = ds.df_actual()
        outliers_total = None
        if ds.ESTADO.get("outliers"):
            outliers_total = sum(c["cantidad_outliers"] for c in ds.ESTADO["outliers"]["columnas"])

        return jsonify({
            "ok": True,
            "dataset": meta["nombre"],
            "registros": int(df.shape[0]),
            "variables": int(df.shape[1]),
            "nulos": int(df.isnull().sum().sum()),
            "outliers": outliers_total,
            "modelo": ds.ESTADO.get("nombre_modelo"),
            "metricas": ds.ESTADO.get("metricas"),
            "problema": ds.ESTADO.get("problema"),
        })
    except Exception as exc:
        return _error(str(exc))


@app.route("/api/historial")
def api_historial():
    return jsonify({"ok": True, "historial": _cargar_historial()})


# ============================================================
# PDF
# ============================================================

@app.route("/generar-pdf")
def generar_pdf():
    try:
        nombre = ds.dataset_actual()
        meta = ds.obtener_metadata(nombre)

        resultado = {
            "dataset_meta": {"id": nombre, **meta},
            # Siempre el dataset ORIGINAL (nunca el ya preprocesado): esta seccion describe el
            # punto de partida del analisis, y debe coincidir con la columna "Antes" de la
            # seccion de Preprocesamiento, sin importar si ya se preproceso antes de pedir el PDF.
            "exploracion": pre.explorar_dataset(ds.cargar_dataset(nombre), objetivo=meta["objetivo"]),
            "preprocesamiento": None,
            "algebra": ds.ESTADO.get("algebra"),
            "estadistica": ds.ESTADO.get("estadistica"),
            "outliers": ds.ESTADO.get("outliers"),
            "graficos": ds.ESTADO.get("graficos"),
            "entrenamiento": None,
            "comparacion": ds.ESTADO.get("comparacion_modelos"),
            "parametros_modelos": ds.ESTADO.get("parametros_modelos"),
            "metrica_principal": ds.ESTADO.get("metricas"),
            "matriz_confusion_url": ds.ESTADO.get("matriz_confusion_url"),
            "real_vs_prediccion_url": ds.ESTADO.get("real_vs_prediccion_url"),
            "predicciones": ds.ESTADO.get("predicciones"),
            "comparacion_chart_url": ds.ESTADO.get("comparacion_chart_url"),
            "comparacion_chart_explicacion": ds.ESTADO.get("comparacion_chart_explicacion"),
            "importancia_url": ds.ESTADO.get("importancia_url"),
            "importancia_explicacion": ds.ESTADO.get("importancia_explicacion"),
            "importancia_disponible": ds.ESTADO.get("importancia_disponible"),
            "filas_prueba": (
                int(ds.ESTADO["X_test"].shape[0]) if ds.ESTADO.get("X_test") is not None else None
            ),
        }

        if ds.ESTADO.get("df_procesado") is not None and ds.ESTADO.get("transformaciones") is not None:
            resultado["preprocesamiento"] = {
                "antes": pre.explorar_dataset(ds.cargar_dataset(nombre)),
                "despues": pre.explorar_dataset(ds.ESTADO["df_procesado"]),
                "transformaciones": ds.ESTADO["transformaciones"],
            }
            # Reempaqueta antes/después en el formato compacto que espera pdf_service.
            resultado["preprocesamiento"]["antes"] = {
                "filas": resultado["preprocesamiento"]["antes"]["filas"],
                "columnas": resultado["preprocesamiento"]["antes"]["columnas"],
                "nulos": resultado["preprocesamiento"]["antes"]["total_nulos"],
                "duplicados": resultado["preprocesamiento"]["antes"]["duplicados"],
            }
            resultado["preprocesamiento"]["despues"] = {
                "filas": resultado["preprocesamiento"]["despues"]["filas"],
                "columnas": resultado["preprocesamiento"]["despues"]["columnas"],
                "nulos": resultado["preprocesamiento"]["despues"]["total_nulos"],
                "duplicados": resultado["preprocesamiento"]["despues"]["duplicados"],
            }

        if ds.ESTADO.get("modelo") is not None:
            resultado["entrenamiento"] = {
                "problema": ds.ESTADO["problema"],
                "mejor_modelo_nombre": ds.ESTADO["nombre_modelo"],
            }

        ruta_pdf = os.path.join(INFORMES_DIR, "DataExpert_IA_Informe.pdf")
        pdf_srv.generar_pdf(resultado, ruta_pdf)

        return jsonify({"ok": True, "mensaje": "✅ Informe PDF generado correctamente",
                         "ruta": ruta_pdf, "existe": os.path.isfile(ruta_pdf)})
    except Exception as exc:
        return _error(str(exc))


@app.route("/ver-pdf")
def ver_pdf():
    ruta_pdf = os.path.join(INFORMES_DIR, "DataExpert_IA_Informe.pdf")
    if not os.path.isfile(ruta_pdf):
        return _error("Todavía no se ha generado el informe.", 404)
    return send_file(ruta_pdf, mimetype="application/pdf")


@app.route("/descargar-pdf")
def descargar_pdf():
    ruta_pdf = os.path.join(INFORMES_DIR, "DataExpert_IA_Informe.pdf")
    if not os.path.isfile(ruta_pdf):
        return _error("Todavía no se ha generado el informe.", 404)
    return send_file(ruta_pdf, as_attachment=True, download_name="DataExpert_IA_Informe.pdf")


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5050))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    print(f"\n🚀 DataExpert IA corriendo en http://{host}:{port}\n")
    app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)
