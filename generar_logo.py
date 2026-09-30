"""Genera el logotipo de DataExpert IA como PNG (con transparencia) para usarlo tanto en
la página web como en la portada del informe PDF, donde los emoji no siempre se renderizan
bien con las fuentes por defecto de ReportLab.

Dibuja una insignia cuadrada redondeada con degradado azul -> morado (los mismos colores
de la marca) y un ícono simple de "red de nodos" que representa datos/IA.

Ejecutar: python generar_logo.py
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw

TAM = 512
RADIO_ESQUINA = 110

AZUL = (217, 164, 65)  # caramelo
MORADO = (194, 87, 15)  # terracota

RUTA_SALIDA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "static", "img", "logo.png"
)


def _degradado_diagonal(tam, color_inicio, color_fin):
    """Genera un degradado diagonal (esquina superior izq. -> inferior der.) como array RGB."""
    y, x = np.mgrid[0:tam, 0:tam]
    t = (x.astype(float) + y.astype(float)) / (2 * tam)
    canal = [
        (color_inicio[i] + (color_fin[i] - color_inicio[i]) * t).astype(np.uint8)
        for i in range(3)
    ]
    return np.dstack(canal)


def _mascara_rect_redondeado(tam, radio):
    mascara = Image.new("L", (tam, tam), 0)
    dibujo = ImageDraw.Draw(mascara)
    dibujo.rounded_rectangle([0, 0, tam - 1, tam - 1], radius=radio, fill=255)
    return mascara


def generar_logo():
    fondo_rgb = _degradado_diagonal(TAM, AZUL, MORADO)
    fondo = Image.fromarray(fondo_rgb, mode="RGB").convert("RGBA")
    mascara = _mascara_rect_redondeado(TAM, RADIO_ESQUINA)
    fondo.putalpha(mascara)

    dibujo = ImageDraw.Draw(fondo)

    centro = TAM / 2
    radio_nodo_central = TAM * 0.05
    radio_orbita = TAM * 0.24
    radio_nodo_externo = TAM * 0.032
    n_nodos = 6

    blanco = (255, 255, 255, 235)
    blanco_linea = (255, 255, 255, 130)
    ancho_linea = max(2, TAM // 140)

    puntos_externos = []
    for i in range(n_nodos):
        angulo = (2 * math.pi / n_nodos) * i - math.pi / 2
        x = centro + radio_orbita * math.cos(angulo)
        y = centro + radio_orbita * math.sin(angulo)
        puntos_externos.append((x, y))

    # Líneas del nodo central hacia cada nodo externo, y entre nodos externos consecutivos
    # (para que se lea como una red, no solo una estrella).
    for x, y in puntos_externos:
        dibujo.line([(centro, centro), (x, y)], fill=blanco_linea, width=ancho_linea)
    for i in range(n_nodos):
        x1, y1 = puntos_externos[i]
        x2, y2 = puntos_externos[(i + 1) % n_nodos]
        dibujo.line([(x1, y1), (x2, y2)], fill=blanco_linea, width=max(1, ancho_linea - 1))

    for x, y in puntos_externos:
        dibujo.ellipse(
            [x - radio_nodo_externo, y - radio_nodo_externo, x + radio_nodo_externo, y + radio_nodo_externo],
            fill=blanco,
        )

    dibujo.ellipse(
        [centro - radio_nodo_central, centro - radio_nodo_central,
         centro + radio_nodo_central, centro + radio_nodo_central],
        fill=blanco,
    )

    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
    fondo.save(RUTA_SALIDA)
    print(f"Logo guardado en {RUTA_SALIDA}")


if __name__ == "__main__":
    generar_logo()
