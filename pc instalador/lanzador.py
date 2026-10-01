"""Lanzador de DataExpert IA para Windows.

Al hacer doble clic en el acceso directo:
  1. aparece una ventana pequeña (así se ve enseguida que está arrancando),
  2. se prepara la carpeta de datos y se inicia el servidor local,
  3. se abre la aplicación en el navegador.
Cerrar la ventana cierra la aplicación. Los informes, resultados, gráficos e historial quedan en la carpeta de datos del usuario.

Variables solo para pruebas: DATAEXPERT_PRUEBA=1 (sin ventana ni navegador), DATAEXPERT_PUERTO, DATAEXPERT_DATOS.
"""
import ctypes
import json
import multiprocessing
import os
import queue
import socket
import sys
import threading
import time
import traceback
import urllib.request
import webbrowser
from pathlib import Path

CODIGO = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
if str(CODIGO) not in sys.path:
    sys.path.insert(0, str(CODIGO))

NOMBRE = "DataExpert IA"
PUERTO_BLOQUEO = 50778  # solo una copia de DataExpert IA a la vez
PRIMER_PUERTO = int(os.environ.get("DATAEXPERT_PUERTO") or 5050)
CANTIDAD_PUERTOS = 1 if os.environ.get("DATAEXPERT_PUERTO") else 11
MODO_PRUEBA = os.environ.get("DATAEXPERT_PRUEBA") == "1"
RECURSOS = CODIGO / "recursos" if (CODIGO / "recursos").exists() else Path(__file__).resolve().parent / "recursos"


def responde_la_aplicacion(puerto):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{puerto}/api/salud", timeout=1) as r:
            return json.loads(r.read().decode("utf-8")).get("aplicacion") == "dataexpert_ia"
    except Exception:
        return False


def puerto_libre(puerto):
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", puerto))
            return True
        except OSError:
            return False


def buscar_copia_abierta(segundos):
    """Espera hasta `segundos` a que otra copia responda; devuelve su dirección o None."""
    limite = time.time() + segundos
    while time.time() < limite:
        for puerto in range(PRIMER_PUERTO, PRIMER_PUERTO + CANTIDAD_PUERTOS):
            if responde_la_aplicacion(puerto):
                return f"http://127.0.0.1:{puerto}"
        time.sleep(0.5)
    return None


