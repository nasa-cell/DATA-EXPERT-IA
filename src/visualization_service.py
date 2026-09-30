"""Genera los gráficos del análisis (histogramas, dispersión, correlación) con
Matplotlib y Seaborn, y los guarda como PNG en la carpeta de gráficos (static/graficos/<dataset>/ al ejecutar desde el código).

Cada gráfico se genera como una imagen independiente (uno por variable, no un panel
combinado) y viene acompañado de una explicación en texto calculada a partir de los
datos reales (forma de la distribución, fuerza de la correlación, balance de clases...),
para que el informe PDF pueda mostrar cada uno en su propia sección con contexto.
"""

import os
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
import numpy as np
import pandas as pd

from src import configuracion as cfg


GRAFICOS_DIR = str(cfg.GRAFICOS_DIR)

# Paleta categórica validada (contraste y daltonismo) y el mismo estilo que la página: tinta oscura, ejes limpios y rejilla suave.
PALETA = ["#e8590c", "#6c4dff", "#12a06a", "#0a84d6", "#d6336c", "#00a3a3", "#b58900"]
TINTA = "#14112b"
_CMAP_DIVERGENTE = LinearSegmentedColormap.from_list("divergente", ["#0a84d6", "#f4f3f8", "#e8590c"])  # dos tonos con gris al centro
_CMAP_SECUENCIAL = LinearSegmentedColormap.from_list("secuencial", ["#ffffff", "#0a84d6"])

sns.set_theme(style="whitegrid", palette=PALETA, rc={
    "figure.facecolor": "#ffffff", "axes.facecolor": "#ffffff", "axes.edgecolor": TINTA, "axes.linewidth": 1.6,
    "axes.labelcolor": TINTA, "text.color": TINTA, "xtick.color": TINTA, "ytick.color": TINTA,
    "grid.color": "#e6e3f2", "grid.linewidth": 1.0, "axes.titleweight": "bold", "axes.titlesize": 13,
    "axes.titlelocation": "left", "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 10.5, "legend.frameon": False, "axes.labelweight": "bold",
})


def _ruta(dataset: str, nombre: str) -> str:
    carpeta = os.path.join(GRAFICOS_DIR, dataset)
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, nombre)


def _url(dataset: str, nombre: str) -> str:
    return f"{cfg.URL_GRAFICOS}/{dataset}/{nombre}"


def _slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")


def _fuerza_correlacion(r: float) -> str:
    magnitud = abs(r)
    if magnitud < 0.3:
        return "débil"
    if magnitud < 0.6:
        return "moderada"
    return "fuerte"


def _explicacion_forma(skew: float) -> str:
    """Describe la forma de la distribución en lenguaje simple primero, y nombra el término
    técnico (asimetría) entre paréntesis para quien quiera profundizar, en vez de asumir que
    el lector ya sabe qué significa "sesgo" o "asimetría"."""
    if skew is None or (isinstance(skew, float) and np.isnan(skew)):
        return "no se pudo calcular bien su forma (hay pocos datos o casi todos son iguales)"
    if abs(skew) < 0.5:
        return "sus valores se reparten de forma bastante pareja a los dos lados del centro"
    lado = "altos" if skew > 0 else "bajos"
    cuanto = "algunos" if abs(skew) < 1 else "varios"
    return f'{cuanto} valores muy {lado} "estiran" la distribución hacia ese lado (asimetría)'


