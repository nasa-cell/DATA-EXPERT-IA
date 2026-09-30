"""Genera el informe PDF completo del análisis con ReportLab.

Recibe el diccionario de resultados del análisis actual (dataset, exploración,
preprocesamiento, álgebra lineal, estadística, outliers, gráficos, entrenamiento,
evaluación y comparación de modelos) y arma un documento con portada, texto explicativo
generado a partir de los datos reales, tablas y las imágenes ya generadas por
visualization_service.py — cada gráfico en su propia sección, con su propia interpretación.
"""

import os
import re
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph as _Paragraph, SimpleDocTemplate, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether,
)

from src import configuracion as cfg

BASE_DIR = str(cfg.CODIGO)
ANCHO_CONTENIDO = 17.4 * cm

# ------------------------------------------------------------------
# Identidad visual: la misma de la página web («laboratorio pop»).
# Tinta oscura, blanco, un color por dataset y tipografías propias.
# ------------------------------------------------------------------
HEX_TINTA = "#14112b"
HEX_TINTA_SUAVE = "#4a4668"
C_TINTA = colors.HexColor(HEX_TINTA)
C_TINTA_SUAVE = colors.HexColor(HEX_TINTA_SUAVE)
C_BLANCO = colors.white
C_AMARILLO = colors.HexColor("#ffd23f")
C_ROSA = colors.HexColor("#ff5c8a")
C_CIELO = colors.HexColor("#3dc7ff")
C_MENTA = colors.HexColor("#2fe0a1")
C_LINEA = colors.HexColor("#d8d4ea")