def preparar_registro(carpeta):
    """Sin consola, print y los avisos de Flask fallarían: todo va a un archivo de registro en la carpeta de datos."""
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / "registro_dataexpert.log"
    if ruta.exists() and ruta.stat().st_size > 2_000_000:
        ruta.unlink()
    archivo = open(ruta, "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = archivo
    return ruta


class Arranque:
    """Importa la aplicación (lo lento) e inicia el servidor local."""

    def __init__(self):
        self.url = None
        self.servidor = None
        self.modulo = None

    def iniciar(self):
        puerto = next((p for p in range(PRIMER_PUERTO, PRIMER_PUERTO + CANTIDAD_PUERTOS) if puerto_libre(p)), None)
        if puerto is None:
            raise RuntimeError("No hay ningún puerto libre entre el %d y el %d." % (PRIMER_PUERTO, PRIMER_PUERTO + CANTIDAD_PUERTOS - 1))
        import app as modulo
        from werkzeug.serving import make_server
        self.modulo = modulo
        self.servidor = make_server("127.0.0.1", puerto, modulo.app, threaded=True)
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{puerto}"
        return self.url

    def procesos_en_curso(self):
        nombres = {"explorar": "Exploración", "preprocesar": "Preprocesamiento", "algebra": "Álgebra lineal",
                   "estadistica": "Estadística", "outliers": "Valores atípicos", "graficos": "Gráficos",
                   "entrenar": "Entrenamiento de modelos", "evaluar": "Evaluación", "pdf": "Informe PDF"}
        try:
            if self.modulo:
                with self.modulo._LOCK_ACTIVIDAD:
                    activos = list(self.modulo.ACTIVIDAD["activos"].values())
                return [nombres.get(p["accion"], p["accion"]) for p in activos]
        except Exception:
            pass
        return []

    def detener(self):
        try:
            if self.servidor:
                self.servidor.shutdown()
        except Exception:
            pass


def registrar_tipografia():
    """Carga Unbounded (la tipografía de los títulos) solo para esta ventana; si no se puede, se usa Segoe UI."""
    try:
        for archivo in ("Unbounded-Black.ttf", "InstrumentSans-Regular.ttf", "InstrumentSans-Bold.ttf"):
            ruta = CODIGO / "static" / "fuentes" / "pdf" / archivo
            if ruta.exists():
                ctypes.windll.gdi32.AddFontResourceExW(str(ruta), 0x10, 0)  # FR_PRIVATE
    except Exception:
        pass


def ventana(arranque, carpeta_datos):
    import tkinter as tk
    from tkinter import font as tkfont
    from tkinter import messagebox

    amarillo, tinta, blanco, rosa, cielo, suave = "#ffd23f", "#14112b", "#ffffff", "#ff8a9d", "#4cc3ff", "#5b5680"
    registrar_tipografia()
    raiz = tk.Tk()
    raiz.title(NOMBRE)
    raiz.configure(bg=amarillo)
    raiz.resizable(False, False)
    try:
        raiz.iconbitmap(default=str(RECURSOS / "icono.ico"))
    except Exception:
        pass
    familias = set(tkfont.families())
    titulo_fuente = next((f for f in sorted(familias) if f.startswith("Unbounded")), "Segoe UI")
    texto_fuente = "Instrument Sans" if "Instrument Sans" in familias else "Segoe UI"
    ancho = 460

    # Sombra dura como en la página: un marco de tinta que sobresale 6 px a la derecha y abajo; dos cuadros del color del fondo
    # recortan las esquinas para que parezca un panel desplazado.
    sombra = tk.Frame(raiz, bg=tinta)
    sombra.pack(padx=26, pady=26, fill="x")
    panel = tk.Frame(sombra, bg=blanco, highlightbackground=tinta, highlightcolor=tinta, highlightthickness=3)
    panel.pack(padx=(0, 6), pady=(0, 6), fill="x")
    tk.Frame(sombra, bg=amarillo, width=6, height=6).place(relx=1.0, y=0, anchor="ne")
    tk.Frame(sombra, bg=amarillo, width=6, height=6).place(x=0, rely=1.0, anchor="sw")
    try:
        logo = tk.PhotoImage(file=str(RECURSOS / "logo_128.png")).subsample(2, 2)
        tk.Label(panel, image=logo, bg=blanco).pack(pady=(20, 6))
        raiz.logo = logo
    except Exception:
        pass
    tk.Label(panel, text=NOMBRE, font=(titulo_fuente, 17, "bold"), bg=blanco, fg=tinta).pack()
    estado = tk.StringVar(value="Iniciando… un momento, se está preparando todo.")
    tk.Label(panel, textvariable=estado, font=(texto_fuente, 10), bg=blanco, fg=suave, wraplength=340, justify="center", height=3).pack(pady=(6, 10))

    def boton(texto, comando, color):
        contorno = tk.Frame(panel, bg=tinta)
        contorno.pack(fill="x", padx=38, pady=4)
        b = tk.Button(contorno, text=texto, command=comando, font=(texto_fuente, 10, "bold"), relief="flat", cursor="hand2", bg=color, fg=tinta,
                      activebackground=amarillo, activeforeground=tinta, bd=0, padx=14, pady=8)
        b.pack(fill="x", padx=2, pady=2)
        return b

    abrir = boton("Abrir DataExpert IA en el navegador", lambda: arranque.url and webbrowser.open(arranque.url), rosa)
    boton("Abrir la carpeta de mis datos", lambda: os.startfile(str(carpeta_datos)), blanco)
    boton("Cerrar DataExpert IA", lambda: salir(), blanco)
    tk.Label(panel, text=f"Tus informes y resultados se guardan en:\n{carpeta_datos}", font=(texto_fuente, 8), bg=blanco, fg=suave, wraplength=360).pack(pady=(10, 18))

    mensajes = queue.Queue()

    def salir(forzar=False):
        pendientes = [] if forzar else arranque.procesos_en_curso()
        if pendientes and not messagebox.askokcancel(NOMBRE, "Hay un proceso en marcha:\n\n• " + "\n• ".join(pendientes) +
                                                     "\n\nSi cierras DataExpert IA ahora se pierde. ¿Cerrar de todos modos?", icon="warning"):
            return
        arranque.detener()
        raiz.destroy()
        os._exit(0)

    def trabajar():
        try:
            mensajes.put(("listo", arranque.iniciar()))
        except Exception:
            traceback.print_exc()
            mensajes.put(("error", traceback.format_exc(limit=3)))

    def revisar():
        try:
            tipo, dato = mensajes.get_nowait()
        except queue.Empty:
            raiz.after(200, revisar)
            return
        if tipo == "listo":
            estado.set("DataExpert IA está funcionando. Se abrió en tu navegador; si lo cerraste, pulsa el botón de abajo.")
            webbrowser.open(dato)
        else:
            estado.set("No se pudo iniciar. El detalle quedó guardado en registro_dataexpert.log dentro de la carpeta de datos.")
            messagebox.showerror(NOMBRE, "No se pudo iniciar DataExpert IA.\n\n" + dato[-600:])

    raiz.update_idletasks()  # el alto se calcula con lo que hay dentro, para que nada quede cortado
    alto = raiz.winfo_reqheight()
    raiz.geometry(f"{ancho}x{alto}+{(raiz.winfo_screenwidth() - ancho) // 2}+{max(20, (raiz.winfo_screenheight() - alto) // 3)}")
    raiz.protocol("WM_DELETE_WINDOW", salir)
    threading.Thread(target=trabajar, daemon=True).start()
    raiz.after(200, revisar)
    raiz.mainloop()


def main():
    multiprocessing.freeze_support()
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    from src import configuracion

    bloqueo = socket.socket()
    try:
        bloqueo.bind(("127.0.0.1", PUERTO_BLOQUEO + (PRIMER_PUERTO if os.environ.get("DATAEXPERT_PUERTO") else 0)))
    except OSError:  # ya hay una copia abierta o arrancando: se muestra esa en vez de abrir otra
        direccion = buscar_copia_abierta(90)
        if direccion and not MODO_PRUEBA:
            webbrowser.open(direccion)
        return
    preparar_registro(configuracion.RAIZ)

    arranque = Arranque()
    if MODO_PRUEBA:
        print("Iniciando DataExpert IA en modo de prueba…", flush=True)
        print("DATAEXPERT_LISTA", arranque.iniciar(), flush=True)
        threading.Event().wait()
    else:
        ventana(arranque, configuracion.RAIZ)


if __name__ == "__main__":
    main()