def _explicacion_histograma(columna: str, serie: pd.Series) -> str:
    media = float(serie.mean())
    mediana = float(serie.median())
    std = float(serie.std(ddof=0))
    skew = float(serie.skew()) if serie.shape[0] > 2 and std > 0 else float("nan")
    forma = _explicacion_forma(skew)

    # Usa el mismo umbral que _explicacion_forma (abs(skew) < 0.5) para decidir esta frase: antes
    # comparaba media/mediana contra un umbral aparte (0.05*std), lo que a veces daba una frase
    # sobre "coinciden" justo al lado de otra que decía "despareja" para el mismo dato.
    if np.isnan(skew) or abs(skew) < 0.5:
        relacion = "El promedio y el valor central están cerca uno del otro, lo cual va de la mano con esa forma pareja."
    else:
        relacion = "El promedio y el valor central no coinciden del todo, lo cual va de la mano con esa forma despareja."

    return (
        f'La variable "{columna}" tiene un promedio de {media:.2f} sobre {int(serie.shape[0])} datos '
        f"(la mitad de los casos queda por debajo de {mediana:.2f}, su valor central). En promedio, cada "
        f"dato se aleja de ese promedio en unas {std:.2f} unidades. En cuanto a su forma, {forma}. {relacion}"
    )


