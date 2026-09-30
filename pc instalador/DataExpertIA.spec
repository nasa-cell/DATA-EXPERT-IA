# -*- mode: python ; coding: utf-8 -*-
"""Receta de PyInstaller para DataExpert IA (carpeta con DataExpertIA.exe y todo lo que necesita)."""
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

AQUI = Path(SPECPATH)
PROYECTO = AQUI.parent

datos = [
    (str(PROYECTO / "templates"), "templates"),
    # Solo el código de la página: static/graficos son gráficos generados al usar la aplicación y no se empaquetan.
    (str(PROYECTO / "static" / "css"), "static/css"),
    (str(PROYECTO / "static" / "js"), "static/js"),
    (str(PROYECTO / "static" / "img"), "static/img"),
    (str(PROYECTO / "static" / "fuentes"), "static/fuentes"),
    (str(PROYECTO / "data"), "data"),
    (str(AQUI / "recursos" / "icono.ico"), "recursos"),
    (str(AQUI / "recursos" / "logo_128.png"), "recursos"),
    (str(PROYECTO / "README.md"), "."),
]

a = Analysis(
    [str(AQUI / "lanzador.py")],
    pathex=[str(PROYECTO)],
    binaries=[],
    datas=datos,
    hiddenimports=collect_submodules("sklearn", filter=lambda n: ".tests" not in n) + collect_submodules("src")
    + ["werkzeug.serving", "openpyxl", "matplotlib.backends.backend_agg"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["IPython", "pytest", "PyQt5", "PyQt6", "PySide2", "PySide6", "notebook", "sphinx", "matplotlib.tests",
              "tensorboard", "tensorflow", "keras", "torch", "grpc", "h5py", "onnx", "triton"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DataExpertIA",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(AQUI / "recursos" / "icono.ico"),
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="DataExpertIA")
