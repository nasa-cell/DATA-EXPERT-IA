"""Rutas de DataExpert IA: separa el código (que se lee) de los datos que la aplicación escribe.

- Desde el código fuente (python app.py) todo queda como siempre, dentro de la carpeta del proyecto.
- Instalada con el instalador de Windows, el código va dentro del ejecutable y todo lo que la persona genera
  (informes, resultados, historial y gráficos) se guarda en la carpeta «datos_usuario» junto al programa,
  para que sobreviva a las actualizaciones. La variable DATAEXPERT_DATOS permite cambiar esa carpeta (se usa en las pruebas).
"""
import os
import sys
from pathlib import Path

EMPAQUETADO = bool(getattr(sys, "frozen", False))

# CODIGO: donde están templates/, static/ y data/ (dentro del ejecutable si está instalada).
CODIGO = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))

# RAIZ: donde se escribe todo lo que genera la persona.
if os.environ.get("DATAEXPERT_DATOS"):
    RAIZ = Path(os.environ["DATAEXPERT_DATOS"])
elif EMPAQUETADO:
    RAIZ = Path(sys.executable).resolve().parent / "datos_usuario"
else:
    RAIZ = CODIGO

INFORMES_DIR = RAIZ / "informes"
RESULTADOS_DIR = RAIZ / "resultados"
HISTORIAL_PATH = RESULTADOS_DIR / "historial.json"

# Los gráficos generados se sirven desde una ruta propia cuando viven fuera del código empaquetado.
if RAIZ == CODIGO:
    GRAFICOS_DIR = CODIGO / "static" / "graficos"
    URL_GRAFICOS = "/static/graficos"
else:
    GRAFICOS_DIR = RAIZ / "graficos"
    URL_GRAFICOS = "/graficos-generados"


def preparar_carpetas():
    for carpeta in (RAIZ, INFORMES_DIR, RESULTADOS_DIR, GRAFICOS_DIR):
        carpeta.mkdir(parents=True, exist_ok=True)


def ruta_de_url(url: str):
    """Convierte una URL de la aplicación (/static/... o /graficos-generados/...) en la ruta real del archivo, o None."""
    url = url.split("?", 1)[0]
    if url.startswith(URL_GRAFICOS + "/"):
        base, resto = GRAFICOS_DIR, url[len(URL_GRAFICOS) + 1:]
    else:
        base, resto = CODIGO, url.lstrip("/")
    ruta = (base / resto).resolve()
    try:
        ruta.relative_to(base.resolve())
    except ValueError:
        return None
    return ruta