def generar_graficos(df: pd.DataFrame, dataset: str, objetivo: str = None, mapeo_objetivo: dict = None) -> dict:
    """`mapeo_objetivo` (id numérico -> nombre real de la clase) se pasa cuando el dataset ya
    fue preprocesado y el objetivo categórico quedó codificado con LabelEncoder: sin este
    mapeo, la leyenda y el eje de los gráficos mostrarían "0, 1, 2" en vez de los nombres
    reales de cada clase (p. ej. "setosa, versicolor, virginica")."""
    numericas = df.select_dtypes(include=[np.number]).columns.tolist()
    numericas = [c for c in numericas if c != objetivo][:6]  # máximo 6 para no saturar el informe

    # Version "para mostrar" del objetivo: mismos datos, pero con el nombre real de cada
    # clase en vez del código numérico que dejó el LabelEncoder, solo para leyendas y ejes
    # (los cálculos de correlación siguen usando la columna numérica original, sin tocar).
    etiquetas_objetivo = None
    if mapeo_objetivo and objetivo and objetivo in df.columns:
        etiquetas_objetivo = df[objetivo].map(mapeo_objetivo)

    graficos = []

    # --- Histogramas: una imagen independiente por variable numérica ---
    for i, columna in enumerate(numericas):
        serie = df[columna].dropna()
        if serie.empty:
            continue

        fig, ax = plt.subplots(figsize=(7.4, 4.3))
        sns.histplot(serie, kde=True, ax=ax, color=PALETA[i % len(PALETA)])
        ax.set_title(f"Distribución de {columna}")
        ax.set_xlabel(columna)
        ax.set_ylabel("Frecuencia")
        fig.tight_layout()
        nombre = f"histograma_{_slug(columna)}.png"
        fig.savefig(_ruta(dataset, nombre), dpi=130)
        plt.close(fig)

        graficos.append({
            "titulo": f"Histograma: distribución de {columna}",
            "url": _url(dataset, nombre),
            "explicacion": _explicacion_histograma(columna, serie),
        })

    # --- Dispersión (primeras 2 variables numéricas, coloreado por objetivo si existe) ---
    if len(numericas) >= 2:
        col_x, col_y = numericas[0], numericas[1]
        fig, ax = plt.subplots(figsize=(7.4, 5.6))
        coloreado_por_objetivo = bool(objetivo and objetivo in df.columns)
        # Si el objetivo es numérico continuo (regresión), una paleta de pocos colores fijos
        # se repite de forma ilegible sobre cientos de valores distintos: en ese caso se usa
        # un colormap continuo en vez de la lista discreta de colores de la marca.
        objetivo_continuo = coloreado_por_objetivo and pd.api.types.is_numeric_dtype(df[objetivo]) and df[objetivo].nunique() > 12
        if objetivo_continuo:
            sns.scatterplot(data=df, x=col_x, y=col_y, hue=objetivo, palette="viridis", ax=ax, alpha=0.8)
        elif coloreado_por_objetivo:
            hue_valores = etiquetas_objetivo if etiquetas_objetivo is not None else df[objetivo]
            sns.scatterplot(data=df, x=col_x, y=col_y, hue=hue_valores, palette=PALETA, ax=ax, alpha=0.8)
            ax.legend(title=objetivo)
        else:
            sns.scatterplot(data=df, x=col_x, y=col_y, color=PALETA[0], ax=ax, alpha=0.8)
        ax.set_title(f"{col_x} vs {col_y}")
        fig.tight_layout()
        nombre = "dispersion.png"
        fig.savefig(_ruta(dataset, nombre), dpi=130)
        plt.close(fig)

        r = float(df[[col_x, col_y]].corr().iloc[0, 1])
        fuerza = _fuerza_correlacion(r)
        direccion = "positiva (cuando una crece, la otra tiende a crecer)" if r >= 0 else "negativa (cuando una crece, la otra tiende a bajar)"
        texto_color = (
            f' Los puntos están coloreados según "{objetivo}" para ver si ese agrupamiento visual coincide '
            f"con alguna zona del gráfico."
            if coloreado_por_objetivo else ""
        )
        graficos.append({
            "titulo": f"Dispersión: {col_x} vs {col_y}",
            "url": _url(dataset, nombre),
            "explicacion": (
                f'Cada punto es un registro del dataset ubicado según sus valores de "{col_x}" (eje X) y '
                f'"{col_y}" (eje Y). Si los puntos forman una tendencia clara (una especie de línea), '
                f"significa que ambas variables están relacionadas; si se ven como una nube sin forma, no lo "
                f"están. Aquí esa relación (llamada correlación, un número de -1 a 1) es de {r:.3f}: una "
                f"relación {fuerza} y {direccion}.{texto_color}"
            ),
        })

    # --- Correlación (heatmap) ---
    if len(numericas) >= 2:
        objetivo_numerico = bool(objetivo and objetivo in df.columns and pd.api.types.is_numeric_dtype(df[objetivo]))
        columnas_corr = numericas + ([objetivo] if objetivo_numerico else [])
        matriz = df[columnas_corr].corr()
        fig, ax = plt.subplots(figsize=(1.1 * len(columnas_corr) + 2, 1.1 * len(columnas_corr) + 1))
        sns.heatmap(matriz, annot=True, fmt=".2f", cmap=_CMAP_DIVERGENTE, center=0, vmin=-1, vmax=1, linewidths=1.5, linecolor="#ffffff", ax=ax)
        ax.set_title("Matriz de correlación")
        fig.tight_layout()
        nombre = "correlacion.png"
        fig.savefig(_ruta(dataset, nombre), dpi=130)
        plt.close(fig)

        pares = [
            (columnas_corr[i], columnas_corr[j], float(matriz.iloc[i, j]))
            for i in range(len(columnas_corr)) for j in range(i + 1, len(columnas_corr))
        ]
        if pares:
            var_a, var_b, r_max = max(pares, key=lambda t: abs(t[2]))
            fuerza = _fuerza_correlacion(r_max)
            direccion = "positiva" if r_max >= 0 else "negativa"
            texto_par = (
                f'El par con la correlación más fuerte es "{var_a}" y "{var_b}" ({r_max:.3f}), una relación '
                f"{fuerza} y {direccion}."
            )
        else:
            texto_par = ""
        graficos.append({
            "titulo": "Matriz de correlación",
            "url": _url(dataset, nombre),
            "explicacion": (
                "Cada celda mide qué tan relacionadas están dos variables entre sí (correlación), con un "
                "número de -1 a 1: cerca de 1 significa que cuando una sube la otra también sube, cerca de "
                "-1 significa que cuando una sube la otra baja, y cerca de 0 significa que no hay relación "
                f"clara entre ellas. Los colores más intensos (rojo o azul fuerte) marcan las relaciones más "
                f"marcadas. {texto_par}"
            ),
        })

    # --- Distribución del objetivo (barra si es categórico, histograma si es numérico) ---
    if objetivo and objetivo in df.columns:
        if etiquetas_objetivo is not None:
            # Ya se sabe con certeza que es categorico (por eso existe un mapeo_objetivo):
            # se usan los nombres reales de cada clase en vez del codigo de LabelEncoder.
            serie_obj = etiquetas_objetivo.dropna()
            es_numerico_continuo = False
        else:
            serie_obj = df[objetivo].dropna()
            es_numerico_continuo = pd.api.types.is_numeric_dtype(serie_obj) and serie_obj.nunique() > 10

        fig, ax = plt.subplots(figsize=(6.8, 4.6))
        if es_numerico_continuo:
            sns.histplot(serie_obj, kde=True, ax=ax, color=PALETA[2])
            explicacion = _explicacion_histograma(objetivo, serie_obj)
        else:
            conteo = serie_obj.value_counts()
            conteo.plot(kind="bar", ax=ax, color=PALETA[:conteo.shape[0]])
            proporciones = (conteo / conteo.sum() * 100).round(1)
            clase_mayor, pct_mayor = proporciones.index[0], proporciones.iloc[0]
            clase_menor, pct_menor = proporciones.index[-1], proporciones.iloc[-1]
            balanceado = (pct_mayor - pct_menor) <= 20
            texto_balance = (
                "Las clases están relativamente balanceadas entre sí." if balanceado else
                "Hay un desbalance notable entre clases, lo que puede sesgar las métricas del modelo "
                "hacia la clase mayoritaria."
            )
            explicacion = (
                f'La variable objetivo "{objetivo}" tiene {conteo.shape[0]} categoría(s) distinta(s). La más '
                f'frecuente es "{clase_mayor}" ({pct_mayor:.1f}% de los registros) y la menos frecuente es '
                f'"{clase_menor}" ({pct_menor:.1f}%). {texto_balance}'
            )
        ax.set_title(f"Distribución de la variable objetivo: {objetivo}")
        fig.tight_layout()
        nombre = "distribucion_objetivo.png"
        fig.savefig(_ruta(dataset, nombre), dpi=130)
        plt.close(fig)

        graficos.append({
            "titulo": f"Distribución de la variable objetivo: {objetivo}",
            "url": _url(dataset, nombre),
            "explicacion": explicacion,
        })

    return {"graficos": graficos}