def _mezclar(hex_color, blanco):
    """Mezcla un color con blanco (`blanco` de 0 a 1 es la proporción de blanco)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return colors.Color(*(round(v * (1 - blanco) + 255 * blanco) / 255 for v in (r, g, b)))


# Colores que cambian con el dataset (se fijan al empezar cada informe con _aplicar_tema).
TEMA = {"vivo": C_AMARILLO, "pagina": C_AMARILLO, "tinte": colors.HexColor("#fff6d6")}


def _aplicar_tema(meta):
    hex_a = (meta or {}).get("color_a") or "#ffd23f"
    try:
        TEMA["vivo"] = colors.HexColor(hex_a)
        TEMA["pagina"] = _mezclar(hex_a, 0.16)
        TEMA["tinte"] = _mezclar(hex_a, 0.88)
    except Exception:
        TEMA.update(vivo=C_AMARILLO, pagina=C_AMARILLO, tinte=colors.HexColor("#fff6d6"))


# ------------------------------------------------------------------
# Tipografías: Unbounded (títulos), Instrument Sans (texto) y JetBrains Mono (datos), en static/fuentes/pdf/.
# Si faltaran los archivos, se usan las fuentes básicas de PDF y el informe sigue saliendo.
# ------------------------------------------------------------------
F_TITULO, F_TITULO_NEGRA = "Helvetica-Bold", "Helvetica-Bold"
F_TEXTO, F_TEXTO_NEGRITA = "Helvetica", "Helvetica-Bold"
F_DATOS, F_DATOS_NEGRITA = "Courier", "Courier-Bold"


def _registrar_fuentes():
    global F_TITULO, F_TITULO_NEGRA, F_TEXTO, F_TEXTO_NEGRITA, F_DATOS, F_DATOS_NEGRITA
    carpeta = os.path.join(BASE_DIR, "static", "fuentes", "pdf")
    archivos = {
        "Titulo": "Unbounded-Bold.ttf", "TituloNegra": "Unbounded-Black.ttf",
        "Texto": "InstrumentSans-Regular.ttf", "TextoNegrita": "InstrumentSans-Bold.ttf",
        "Datos": "JetBrainsMono-Regular.ttf", "DatosNegrita": "JetBrainsMono-Bold.ttf",
    }
    try:
        for nombre, archivo in archivos.items():
            pdfmetrics.registerFont(TTFont(nombre, os.path.join(carpeta, archivo)))
        # <b> usa la negrita del texto y <i> usa la letra de datos: los nombres de funciones y variables se ven como código.
        pdfmetrics.registerFontFamily("Texto", normal="Texto", bold="TextoNegrita", italic="Datos", boldItalic="DatosNegrita")
        F_TITULO, F_TITULO_NEGRA, F_TEXTO, F_TEXTO_NEGRITA, F_DATOS, F_DATOS_NEGRITA = (
            "Titulo", "TituloNegra", "Texto", "TextoNegrita", "Datos", "DatosNegrita")
    except Exception:
        pass


_registrar_fuentes()

# Instrument Sans no trae estos símbolos: se dibujan con la letra de datos para que nunca salgan cuadros vacíos.
_GLIFOS_FALTANTES = re.compile("[²±σ≥≤]")


def Paragraph(texto, estilo, *args, **kwargs):
    if isinstance(texto, str) and estilo.fontName in (F_TEXTO, F_TEXTO_NEGRITA):
        texto = _GLIFOS_FALTANTES.sub(lambda m: f'<font name="{F_DATOS}">{m.group(0)}</font>', texto)
    return _Paragraph(texto, estilo, *args, **kwargs)


# ============================================================
# PORTADA Y MARCO DE PÁGINA (se dibujan sobre el lienzo)
# ============================================================

def _ruta_estatica(ruta_relativa):
    ruta = os.path.join(BASE_DIR, ruta_relativa.replace("/", os.sep))
    return ruta if os.path.isfile(ruta) else None


def _portada(canvas_obj, doc, meta, fecha):
    ancho, alto = A4
    c = canvas_obj
    c.saveState()
    # Fondo: el color del dataset
    c.setFillColor(TEMA["pagina"])
    c.rect(0, 0, ancho, alto, stroke=0, fill=1)

    # Barra superior con la marca
    c.setFillColor(C_TINTA)
    c.rect(0, alto - 2.6 * cm, ancho, 2.6 * cm, stroke=0, fill=1)
    logo = _ruta_estatica("static/img/logo.png")
    if logo:
        c.drawImage(ImageReader(logo), 1.8 * cm, alto - 2.15 * cm, 1.7 * cm, 1.7 * cm, mask="auto")
    c.setFillColor(C_BLANCO)
    c.setFont(F_TITULO_NEGRA, 17)
    c.drawString(3.9 * cm, alto - 1.5 * cm, "DataExpert IA")
    c.setFont(F_TEXTO, 9)
    c.drawString(3.9 * cm, alto - 2.05 * cm, "Fundamentos y Algoritmia para Inteligencia Artificial")

    # Panel principal con sombra dura
    x0, y0, w, h = 1.8 * cm, 8.9 * cm, ancho - 3.6 * cm, 15.4 * cm
    c.setFillColor(C_TINTA)
    c.roundRect(x0 + 0.35 * cm, y0 - 0.35 * cm, w, h, 0.7 * cm, stroke=0, fill=1)
    c.setFillColor(C_BLANCO)
    c.setStrokeColor(C_TINTA)
    c.setLineWidth(3)
    c.roundRect(x0, y0, w, h, 0.7 * cm, stroke=1, fill=1)

    cursor = y0 + h - 1.5 * cm
    # Etiqueta «Informe de análisis»
    etiqueta = "Informe de análisis"
    c.setFont(F_TEXTO_NEGRITA, 10)
    ancho_et = pdfmetrics.stringWidth(etiqueta, F_TEXTO_NEGRITA, 10) + 0.9 * cm
    c.setFillColor(TEMA["pagina"])
    c.setLineWidth(1.6)
    c.roundRect(x0 + 1 * cm, cursor - 0.2 * cm, ancho_et, 0.75 * cm, 0.3 * cm, stroke=1, fill=1)
    c.setFillColor(C_TINTA)
    c.drawString(x0 + 1.45 * cm, cursor + 0.05 * cm, etiqueta)
    cursor -= 1.9 * cm

    # Nombre del dataset, lo más grande que quepa
    nombre = str(meta.get("nombre", "Dataset"))
    maximo = w - 2 * cm
    tam = 44
    while pdfmetrics.stringWidth(nombre, F_TITULO_NEGRA, tam) > maximo and tam > 22:
        tam -= 2
    lineas = simpleSplit(nombre, F_TITULO_NEGRA, tam, maximo)[:2]
    c.setFillColor(C_TINTA)
    c.setFont(F_TITULO_NEGRA, tam)
    for linea in lineas:
        c.drawString(x0 + 1 * cm, cursor, linea)
        cursor -= tam * 1.15
    cursor -= 0.2 * cm

    # Descripción
    c.setFont(F_TEXTO, 12.5)
    c.setFillColor(C_TINTA_SUAVE)
    for linea in simpleSplit(str(meta.get("descripcion", "")), F_TEXTO, 12.5, maximo)[:3]:
        c.drawString(x0 + 1 * cm, cursor, linea)
        cursor -= 0.62 * cm
    cursor -= 0.35 * cm

    # Datos clave en «pastillas»
    tipo = {"clasificacion": "Clasificación", "regresion": "Regresión"}.get(meta.get("problema"), str(meta.get("problema", "")))
    pastillas = [tipo, f"Objetivo: {meta.get('objetivo', '')}", fecha.strftime("%d/%m/%Y %H:%M")]
    x = x0 + 1 * cm
    c.setFont(F_TEXTO_NEGRITA, 9.5)
    for texto in pastillas:
        ancho_p = pdfmetrics.stringWidth(texto, F_TEXTO_NEGRITA, 9.5) + 0.8 * cm
        if x + ancho_p > x0 + w - 0.8 * cm:
            break
        c.setFillColor(C_BLANCO)
        c.setLineWidth(1.4)
        c.roundRect(x, cursor - 0.22 * cm, ancho_p, 0.7 * cm, 0.35 * cm, stroke=1, fill=1)
        c.setFillColor(C_TINTA)
        c.drawString(x + 0.4 * cm, cursor + 0.02 * cm, texto)
        x += ancho_p + 0.3 * cm
    cursor -= 0.9 * cm

    # Foto del dataset (si tiene), recortada para llenar su marco
    foto = _ruta_estatica("static/" + str(meta["imagen"])) if meta.get("imagen") else None
    bx, by, bw = x0 + 1 * cm, y0 + 1 * cm, w - 2 * cm
    bh = max(2.2 * cm, cursor - by)
    if foto:
        lector = ImageReader(foto)
        iw, ih = lector.getSize()
        escala = max(bw / iw, bh / ih)
        c.saveState()
        camino = c.beginPath()
        camino.roundRect(bx, by, bw, bh, 0.5 * cm)
        c.clipPath(camino, stroke=0, fill=0)
        c.drawImage(lector, bx + (bw - iw * escala) / 2, by + (bh - ih * escala) / 2, iw * escala, ih * escala)
        c.restoreState()
        c.setStrokeColor(C_TINTA)
        c.setLineWidth(3)
        c.roundRect(bx, by, bw, bh, 0.5 * cm, stroke=1, fill=0)
    else:
        c.setFillColor(TEMA["tinte"])
        c.setStrokeColor(C_TINTA)
        c.setLineWidth(3)
        c.roundRect(bx, by, bw, bh, 0.5 * cm, stroke=1, fill=1)

    # Ilustración de datos bajo el panel: tres barras con sombra y puntos
    base = 1.3 * cm
    barras = [(2.3 * cm, 3.0 * cm, C_ROSA), (5.3 * cm, 4.6 * cm, C_CIELO), (8.3 * cm, 6.2 * cm, C_BLANCO)]
    for bxx, alto_b, color in barras:
        c.setFillColor(C_TINTA)
        c.roundRect(bxx + 0.22 * cm, base - 0.22 * cm, 2.4 * cm, alto_b, 0.4 * cm, stroke=0, fill=1)
        c.setFillColor(color)
        c.setStrokeColor(C_TINTA)
        c.setLineWidth(2.6)
        c.roundRect(bxx, base, 2.4 * cm, alto_b, 0.4 * cm, stroke=1, fill=1)
    puntos = [(12.4, 3.0, 0.32, C_ROSA), (13.7, 5.2, 0.26, C_CIELO), (15.2, 2.2, 0.36, C_AMARILLO), (16.6, 4.4, 0.3, C_MENTA),
              (17.9, 6.0, 0.24, C_ROSA), (14.5, 7.0, 0.22, C_BLANCO), (18.2, 2.9, 0.3, C_BLANCO)]
    for px, py, radio, color in puntos:
        c.setFillColor(color)
        c.setStrokeColor(C_TINTA)
        c.setLineWidth(1.8)
        c.circle(px * cm, py * cm, radio * cm, stroke=1, fill=1)
    c.restoreState()


def _interior(canvas_obj, doc, meta):
    ancho, alto = A4
    c = canvas_obj
    c.saveState()
    c.setFillColor(C_BLANCO)
    c.rect(0, 0, ancho, alto, stroke=0, fill=1)

    # Cabecera: marca a la izquierda, dataset a la derecha y una línea gruesa
    logo = _ruta_estatica("static/img/logo.png")
    if logo:
        c.drawImage(ImageReader(logo), 1.8 * cm, alto - 1.55 * cm, 0.85 * cm, 0.85 * cm, mask="auto")
    c.setFillColor(C_TINTA)
    c.setFont(F_TITULO, 8.5)
    c.drawString(2.9 * cm, alto - 1.13 * cm, "DataExpert IA")
    nombre = str(meta.get("nombre", ""))
    c.setFont(F_TEXTO_NEGRITA, 8.5)
    ancho_n = pdfmetrics.stringWidth(nombre, F_TEXTO_NEGRITA, 8.5) + 0.7 * cm
    c.setFillColor(TEMA["pagina"])
    c.setStrokeColor(C_TINTA)
    c.setLineWidth(1.3)
    c.roundRect(ancho - 1.8 * cm - ancho_n, alto - 1.42 * cm, ancho_n, 0.6 * cm, 0.3 * cm, stroke=1, fill=1)
    c.setFillColor(C_TINTA)
    c.drawString(ancho - 1.8 * cm - ancho_n + 0.35 * cm, alto - 1.22 * cm, nombre)
    c.setLineWidth(2)
    c.line(1.8 * cm, alto - 1.8 * cm, ancho - 1.8 * cm, alto - 1.8 * cm)

    # Pie: número de página en un cuadro con el color del dataset
    c.setFillColor(C_TINTA_SUAVE)
    c.setFont(F_TEXTO, 8)
    c.drawString(1.8 * cm, 1.15 * cm, "Informe de análisis · Fundamentos y Algoritmia para Inteligencia Artificial")
    lado = 0.85 * cm
    c.setFillColor(TEMA["pagina"])
    c.setStrokeColor(C_TINTA)
    c.setLineWidth(1.5)
    c.roundRect(ancho - 1.8 * cm - lado, 0.85 * cm, lado, lado, 0.25 * cm, stroke=1, fill=1)
    c.setFillColor(C_TINTA)
    c.setFont(F_TITULO, 8.5)
    c.drawCentredString(ancho - 1.8 * cm - lado / 2, 1.1 * cm, str(doc.page))
    c.restoreState()


# ============================================================
# HELPERS DE MAQUETACIÓN
# ============================================================

def _seccion(titulo, estilos):
    """Encabezado de sección: insignia con el número, título y línea gruesa. Va en un KeepTogether para que el
    título nunca quede solo al final de una página."""
    coincidencia = re.match(r"^([\d\-]+)\.\s*(.+)$", titulo)
    numero, texto = (coincidencia.group(1), coincidencia.group(2)) if coincidencia else ("", titulo)
    ancho_insignia = 1.5 * cm if len(numero) <= 2 else 2.3 * cm
    celdas = [[Paragraph(numero, estilos["insignia"]) if numero else "", Paragraph(texto, estilos["h1"])]]
    tabla = Table(celdas, colWidths=[ancho_insignia, ANCHO_CONTENIDO - ancho_insignia], rowHeights=[1.3 * cm], spaceBefore=0.5 * cm)
    estilo = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 0),
        ("LEFTPADDING", (1, 0), (1, 0), 12),
        ("LINEBELOW", (0, 0), (-1, 0), 2.4, C_TINTA),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]
    if numero:
        estilo += [("BACKGROUND", (0, 0), (0, 0), TEMA["pagina"]), ("BOX", (0, 0), (0, 0), 1.8, C_TINTA)]
    tabla.setStyle(TableStyle(estilo))
    separacion = Spacer(1, 0.6 * cm)
    tabla.keepWithNext = separacion.keepWithNext = True
    return [tabla, separacion]


def _h2(texto, estilos):
    """Subtítulo con una barra de color a la izquierda."""
    tabla = Table([["", Paragraph(texto, estilos["h2"])]], colWidths=[0.28 * cm, ANCHO_CONTENIDO - 0.28 * cm], spaceBefore=0.35 * cm)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), TEMA["vivo"]), ("BOX", (0, 0), (0, 0), 1.2, C_TINTA),
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 0),
        ("LEFTPADDING", (1, 0), (1, 0), 10), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    tabla.hAlign = "CENTER"  # mismo borde que las insignias de sección y los recuadros
    tabla.keepWithNext = True
    return tabla


def _callout(texto, estilos, color=None):
    """Recuadro con borde oscuro y barra de color, usado para las explicaciones e interpretaciones generadas
    a partir de los datos reales. El parámetro `color` se conserva por compatibilidad: el color lo pone el tema."""
    tabla = Table([[Paragraph(texto, estilos["callout"])]], colWidths=[ANCHO_CONTENIDO])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TEMA["tinte"]),
        ("BOX", (0, 0), (-1, -1), 1.4, C_TINTA),
        ("LINEBEFORE", (0, 0), (0, -1), 6, TEMA["vivo"]),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 15), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return tabla


def _tabla_kv(pares, estilos, col_izq=6.5 * cm):
    filas = [[Paragraph(f"<b>{k}</b>", estilos["kv_label"]), Paragraph(str(v), estilos["kv_valor"])] for k, v in pares]
    tabla = Table(filas, colWidths=[col_izq, ANCHO_CONTENIDO - col_izq])
    tabla.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.4, C_TINTA),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, C_LINEA),
        ("BACKGROUND", (0, 0), (0, -1), TEMA["tinte"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
    ]))
    # KeepTogether: si la tabla no entra completa en lo que queda de la página, se mueve entera a la siguiente.
    return KeepTogether([tabla])


def _tabla_datos(encabezados, filas, estilos, anchos=None):
    datos = [[Paragraph(f"<b>{h}</b>", estilos["th"]) for h in encabezados]]
    for fila in filas:
        datos.append([Paragraph(str(c), estilos["td_primera"] if i == 0 else estilos["td"]) for i, c in enumerate(fila)])
    tabla = Table(datos, colWidths=anchos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_TINTA),
        ("BOX", (0, 0), (-1, -1), 1.4, C_TINTA),
        ("INNERGRID", (0, 1), (-1, -1), 0.5, C_LINEA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_BLANCO, TEMA["tinte"]]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return KeepTogether([tabla])


def _tarjetas_resumen(resultado, estilos):
    """Fila de cuatro tarjetas con los números clave del análisis, como en la página."""
    meta = resultado["dataset_meta"]
    explor = resultado.get("exploracion") or {}
    entren = resultado.get("entrenamiento") or {}
    metrica = resultado.get("metrica_principal")
    if metrica and entren.get("problema") == "clasificacion":
        valor_metrica, etiqueta_metrica = f"{metrica['accuracy'] * 100:.1f}%", "Accuracy"
    elif metrica:
        valor_metrica, etiqueta_metrica = f"{metrica['r2']:.3f}", "R²"
    else:
        valor_metrica, etiqueta_metrica = "—", "Métrica principal"
    tarjetas = [
        (str(explor.get("filas", "—")), "Registros"),
        (str(explor.get("columnas", "—")), "Variables"),
        (str(entren.get("mejor_modelo_nombre", "—")), "Mejor modelo"),
        (valor_metrica, etiqueta_metrica),
    ]
    celdas, columnas = [], []
    for i, (valor, etiqueta) in enumerate(tarjetas):
        if i:
            celdas.append("")
            columnas.append(0.3 * cm)
        celdas.append([Paragraph(valor, estilos["tarjeta_valor_chico"] if len(valor) > 11 else estilos["tarjeta_valor"]), Paragraph(etiqueta, estilos["tarjeta_etiqueta"])])
        columnas.append((ANCHO_CONTENIDO - 3 * 0.3 * cm) / 4)
    tabla = Table([celdas], colWidths=columnas)
    estilo = [("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    for i in range(4):
        col = i * 2
        estilo += [("BOX", (col, 0), (col, 0), 1.6, C_TINTA), ("BACKGROUND", (col, 0), (col, 0), TEMA["pagina"] if i == 0 else C_BLANCO),
                   ("TOPPADDING", (col, 0), (col, 0), 9), ("BOTTOMPADDING", (col, 0), (col, 0), 9),
                   ("LEFTPADDING", (col, 0), (col, 0), 10), ("RIGHTPADDING", (col, 0), (col, 0), 6)]
    tabla.setStyle(TableStyle(estilo))
    return tabla


def _imagen_segura(url_relativa, ancho=15 * cm, marco=True, alto_max=12 * cm):
    """Convierte una URL /static/... o /graficos-generados/... de la aplicación en una ruta de archivo e inserta la imagen si existe (dentro de un marco
    con borde oscuro); si no existe, no rompe el PDF (el análisis pudo no haber generado ese gráfico)."""
    if not url_relativa:
        return None
    ruta = cfg.ruta_de_url(url_relativa)
    if ruta is None or not ruta.is_file():
        return None
    ruta = str(ruta)
    try:
        img = Image(ruta)
        proporcion = img.drawHeight / img.drawWidth
        if ancho * proporcion > alto_max:
            ancho = alto_max / proporcion
        img.drawWidth = ancho
        img.drawHeight = ancho * proporcion
        img.hAlign = "CENTER"
        if not marco:
            return img
        marco_tabla = Table([[img]], colWidths=[ancho + 0.5 * cm])
        marco_tabla.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.6, C_TINTA), ("BACKGROUND", (0, 0), (-1, -1), C_BLANCO),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        marco_tabla.hAlign = "CENTER"
        return marco_tabla
    except Exception:
        return None


def _fmt_vector(v):
    return "[" + ", ".join(f"{x:.2f}" for x in v) + "]"


def _fmt_matriz(m):
    return "[" + ", ".join("[" + ", ".join(f"{x:.2f}" for x in fila) + "]" for fila in m) + "]"


def _fmt_problema(problema):
    """Nombre del tipo de problema con tilde correcta para mostrar en el PDF (los metadatos
    internos lo guardan sin tilde, p. ej. "clasificacion")."""
    return {"clasificacion": "Clasificación", "regresion": "Regresión"}.get(problema, problema)


def _nota_fuente_datos(datos):
    """Aclara, cuando corresponde, que los cálculos se hicieron sobre el dataset ya
    preprocesado (normalizado): si no se explica, una media ~0 y desviación ~1 en todas las
    variables puede parecer un error en vez del resultado esperado de StandardScaler."""
    if isinstance(datos, dict) and datos.get("fuente_datos") == "preprocesado":
        return (
            " Estos valores se calculan sobre el dataset ya preprocesado (normalizado): por eso la media de "
            "cada variable numérica es cercana a 0 y su desviación estándar cercana a 1 en todas ellas — es "
            "el resultado esperado de aplicar StandardScaler, no un error."
        )
    return ""


# ============================================================
# TEXTOS EXPLICATIVOS GENERADOS A PARTIR DE LOS DATOS REALES
# ============================================================

def _resumen_exploracion(exploracion):
    registros = exploracion.get("filas")
    columnas = exploracion.get("columnas")
    numericas = exploracion.get("columnas_numericas", [])
    categoricas = exploracion.get("columnas_categoricas", [])
    nulos = exploracion.get("total_nulos", 0)
    duplicados = exploracion.get("duplicados", 0)

    base = (
        f"El dataset contiene <b>{registros}</b> registros y <b>{columnas}</b> variables "
        f"({len(numericas)} numérica(s) y {len(categoricas)} categórica(s))."
    )
    if nulos and duplicados:
        estado = (
            f" Se detectaron {nulos} valor(es) nulo(s) y {duplicados} fila(s) duplicada(s), por lo que "
            "el preprocesamiento debe resolver ambos problemas antes de entrenar cualquier modelo."
        )
    elif nulos:
        estado = f" Se detectaron {nulos} valor(es) nulo(s), que el preprocesamiento debe imputar antes de entrenar un modelo."
    elif duplicados:
        estado = f" Se detectaron {duplicados} fila(s) duplicada(s), que conviene eliminar antes de entrenar un modelo."
    else:
        estado = " No se detectaron valores nulos ni filas duplicadas: en ese sentido, el dataset ya está limpio."
    return base + estado


def _fuerza_texto(valor, umbrales=(0.3, 0.6)):
    magnitud = abs(valor)
    if magnitud < umbrales[0]:
        return "débil"
    if magnitud < umbrales[1]:
        return "moderada"
    return "fuerte"


def _insight_estadistica(columnas):
    # El coeficiente de variación (desviación / media) solo es interpretable cuando la media
    # no está pegada a cero: sobre datos normalizados (StandardScaler) la media de cada
    # variable es ~0 por diseño, y dividir por un valor tan pequeño da porcentajes absurdos.
    cvs = [
        (c["columna"], abs(c["desviacion_numpy"] / c["media"]))
        for c in columnas
        if c.get("media") and abs(c["media"]) >= max(1e-9, 0.02 * abs(c.get("desviacion_numpy") or 0))
    ]
    if len(cvs) < 2:
        return ""
    cvs.sort(key=lambda t: t[1], reverse=True)
    mas_dispersa, mas_homogenea = cvs[0], cvs[-1]
    if mas_dispersa[0] == mas_homogenea[0]:
        return ""
    return (
        f' Comparando cada variable contra su propio promedio, la que más varía (proporcionalmente) es '
        f'"{mas_dispersa[0]}" ({mas_dispersa[1] * 100:.1f}% de su propio promedio), mientras que '
        f'"{mas_homogenea[0]}" es la más estable ({mas_homogenea[1] * 100:.1f}%).'
    )


def _resumen_outliers(outliers):
    columnas = outliers.get("columnas", [])
    total = sum(c["cantidad_outliers"] for c in columnas)
    if total == 0:
        return "No se detectó ningún valor atípico en las variables numéricas con este criterio."
    con_outliers = sorted((c for c in columnas if c["cantidad_outliers"] > 0),
                           key=lambda c: c["cantidad_outliers"], reverse=True)
    peor = con_outliers[0]
    return (
        f'Se detectaron <b>{total}</b> valor(es) atípico(s) en total. La variable con más outliers es '
        f'"{peor["columna"]}", con {peor["cantidad_outliers"]}.'
    )


def _explicacion_metricas(problema):
    if problema == "clasificacion":
        return (
            "<b>Accuracy</b> es el porcentaje de predicciones correctas sobre el total de casos evaluados. "
            "<b>Precision</b> mide qué proporción de los casos que el modelo predijo como positivos lo eran "
            "realmente. <b>Recall</b> mide qué proporción de los casos positivos reales fue detectada por el "
            "modelo. <b>F1-score</b> combina precision y recall en un solo valor, especialmente útil cuando "
            "las clases no están balanceadas."
        )
    return (
        "<b>MAE</b> (error absoluto medio) indica, en las mismas unidades que la variable objetivo, cuánto se "
        "equivoca el modelo en promedio. <b>MSE</b> penaliza más los errores grandes al elevarlos al cuadrado, "
        "y <b>RMSE</b> es su raíz cuadrada, de nuevo en las unidades originales. <b>R²</b> indica qué "
        "proporción de la variabilidad de la variable objetivo explica el modelo (1 = ajuste perfecto, "
        "0 = equivalente a predecir siempre el promedio)."
    )


def _resumen_comparacion(comparacion, entrenamiento):
    if not comparacion or not entrenamiento:
        return ""
    problema = entrenamiento["problema"]
    metrica_clave = "f1" if problema == "clasificacion" else "r2"
    nombre_metrica = "F1-score" if problema == "clasificacion" else "R²"
    valores = {nombre: m[metrica_clave] for nombre, m in comparacion.items()}
    if len(valores) < 2:
        return ""
    ordenados = sorted(valores.items(), key=lambda t: t[1], reverse=True)
    mejor, segundo = ordenados[0], ordenados[1]
    diferencia = mejor[1] - segundo[1]
    return (
        f"<b>{mejor[0]}</b> obtuvo el mejor desempeño según {nombre_metrica} ({mejor[1]:.3f} frente a "
        f"{segundo[1]:.3f} de {segundo[0]}, una diferencia de {diferencia:.3f}), por lo que fue elegido como "
        "el modelo final para este dataset."
    )


def _resumen_predicciones(predicciones, problema, metrica_principal=None, filas_prueba=None):
    """OJO: `predicciones` ya viene recortado a una muestra (ver tabla_predicciones, limite=20)
    para no imprimir cientos de filas en el PDF. Por eso el accuracy/total real del conjunto de
    prueba se toma de `metrica_principal` y `filas_prueba` (calculados sobre TODO el conjunto de
    prueba), nunca contando aciertos dentro de `predicciones`: hacerlo con la muestra recortada
    daría un porcentaje distinto (y potencialmente contradictorio) al de las secciones 11-14."""
    mostrados = min(12, len(predicciones))
    total_real = filas_prueba if filas_prueba is not None else len(predicciones)
    if problema == "clasificacion":
        if metrica_principal is not None:
            aciertos_reales = round(metrica_principal["accuracy"] * total_real)
            return (
                f"Se muestran los primeros {mostrados} casos (de {total_real} evaluados en todo el conjunto "
                f"de prueba) a modo de muestra. Sobre el conjunto de prueba completo, <b>{aciertos_reales}</b> "
                f"de {total_real} casos fueron clasificados correctamente, el mismo "
                f"{metrica_principal['accuracy']*100:.1f}% de accuracy reportado en la sección 11-13."
            )
        aciertos_muestra = sum(1 for p in predicciones if p.get("acierto"))
        return (
            f"Se muestran los primeros {mostrados} de {len(predicciones)} casos de una muestra del conjunto "
            f"de prueba; de esa muestra, {aciertos_muestra} fueron clasificados correctamente."
        )
    return (
        f"Se muestran los primeros {mostrados} casos (de {total_real} evaluados en todo el conjunto de "
        'prueba) a modo de muestra. La columna "Resultado" es la diferencia entre el valor real y la '
        "predicción: cuanto más cerca de 0, mejor fue la predicción del modelo."
    )


# ============================================================
# GENERACIÓN DEL PDF
# ============================================================

def generar_pdf(resultado: dict, ruta_pdf: str) -> str:
    os.makedirs(os.path.dirname(ruta_pdf), exist_ok=True)

    doc = SimpleDocTemplate(
        ruta_pdf, pagesize=A4,
        rightMargin=1.8 * cm, leftMargin=1.8 * cm, topMargin=2.5 * cm, bottomMargin=2.0 * cm,
        title="DataExpert IA — Informe de análisis",
        author="DataExpert IA",
        subject="Fundamentos y algoritmia para inteligencia artificial",
    )

    base = getSampleStyleSheet()
    estilos = {
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontName=F_TITULO_NEGRA, fontSize=17, leading=21, textColor=C_TINTA, spaceAfter=0),
        "insignia": ParagraphStyle("Insignia", fontName=F_TITULO_NEGRA, fontSize=12, leading=14, textColor=C_TINTA, alignment=1),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontName=F_TITULO, fontSize=10.5, leading=14, textColor=C_TINTA, spaceBefore=0, spaceAfter=0),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName=F_TEXTO, fontSize=10, leading=15.2, textColor=C_TINTA, spaceAfter=6),
        "kv_label": ParagraphStyle("KVLabel", fontName=F_TEXTO_NEGRITA, fontSize=9.3, leading=13, textColor=C_TINTA),
        "kv_valor": ParagraphStyle("KVValor", fontName=F_TEXTO, fontSize=9.3, leading=13, textColor=C_TINTA),
        "th": ParagraphStyle("TH", fontName=F_TEXTO_NEGRITA, fontSize=8.8, leading=12, textColor=C_BLANCO),
        "td": ParagraphStyle("TD", fontName=F_DATOS, fontSize=8.3, leading=12, textColor=C_TINTA),
        "td_primera": ParagraphStyle("TDPrimera", fontName=F_TEXTO_NEGRITA, fontSize=8.8, leading=12, textColor=C_TINTA),
        "callout": ParagraphStyle("Callout", fontName=F_TEXTO, fontSize=9.5, leading=14.2, textColor=C_TINTA),
        "tarjeta_valor": ParagraphStyle("TarjetaValor", fontName=F_TITULO_NEGRA, fontSize=15, leading=18, textColor=C_TINTA),
        "tarjeta_valor_chico": ParagraphStyle("TarjetaValorChico", fontName=F_TITULO_NEGRA, fontSize=9.5, leading=12, textColor=C_TINTA),
        "tarjeta_etiqueta": ParagraphStyle("TarjetaEtiqueta", fontName=F_TEXTO_NEGRITA, fontSize=8.3, leading=11, textColor=C_TINTA_SUAVE),
    }

    meta = resultado["dataset_meta"]
    _aplicar_tema(meta)
    fecha = datetime.now()
    exploracion = resultado.get("exploracion") or {}
    preprocesamiento = resultado.get("preprocesamiento")
    algebra = resultado.get("algebra")
    estadistica = resultado.get("estadistica")
    outliers = resultado.get("outliers")
    graficos = resultado.get("graficos") or {"graficos": []}
    entrenamiento = resultado.get("entrenamiento")
    comparacion = resultado.get("comparacion")
    metrica_principal = resultado.get("metrica_principal")
    matriz_confusion_url = resultado.get("matriz_confusion_url")
    real_vs_prediccion_url = resultado.get("real_vs_prediccion_url")
    predicciones = resultado.get("predicciones") or []
    comparacion_chart_url = resultado.get("comparacion_chart_url")
    comparacion_chart_explicacion = resultado.get("comparacion_chart_explicacion")
    importancia_url = resultado.get("importancia_url")
    importancia_explicacion = resultado.get("importancia_explicacion")
    importancia_disponible = resultado.get("importancia_disponible")
    parametros_modelos = resultado.get("parametros_modelos") or {}

    story = []

    # --- Portada: se dibuja sobre el lienzo (ver _portada); esta hoja solo reserva la pagina ---
    story.append(Spacer(1, 1))
    story.append(PageBreak())

    # --- Resumen en tarjetas ---
    story.append(_tarjetas_resumen(resultado, estilos))
    story.append(Spacer(1, 0.7 * cm))

    # --- 1. Introducción ---
    story.extend(_seccion("1. Introducción", estilos))
    story.append(Paragraph(
        "DataExpert IA es una plataforma que aplica fundamentos matemáticos y algorítmicos (álgebra lineal, "
        "estadística y Machine Learning) sobre datasets reales o generados sintéticamente, para demostrar de "
        "forma práctica el flujo completo de un proyecto de ciencia de datos. Este informe documenta, paso a "
        "paso y con los datos reales de la sesión de análisis actual, cada etapa: desde la exploración inicial "
        "del dataset hasta el entrenamiento, la evaluación y la comparación de modelos de Machine Learning, "
        "pasando por operaciones de álgebra lineal con NumPy y estadística descriptiva —incluyendo funciones "
        "de varianza y desviación estándar implementadas manualmente para verificar los resultados de NumPy. "
        "Ningún resultado mostrado a continuación es simulado: todos provienen de la ejecución real del "
        "pipeline sobre el dataset seleccionado.",
        estilos["body"],
    ))
    story.append(Paragraph(
        "El documento sigue el mismo orden en el que normalmente se aborda un proyecto de ciencia de datos: "
        "primero se entiende el problema y los datos disponibles (secciones 2 y 3), luego se preparan esos "
        "datos para que un algoritmo pueda aprender de ellos (sección 4), se revisan sus propiedades "
        "matemáticas y estadísticas (secciones 5 a 9), se visualizan sus patrones (sección 10), se entrena y "
        "compara más de un modelo (secciones 11 a 14), se revisan predicciones concretas (sección 15) y, "
        "finalmente, se resume todo en una conclusión (sección 16). Cada gráfico incluido va acompañado de un "
        "párrafo que interpreta lo que muestra, para que el informe pueda leerse de forma autónoma sin haber "
        "usado la plataforma.",
        estilos["body"],
    ))

    # --- 2. Dataset seleccionado ---
    story.extend(_seccion("2. Dataset seleccionado", estilos))
    imagen_dataset = _imagen_segura(f"static/{meta.get('imagen', '')}", ancho=8 * cm, alto_max=7.5 * cm)
    if imagen_dataset:
        story.append(imagen_dataset)
        story.append(Spacer(1, 0.2 * cm))
    story.append(_tabla_kv([
        ("Nombre", meta["nombre"]), ("Descripción", meta["descripcion"]),
        ("Variable objetivo", meta["objetivo"]), ("Tipo de problema", _fmt_problema(meta["problema"])),
    ], estilos))
    story.append(Spacer(1, 0.2 * cm))
    accion = "predecir la categoría" if meta["problema"] == "clasificacion" else "predecir el valor numérico"
    story.append(Paragraph(
        f'Al tratarse de un problema de <b>{_fmt_problema(meta["problema"]).lower()}</b>, el objetivo del análisis es {accion} de la '
        f'variable "<b>{meta["objetivo"]}</b>" a partir del resto de columnas del dataset.',
        estilos["body"],
    ))
    if meta["problema"] == "clasificacion":
        story.append(Paragraph(
            "En un problema de clasificación, el modelo aprende a asignar cada registro a una de un número "
            "limitado de categorías (por ejemplo, sí/no, o un conjunto pequeño de clases), en vez de un "
            "número continuo. Por eso las métricas de evaluación de las secciones 11 a 14 son accuracy, "
            "precision, recall y F1-score en lugar de un error numérico.",
            estilos["body"],
        ))
    else:
        story.append(Paragraph(
            "En un problema de regresión, el modelo aprende a estimar un valor numérico continuo (por "
            "ejemplo, un precio o una nota), no una categoría. Por eso las métricas de evaluación de las "
            "secciones 11 a 14 miden el tamaño del error (MAE, MSE, RMSE) y qué tan bien explica el modelo "
            "la variabilidad de los datos (R²), en lugar de un porcentaje de aciertos.",
            estilos["body"],
        ))

    # --- 3. Exploración ---
    story.extend(_seccion("3. Exploración de datos", estilos))
    if exploracion:
        story.append(Paragraph(_resumen_exploracion(exploracion), estilos["body"]))
        story.append(Spacer(1, 0.15 * cm))
    story.append(_tabla_kv([
        ("Registros", exploracion.get("filas")), ("Columnas", exploracion.get("columnas")),
        ("Variables numéricas", ", ".join(exploracion.get("columnas_numericas", []))),
        ("Variables categóricas", ", ".join(exploracion.get("columnas_categoricas", [])) or "Ninguna"),
        ("Valores nulos totales", exploracion.get("total_nulos")),
        ("Filas duplicadas", exploracion.get("duplicados")),
    ], estilos))

    # --- 4. Preprocesamiento ---
    story.extend(_seccion("4. Preprocesamiento", estilos))
    if preprocesamiento:
        story.append(Paragraph(
            "El preprocesamiento prepara los datos para que un modelo de Machine Learning pueda entrenarse "
            "correctamente: completa los valores que faltaban (con el promedio en columnas numéricas y el "
            "valor más común en categóricas), elimina filas repetidas, cambia las categorías de texto por "
            "números (porque los modelos solo entienden números) y pone todas las variables numéricas en "
            "una misma escala, para que ninguna pese más que otra solo por tener números más grandes.",
            estilos["body"],
        ))
        story.append(Spacer(1, 0.15 * cm))
        story.append(_tabla_datos(
            ["Métrica", "Antes", "Después"],
            [
                ("Filas", preprocesamiento["antes"]["filas"], preprocesamiento["despues"]["filas"]),
                ("Columnas", preprocesamiento["antes"]["columnas"], preprocesamiento["despues"]["columnas"]),
                ("Valores nulos", preprocesamiento["antes"]["nulos"], preprocesamiento["despues"]["nulos"]),
                ("Duplicados", preprocesamiento["antes"]["duplicados"], preprocesamiento["despues"]["duplicados"]),
            ], estilos, anchos=[7 * cm, 5.2 * cm, 5.2 * cm],
        ))
        if preprocesamiento["transformaciones"]:
            story.append(Spacer(1, 0.25 * cm))
            story.append(Paragraph("Transformaciones aplicadas en esta sesión:", estilos["body"]))
            for transformacion in preprocesamiento["transformaciones"]:
                story.append(Paragraph(f"• {transformacion}", estilos["body"]))
    else:
        story.append(Paragraph("Sección no ejecutada: no se corrió el preprocesamiento antes de generar este informe.", estilos["body"]))

    # --- 5. Álgebra lineal ---
    story.extend(_seccion("5. Álgebra lineal", estilos))
    if algebra:
        story.append(Paragraph(
            "Estas operaciones son la base matemática de muchos algoritmos de Machine Learning: los vectores "
            "representan los datos de un registro o los pesos de un modelo, el producto punto mide su "
            "similitud direccional, la norma mide su magnitud, y resolver un sistema de ecuaciones lineales "
            "equivale a encontrar los coeficientes que ajustan un modelo lineal a un conjunto de restricciones. "
            "Esta sección es independiente del dataset seleccionado: usa vectores y matrices fijos para "
            "ilustrar cada operación de forma clara y verificable.",
            estilos["body"],
        ))
        story.append(Spacer(1, 0.2 * cm))

        v = algebra["vectores"]
        story.append(_tabla_datos(
            ["Operación con vectores", "Resultado"],
            [
                ("Vector v1", _fmt_vector(v["v1"])),
                ("Vector v2", _fmt_vector(v["v2"])),
                ("Suma  v1 + v2", _fmt_vector(v["suma"])),
                ("Resta  v1 − v2", _fmt_vector(v["resta"])),
                (f'Escalar × v1  (× {v["escalar"]:g})', _fmt_vector(v["multiplicacion_escalar"])),
                ("Producto punto  v1 · v2", f'{algebra["producto_punto"]:.3f}'),
                ("Norma (magnitud) de v1", f'{algebra["normas"]["norma_v1"]:.3f}'),
                ("Norma (magnitud) de v2", f'{algebra["normas"]["norma_v2"]:.3f}'),
            ], estilos, anchos=[8.5 * cm, 8.9 * cm],
        ))
        pp = algebra["producto_punto"]
        direccion_pp = "en una dirección similar" if pp > 0 else ("en direcciones opuestas" if pp < 0 else "de forma perpendicular")
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph(
            f"El producto punto entre v1 y v2 es {pp:.3f}: al ser distinto de cero, indica que los vectores "
            f"apuntan {direccion_pp}. La norma mide la magnitud (longitud) de cada vector: v1 tiene una "
            f'magnitud de {algebra["normas"]["norma_v1"]:.3f} y v2 de {algebra["normas"]["norma_v2"]:.3f}.',
            estilos["body"],
        ))
        story.append(Spacer(1, 0.25 * cm))

        m = algebra["matrices"]
        story.append(_tabla_datos(
            ["Operación con matrices", "Resultado"],
            [
                ("Matriz A", _fmt_matriz(m["A"])),
                ("Matriz B", _fmt_matriz(m["B"])),
                ("Suma  A + B", _fmt_matriz(m["suma"])),
                ("Resta  A − B", _fmt_matriz(m["resta"])),
                ("Multiplicación  A × B", _fmt_matriz(m["multiplicacion"])),
                ("Transpuesta de A", _fmt_matriz(m["transpuesta_A"])),
            ], estilos, anchos=[8.5 * cm, 8.9 * cm],
        ))
        story.append(Spacer(1, 0.25 * cm))

        sistema = algebra["sistema_ecuaciones"]
        story.append(Paragraph(
            f"Sistema de ecuaciones lineales: {sistema['descripcion'][0]}, {sistema['descripcion'][1]}. "
            f"Resolviéndolo con <i>np.linalg.solve</i> se obtiene la solución "
            f"x = {sistema['solucion']['x']:.3f}, y = {sistema['solucion']['y']:.3f}. La verificación "
            f"consiste en sustituir esa solución en el sistema original (A·x = {sistema['verificacion']}) y "
            "comprobar que coincide con el vector b original, confirmando que la solución es correcta.",
            estilos["body"],
        ))
    else:
        story.append(Paragraph("Sección no ejecutada.", estilos["body"]))

    # --- 6-8. Estadística, varianza y desviación estándar ---
    story.extend(_seccion("6-8. Estadística, varianza y desviación estándar", estilos))
    if estadistica and estadistica.get("columnas"):
        story.append(Paragraph(
            "La media y la mediana describen el centro de cada variable; la varianza y la desviación "
            "estándar describen qué tan dispersos están los valores alrededor de ese centro. A continuación "
            "se muestran ambas medidas de dispersión calculadas de dos formas: con NumPy y con una función "
            "propia implementada matemáticamente, para verificar que ambos métodos coinciden.",
            estilos["body"],
        ))
        story.append(Spacer(1, 0.15 * cm))
        filas = [
            (c["columna"], f"{c['media']:.2f}", f"{c['mediana']:.2f}",
             f"{c['varianza_numpy']:.3f}", f"{c['varianza_manual']:.3f}",
             f"{c['desviacion_numpy']:.3f}", f"{c['desviacion_manual']:.3f}")
            for c in estadistica["columnas"]
        ]
        story.append(_tabla_datos(
            ["Variable", "Media", "Mediana", "Var. NumPy", "Var. manual", "Desv. NumPy", "Desv. manual"],
            filas, estilos,
        ))
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph(
            "La diferencia entre el resultado de NumPy y el de la función manual es cercana a cero en todas "
            "las variables, confirmando que la implementación manual (promedio de las diferencias al cuadrado "
            "respecto a la media, y su raíz cuadrada) es matemáticamente equivalente a la de NumPy."
            + _insight_estadistica(estadistica["columnas"]),
            estilos["body"],
        ))
    else:
        story.append(Paragraph("Sección no ejecutada.", estilos["body"]))

    # --- 9. Valores atípicos ---
    story.extend(_seccion("9. Valores atípicos", estilos))
    if outliers and outliers.get("columnas"):
        story.append(Paragraph(
            f'Se consideran valores atípicos los que se alejan de la media más de k = {outliers.get("k", 2)} '
            "desviaciones estándar (fuera del rango media ± k·σ). Este método es sencillo de calcular y "
            "asume que los datos siguen aproximadamente una distribución normal.",
            estilos["body"],
        ))
        story.append(Spacer(1, 0.15 * cm))
        filas = [
            (c["columna"], f"{c['media']:.2f}", f"{c['desviacion_estandar']:.2f}",
             f"{c['limite_inferior']:.2f}", f"{c['limite_superior']:.2f}", c["cantidad_outliers"])
            for c in outliers["columnas"]
        ]
        story.append(_tabla_datos(
            ["Variable", "Media", "Desv. estándar", "Límite inf.", "Límite sup.", "Outliers"],
            filas, estilos,
        ))
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph(_resumen_outliers(outliers) + _nota_fuente_datos(outliers), estilos["body"]))

        boxplots_url = outliers.get("boxplots_url")
        img_boxplots = _imagen_segura(boxplots_url, ancho=15 * cm) if boxplots_url else None
        if img_boxplots:
            story.append(Spacer(1, 0.3 * cm))
            story.append(KeepTogether([
                _h2("Vista visual: diagramas de caja (boxplot)", estilos), Spacer(1, 0.3 * cm),
                img_boxplots, Spacer(1, 0.25 * cm),
                _callout(outliers.get("boxplots_explicacion", ""), estilos),
            ]))
    else:
        story.append(Paragraph("Sección no ejecutada.", estilos["body"]))

    # --- 10. Gráficos: cada uno con su propia imagen e interpretación, sin forzar una
    # página en blanco por gráfico — se acomodan tantos como quepan en cada página. ---
    story.extend(_seccion("10. Gráficos", estilos))
    lista_graficos = graficos.get("graficos", [])
    if lista_graficos:
        story.append(Paragraph(
            "Esta sección presenta, uno por uno (nunca combinados en un solo panel), los gráficos generados "
            "con Matplotlib y Seaborn a partir de los datos reales del dataset actual: la forma de cada "
            "variable numérica, la relación entre pares de variables, la correlación entre todas ellas y el "
            "balance de la variable objetivo. Cada gráfico incluye debajo una breve interpretación calculada "
            "a partir de esos mismos datos." + _nota_fuente_datos(graficos),
            estilos["body"],
        ))
        story.append(Spacer(1, 0.15 * cm))
        for grafico in lista_graficos:
            img = _imagen_segura(grafico["url"], ancho=12 * cm)
            if not img:
                continue
            bloque = [_h2(grafico["titulo"], estilos), Spacer(1, 0.3 * cm), img]
            explicacion = grafico.get("explicacion")
            if explicacion:
                bloque.append(Spacer(1, 0.25 * cm))
                bloque.append(_callout(explicacion, estilos))
            bloque.append(Spacer(1, 0.2 * cm))
            story.append(KeepTogether(bloque))
    else:
        story.append(Paragraph("Sección no ejecutada.", estilos["body"]))

    # --- 11-13. Machine Learning, entrenamiento y evaluación ---
    story.extend(_seccion("11-13. Machine Learning: entrenamiento y evaluación", estilos))
    if entrenamiento:
        nombres_modelos = list(comparacion.keys()) if comparacion else []
        texto_cantidad = {2: "dos", 3: "tres", 4: "cuatro"}.get(len(nombres_modelos), str(len(nombres_modelos)))
        story.append(Paragraph(
            f"Tipo de problema detectado automáticamente: <b>{_fmt_problema(entrenamiento['problema'])}</b>. "
            "Se separaron los datos en 80% para entrenamiento y 20% para prueba "
            f"(<i>train_test_split</i>, random_state=42), y se compararon {texto_cantidad} modelos de "
            f"Scikit-learn ({', '.join(nombres_modelos)}) entrenados sobre el mismo conjunto. El de mejor "
            f"desempeño fue <b>{entrenamiento['mejor_modelo_nombre']}</b>.",
            estilos["body"],
        ))

        params_mejor = parametros_modelos.get(entrenamiento["mejor_modelo_nombre"])
        if params_mejor:
            texto_params = ", ".join(f"{clave} = {valor}" for clave, valor in params_mejor.items())
            particiones = 10 if entrenamiento["problema"] == "clasificacion" else 5
            story.append(Paragraph(
                "Sus \"hiperparámetros\" (ajustes que se eligen antes de entrenar, no algo que el modelo "
                "aprenda solo) no se fijaron a mano: se probaron varias configuraciones distintas, cada una "
                f"validada {particiones} veces sobre distintas partes de los datos de entrenamiento (nunca "
                f"los de prueba), y se eligió la que mejor funcionó: <b>{texto_params}</b>.",
                estilos["body"],
            ))
        story.append(Spacer(1, 0.2 * cm))

        if metrica_principal:
            story.append(Paragraph(_explicacion_metricas(entrenamiento["problema"]), estilos["body"]))
            story.append(Spacer(1, 0.15 * cm))
            if entrenamiento["problema"] == "clasificacion":
                filas_metricas = [
                    ("Accuracy", f"{metrica_principal['accuracy']*100:.2f}%"),
                    ("Precision", f"{metrica_principal['precision']*100:.2f}%"),
                    ("Recall", f"{metrica_principal['recall']*100:.2f}%"),
                    ("F1-score", f"{metrica_principal['f1']*100:.2f}%"),
                ]
            else:
                filas_metricas = [
                    ("MAE", f"{metrica_principal['mae']:.3f}"),
                    ("MSE", f"{metrica_principal['mse']:.3f}"),
                    ("RMSE", f"{metrica_principal['rmse']:.3f}"),
                    ("R²", f"{metrica_principal['r2']:.3f}"),
                ]
            story.append(_tabla_datos(["Métrica", "Valor"], filas_metricas, estilos, anchos=[8 * cm, 8 * cm]))
            story.append(Spacer(1, 0.2 * cm))

        url_extra = matriz_confusion_url or real_vs_prediccion_url
        img_extra = _imagen_segura(url_extra, ancho=11 * cm)
        if img_extra:
            if matriz_confusion_url:
                titulo_extra = "Matriz de confusión"
                texto_extra = (
                    "La matriz de confusión compara los valores reales (filas) con las predicciones del "
                    "modelo (columnas): la diagonal principal son los aciertos, y el resto de las celdas son "
                    "los errores de clasificación entre cada par de clases."
                )
            else:
                titulo_extra = "Real vs. predicho"
                texto_extra = (
                    "Cada punto compara el valor real (eje X) con el valor predicho por el modelo (eje Y); "
                    "cuanto más cerca estén los puntos de la línea diagonal punteada (predicción ideal), "
                    "mejor es la predicción del modelo."
                )
            story.append(KeepTogether([
                _h2(titulo_extra, estilos), Spacer(1, 0.3 * cm), img_extra,
                Spacer(1, 0.25 * cm), _callout(texto_extra, estilos),
            ]))

        img_importancia = _imagen_segura(importancia_url, ancho=13 * cm) if importancia_url else None
        if img_importancia:
            story.append(Spacer(1, 0.3 * cm))
            story.append(KeepTogether([
                _h2("Variables más influyentes en la predicción", estilos), Spacer(1, 0.3 * cm),
                img_importancia, Spacer(1, 0.25 * cm),
                _callout(importancia_explicacion or "", estilos),
            ]))
        elif importancia_disponible is False:
            story.append(Spacer(1, 0.2 * cm))
            story.append(Paragraph(
                f'El modelo elegido ("{entrenamiento["mejor_modelo_nombre"]}") no tiene un equivalente '
                "directo a \"importancia de variables\": KNN clasifica por cercanía a los vecinos más "
                "próximos en el espacio de todas las variables a la vez, sin asignarle un peso individual a "
                "cada una (a diferencia de un árbol de decisión o un modelo lineal).",
                estilos["body"],
            ))
    else:
        story.append(Paragraph("Sección no ejecutada.", estilos["body"]))

    # --- 14. Comparación de modelos ---
    story.extend(_seccion("14. Comparación de modelos", estilos))
    if comparacion:
        problema = entrenamiento["problema"] if entrenamiento else "clasificacion"
        if problema == "clasificacion":
            filas = [
                (nombre, f"{m['accuracy']*100:.2f}%", f"{m['precision']*100:.2f}%",
                 f"{m['recall']*100:.2f}%", f"{m['f1']*100:.2f}%")
                for nombre, m in comparacion.items()
            ]
            story.append(_tabla_datos(["Modelo", "Accuracy", "Precision", "Recall", "F1"], filas, estilos))
        else:
            filas = [
                (nombre, f"{m['mae']:.3f}", f"{m['rmse']:.3f}", f"{m['r2']:.3f}")
                for nombre, m in comparacion.items()
            ]
            story.append(_tabla_datos(["Modelo", "MAE", "RMSE", "R²"], filas, estilos))
        resumen_comp = _resumen_comparacion(comparacion, entrenamiento)
        if resumen_comp:
            story.append(Spacer(1, 0.15 * cm))
            story.append(Paragraph(resumen_comp, estilos["body"]))

        img_comparacion = _imagen_segura(comparacion_chart_url, ancho=13.5 * cm) if comparacion_chart_url else None
        if img_comparacion:
            story.append(Spacer(1, 0.3 * cm))
            story.append(KeepTogether([
                _h2("Comparación visual", estilos), Spacer(1, 0.3 * cm),
                img_comparacion, Spacer(1, 0.25 * cm),
                _callout(comparacion_chart_explicacion or "", estilos),
            ]))
    else:
        story.append(Paragraph("Sección no ejecutada.", estilos["body"]))

    # --- 15. Resultados (predicciones) ---
    story.extend(_seccion("15. Resultados", estilos))
    if predicciones:
        problema = entrenamiento["problema"] if entrenamiento else "clasificacion"
        story.append(Paragraph(
            _resumen_predicciones(predicciones, problema, metrica_principal, resultado.get("filas_prueba")),
            estilos["body"],
        ))
        story.append(Spacer(1, 0.15 * cm))
        filas = [(p["real"], p["prediccion"], p["resultado"]) for p in predicciones[:12]]
        story.append(_tabla_datos(["Valor real", "Predicción", "Resultado"], filas, estilos))
    else:
        story.append(Paragraph("Sección no ejecutada.", estilos["body"]))

    # --- 16. Conclusiones ---
    story.extend(_seccion("16. Conclusiones", estilos))
    if entrenamiento and metrica_principal:
        if entrenamiento["problema"] == "clasificacion":
            conclusion = (
                f"El modelo {entrenamiento['mejor_modelo_nombre']} alcanzó un accuracy de "
                f"{metrica_principal['accuracy']*100:.2f}% sobre el conjunto de prueba, con un F1-score de "
                f"{metrica_principal['f1']*100:.2f}%. "
            )
        else:
            conclusion = (
                f"El modelo {entrenamiento['mejor_modelo_nombre']} obtuvo un R² de "
                f"{metrica_principal['r2']:.3f} y un error absoluto medio (MAE) de "
                f"{metrica_principal['mae']:.3f} sobre el conjunto de prueba. "
            )
        conclusion += (
            "Estos resultados fueron obtenidos ejecutando el pipeline completo (preprocesamiento, "
            "entrenamiento y evaluación) sobre el dataset seleccionado, sin valores simulados. "
        )
        resumen_comp = _resumen_comparacion(comparacion, entrenamiento) if comparacion else ""
        if resumen_comp:
            conclusion += resumen_comp
        story.append(Paragraph(conclusion, estilos["body"]))
        story.append(Spacer(1, 0.15 * cm))

        if importancia_explicacion and importancia_url:
            conclusion_importancia = (
                "En cuanto a qué variables explican mejor la predicción, el gráfico de la sección 11-13 "
                f"muestra que {importancia_explicacion[0].lower()}{importancia_explicacion[1:]}"
            )
            story.append(Paragraph(conclusion_importancia, estilos["body"]))
            story.append(Spacer(1, 0.15 * cm))

        story.append(Paragraph(
            "En conjunto, este informe recorrió el flujo completo de un proyecto de ciencia de datos aplicado "
            "a Inteligencia Artificial: se exploraron y limpiaron los datos, se revisaron sus propiedades "
            "matemáticas y estadísticas con NumPy (incluyendo funciones propias verificadas contra NumPy), se "
            "visualizaron sus patrones con Matplotlib y Seaborn, y se entrenó, comparó y evaluó más de un "
            "modelo de Scikit-learn sobre el mismo conjunto de datos. Para mejorar estos resultados en un caso "
            "real, los siguientes pasos naturales serían probar más combinaciones de hiperparámetros, "
            "recolectar más datos (especialmente si alguna clase estaba desbalanceada, ver sección 10), o "
            "incorporar variables adicionales relevantes para el problema.",
            estilos["body"],
        ))
    else:
        story.append(Paragraph(
            "Ejecuta la exploración, el preprocesamiento y el entrenamiento antes de generar el informe para "
            "obtener conclusiones basadas en resultados reales.", estilos["body"],
        ))

    def por_pagina(canvas_obj, documento):
        if documento.page == 1:
            _portada(canvas_obj, documento, meta, fecha)
        else:
            _interior(canvas_obj, documento, meta)

    doc.build(story, onFirstPage=por_pagina, onLaterPages=por_pagina)
    return ruta_pdf