def generar_boxplots(df: pd.DataFrame, dataset: str, objetivo: str = None) -> dict:
    """Un panel con un diagrama de caja (boxplot) por variable numerica (hasta 6), para ver
    de un vistazo la mediana, los cuartiles y los valores atipicos de cada una: complementa
    la tabla de valores atipicos (media +/- k*sigma) con una vista visual del mismo tema."""
    numericas = df.select_dtypes(include=[np.number]).columns.tolist()
    numericas = [c for c in numericas if c != objetivo][:6]
    if not numericas:
        return {"url": None, "explicacion": ""}

    columnas = 3 if len(numericas) > 2 else len(numericas)
    filas = -(-len(numericas) // columnas)  # techo de la division
    fig, ejes = plt.subplots(filas, columnas, figsize=(4.6 * columnas, 3.6 * filas), squeeze=False)

    cantidad_con_atipicos = 0
    for i, columna in enumerate(numericas):
        ax = ejes[i // columnas][i % columnas]
        serie = df[columna].dropna()
        sns.boxplot(y=serie, ax=ax, color=PALETA[i % len(PALETA)])
        ax.set_title(columna, fontsize=10)
        ax.set_ylabel("")
        q1, q3 = serie.quantile(0.25), serie.quantile(0.75)
        riq = q3 - q1
        atipicos = serie[(serie < q1 - 1.5 * riq) | (serie > q3 + 1.5 * riq)]
        if not atipicos.empty:
            cantidad_con_atipicos += 1

    # Oculta los subgraficos sobrantes de la grilla si no se llena por completo.
    for j in range(len(numericas), filas * columnas):
        ejes[j // columnas][j % columnas].axis("off")

    fig.suptitle("Diagramas de caja (boxplot) por variable", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    nombre = "boxplots.png"
    fig.savefig(_ruta(dataset, nombre), dpi=130)
    plt.close(fig)

    explicacion = (
        "Cada caja te muestra dónde se concentra la mitad de los datos \"del medio\" de esa variable: la "
        "línea dentro de la caja es el valor central (mediana), y los bordes de la caja marcan hasta dónde "
        "llega el 25% más bajo y el 25% más alto de esa franja central. Las líneas que salen de la caja "
        "(los \"bigotes\") cubren el resto de los valores normales, y los puntos sueltos por fuera son casos "
        "inusuales para esa variable (bastante distintos al resto) — una forma distinta, pero parecida, de "
        "detectar casos raros a la de la tabla de valores atípicos de la sección anterior (que usaba el "
        "promedio y qué tanto se alejan los datos de él). "
        + (
            f"En este dataset, {cantidad_con_atipicos} de {len(numericas)} variable(s) mostradas "
            "tienen al menos un caso así de inusual."
            if cantidad_con_atipicos else
            "En este dataset, ninguna de las variables mostradas tiene casos así de inusuales."
        )
    )
    return {"url": _url(dataset, nombre), "explicacion": explicacion}


def generar_comparacion_modelos_chart(comparacion: dict, problema: str, dataset: str) -> dict:
    """Grafico de barras agrupadas comparando los modelos entrenados: todas las metricas de
    clasificacion estan en escala 0-1, asi que se pueden agrupar en un solo grafico; en
    regresion se muestra solo R^2 (MAE/RMSE quedan en la unidad original del objetivo y no
    son comparables en la misma escala que R^2)."""
    nombres_modelos = list(comparacion.keys())
    if not nombres_modelos:
        return {"url": None, "explicacion": ""}

    if problema == "clasificacion":
        metricas_mostradas = ["accuracy", "precision", "recall", "f1"]
        etiquetas_metricas = ["Accuracy", "Precision", "Recall", "F1-score"]
    else:
        metricas_mostradas = ["r2"]
        etiquetas_metricas = ["R²"]

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    x = np.arange(len(metricas_mostradas))
    ancho = 0.8 / max(len(nombres_modelos), 1)
    for i, nombre_modelo in enumerate(nombres_modelos):
        valores = [comparacion[nombre_modelo][m] for m in metricas_mostradas]
        ax.bar(x + i * ancho, valores, width=ancho, label=nombre_modelo, color=PALETA[i % len(PALETA)])

    ax.set_xticks(x + ancho * (len(nombres_modelos) - 1) / 2)
    ax.set_xticklabels(etiquetas_metricas)
    ax.set_ylim(0, 1.05 if problema == "clasificacion" else None)
    ax.set_ylabel("Valor de la métrica")
    ax.set_title("Comparación de modelos")
    ax.legend()
    fig.tight_layout()
    nombre = "comparacion_modelos.png"
    fig.savefig(_ruta(dataset, nombre), dpi=130)
    plt.close(fig)

    if len(nombres_modelos) >= 2:
        m1, m2 = nombres_modelos[0], nombres_modelos[1]
        clave_principal = metricas_mostradas[-1] if problema != "clasificacion" else "f1"
        v1, v2 = comparacion[m1][clave_principal], comparacion[m2][clave_principal]
        ganador = m1 if v1 >= v2 else m2
        texto_metricas = (
            f"la única métrica mostrada (R²) va de 0 a 1" if len(metricas_mostradas) == 1
            else f"las {len(metricas_mostradas)} métricas mostradas van de 0 a 1"
        )
        explicacion = (
            f"Cada barra representa el valor de esa métrica para un modelo distinto: cuanto más alta, "
            f"mejor ({texto_metricas}). En este dataset, "
            f'"{ganador}" tiene las barras más altas en la métrica principal usada para elegir el mejor '
            "modelo."
        )
    else:
        explicacion = "Cada barra representa el valor de esa métrica para el modelo entrenado."

    return {"url": _url(dataset, nombre), "explicacion": explicacion}


def generar_importancia_variables(modelo, columnas_features: list, dataset: str, maximo: int = 15) -> dict:
    """Grafico de barras horizontales con la importancia de cada variable segun el modelo
    ganador: `feature_importances_` en modelos de arbol (Decision Tree, Random Forest) o los
    coeficientes en Linear Regression. KNN no tiene un equivalente directo e interpretable,
    asi que en ese caso no se genera nada (se documenta la razon en el texto del informe)."""
    if hasattr(modelo, "feature_importances_"):
        valores = np.asarray(modelo.feature_importances_)
        tipo = "importancia"
    elif hasattr(modelo, "coef_"):
        coef = np.asarray(modelo.coef_)
        # Con varias clases (p. ej. Iris) hay una fila de coeficientes por clase: se promedia su magnitud para tener un valor por variable.
        valores = np.abs(coef).mean(axis=0) if coef.ndim > 1 else np.abs(coef)
        tipo = "coeficiente"
    else:
        return {"url": None, "explicacion": "", "disponible": False}

    orden = np.argsort(valores)[::-1][:maximo]
    columnas_top = [columnas_features[i] for i in orden]
    valores_top = valores[orden]

    fig, ax = plt.subplots(figsize=(7.2, max(3.2, 0.42 * len(columnas_top))))
    ax.barh(columnas_top[::-1], valores_top[::-1], color=PALETA[1])
    ax.set_xlabel("Importancia relativa" if tipo == "importancia" else "Magnitud del coeficiente (valor absoluto)")
    ax.set_title("Variables más influyentes en la predicción")
    fig.tight_layout()
    nombre = "importancia_variables.png"
    fig.savefig(_ruta(dataset, nombre), dpi=130)
    plt.close(fig)

    principal = columnas_top[0]
    if tipo == "importancia":
        explicacion = (
            f'El modelo mide qué tanto usó cada variable para dividir sus decisiones: "{principal}" es '
            "la que más influyó en la predicción. Estas importancias siempre suman 1 entre todas las "
            "variables del modelo (aquí se muestran solo las más relevantes)."
        )
    else:
        explicacion = (
            f'Este modelo calcula su predicción con una fórmula donde cada variable "pesa" un poco: '
            f'"{principal}" es la que más cambia el resultado final cuando cambia (para bien o para mal), '
            "así que es la que más peso tiene en esa fórmula."
        )
    return {"url": _url(dataset, nombre), "explicacion": explicacion, "disponible": True}


def generar_matriz_confusion(y_test, y_pred, etiquetas, dataset: str) -> str:
    from sklearn.metrics import confusion_matrix

    matriz = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(5.8, 5.0))
    sns.heatmap(
        matriz, annot=True, fmt="d", cmap=_CMAP_SECUENCIAL, linewidths=1.5, linecolor="#14112b", xticklabels=etiquetas, yticklabels=etiquetas, ax=ax
    )
    ax.set_xlabel("Predicción")
    ax.set_ylabel("Valor real")
    ax.set_title("Matriz de confusión")
    fig.tight_layout()
    nombre = "matriz_confusion.png"
    fig.savefig(_ruta(dataset, nombre), dpi=130)
    plt.close(fig)
    return _url(dataset, nombre)


def generar_comparacion_regresion(y_test, y_pred, dataset: str) -> str:
    fig, ax = plt.subplots(figsize=(6.4, 5.6))
    ax.scatter(y_test, y_pred, alpha=0.6, color=PALETA[0])
    minimo, maximo = min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())
    ax.plot([minimo, maximo], [minimo, maximo], color=PALETA[3], linestyle="--", label="Predicción ideal")
    ax.set_xlabel("Valor real")
    ax.set_ylabel("Valor predicho")
    ax.set_title("Real vs. predicho")
    ax.legend()
    fig.tight_layout()
    nombre = "real_vs_prediccion.png"
    fig.savefig(_ruta(dataset, nombre), dpi=130)
    plt.close(fig)
    return _url(dataset, nombre)
