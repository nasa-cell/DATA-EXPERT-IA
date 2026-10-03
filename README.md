# DataExpert IA

## ⬇️ Descargar la app
Apretá el enlace y se descarga:

- 🖥️ **PC (Windows):** [Apretá acá para descargar DataExpert IA](https://github.com/nasa-cell/DATA-EXPERT-IA/releases/download/v1.2.5/Instalar_DataExpert_IA.exe) — instalador versión 1.2.5, 81 MB

**Plataforma web de análisis matemático, estadístico y Machine Learning**
*Fundamentos y Algoritmia para Inteligencia Artificial*

Plataforma educativa que recorre un proyecto de ciencia de datos completo sobre datos reales: exploración, preprocesamiento, álgebra lineal, estadística, valores atípicos, gráficos, entrenamiento y evaluación de modelos, y un informe PDF final. Incluye 11 datasets listos para usar.

## Aplicación de Windows

**[Descargar el instalador para Windows (versión 1.2.5)](https://github.com/nasa-cell/DATA-EXPERT-IA/releases/download/v1.2.5/Instalar_DataExpert_IA.exe)**: no necesita Python. Abre `Instalar_DataExpert_IA.exe`, elige la carpeta y sigue los pasos; queda un acceso directo en el escritorio.

Para generar el instalador desde el código se usa `pc instalador/construir_instalador.bat` (detalles en `pc instalador/LEEME.txt`).

## Características

- Subida de datasets propios (CSV o Excel .xlsx/.xls), de a uno o varios a la vez: cada archivo dice cuántas columnas y filas se detectaron (y si hay columnas vacías o repetidas), con una vista previa para elegir qué columnas usar y cuál es el objetivo («Viendo columnas 1–6 de 60», buscador, «Usar todas»). Quedan guardados en el equipo, con foto de portada opcional (sale también en el PDF).
- **Procesar varios**: botón general en la barra (y tarjeta en Inicio) para elegir varios datasets —incluidos, CSV o Excel— y los pasos (todo, solo entrenar, solo explorar o uno por uno), y procesarlos solos, 3 o 6 a la vez; los demás esperan en cola. Cada dataset hace sus pasos en orden, los ya hechos no se repiten y siguen aunque se cambie de página.
- Se pueden entrenar varios datasets al mismo tiempo (también desde el panel de cada uno).
- Campana en la barra: muestra lo que se está procesando con su avance y, al terminar, suena (una campana de unos 5 segundos) y ofrece «Ver resultado →». Cada aviso lleva el color de su dataset. Lo del dataset que tienes abierto no aparece (ya se ve en la página) y cada aviso se borra solo al entrar a ver su resultado; la escoba limpia todos de una vez.
- Los 11 datasets incluidos tienen las columnas y categorías en español (tablas, gráficos, predicción y PDF).
- **Semillas de trigo** (dataset real de UCI: 210 granos, 7 medidas, 3 variedades) y **Granos de café** (300 granos simulados de Arábica, Robusta y Liberica con las mismas 7 medidas): los dos traen la sección **«✅ Pautas de la actividad»** con las 7 pautas del curso (explorar con Pandas, StandardScaler, NumPy, estadística de área y perímetro, atípicos con 2σ, histograma y dispersión por variedad, K-Vecinos contra Árbol de Decisión). Cada pauta dice su resultado y se abre con su tabla, sus gráficos y su conclusión, y hay una conclusión general. El botón **«PDF de las pautas»** arma un PDF corto sólo con eso (la campana avisa mientras se genera), y el informe completo también incluye la sección. Aparece en cualquier dataset con columnas `área`, `perímetro` y una variable objetivo.
- El análisis de cada dataset se guarda: al volver (o al abrir otra vez la aplicación) los pasos hechos siguen marcados y se muestran sin recalcular, hasta pulsar «Reiniciar análisis». Los pasos siguen calculando aunque se cambie de página, y la aplicación avisa al terminar.
- Color elegible para cada dataset (página e informe PDF).
- Exploración y preprocesamiento con Pandas (nulos, duplicados, codificación, normalización).
- Álgebra lineal con NumPy: vectores, matrices, producto punto, norma y sistemas de ecuaciones, con un ejemplo fijo y otro con registros reales del dataset.
- Estadística descriptiva sobre los valores reales (sin normalizar), con varianza y desviación estándar también implementadas a mano.
- Detección de valores atípicos (media ± k·σ).
- Gráficos con Matplotlib y Seaborn.
- Modelos de Scikit-learn para clasificación o regresión (se detecta automáticamente), con métricas reales. Cada modelo es un Pipeline que rellena, codifica y escala aprendiendo solo de la parte de entrenamiento, y el mejor se elige por validación cruzada.
- Además del gráfico general, los modelos se comparan de a dos (K-Vecinos contra Árbol de Decisión, y Random Forest contra Regresión Logística; en regresión, Árbol contra Random Forest y Regresión Lineal contra el mejor de ellos), con el valor sobre cada barra y una descripción de quién gana. Sale en todos los datasets y en el informe PDF, antes de las conclusiones.
- Informe PDF con ReportLab.

## Tecnologías

Python 3.11+, Flask, Pandas, NumPy, Scikit-learn, Matplotlib, Seaborn, ReportLab, HTML/CSS/JavaScript.

## Estructura del proyecto

```text
DataExpert_IA/
├── app.py                          # Rutas Flask (páginas y endpoints JSON)
├── generar_datasets.py             # Genera los 11 CSV de data/
├── generar_logo.py                 # Genera static/img/logo.png
├── requirements.txt
├── README.md
├── INFORME_DATAEXPERT.md
│
├── pautas/                         # Entregable de la actividad: las 7 pautas
│   ├── LEEME.md                    # Qué pide cada pauta y dónde está resuelta
│   ├── pautas.ipynb                # Cuaderno con las 7 pautas paso a paso
│   ├── pautas.py                   # Lo mismo en un solo archivo de Python
│   ├── codigo_de_la_app/           # Copia de los servicios de src/ que usan las pautas
│   ├── datos/                      # semillas.csv
│   └── resultados/                 # Tablas CSV, gráficos PNG, salida_pautas.txt y PDF_de_las_pautas.pdf
│
├── data/                           # Los 11 datasets + alumnos_nuevos_prueba.csv
│   ├── semillas.csv                # Semillas de trigo (UCI)
│   ├── cafe.csv                    # Granos de café (simulado)
│   ├── ...                         # iris, diabetes, viviendas, vehiculos, clientes, sintetico, empleados, estudiantes, prestamos
│   └── fuentes/                    # seeds_dataset.txt: archivo original de las semillas
│
├── src/
│   ├── dataset_service.py          # Metadatos, datasets subidos, portadas, colores y análisis guardado
│   ├── preprocessing_service.py    # Exploración y preprocesamiento
│   ├── statistics_service.py       # Estadística + varianza/desviación manuales
│   ├── linear_algebra_service.py   # Vectores, matrices, sistema de ecuaciones
│   ├── visualization_service.py    # Histogramas, dispersión, correlación, matriz de confusión
│   ├── machine_learning_service.py # Entrenamiento, evaluación y comparación de modelos
│   ├── pautas_service.py           # Las 7 pautas de la actividad (sección «Pautas de la actividad»)
│   ├── pdf_service.py              # Informe PDF completo y PDF de las pautas
│   ├── turnos.py                   # Cuántos procesos largos van a la vez (3 o 6) y la cola
│   └── configuracion.py            # Rutas: código (solo lectura) y datos del usuario
│
├── templates/                      # base.html, index.html, dashboard.html, subir.html, procesar.html
├── static/
│   ├── css/style.css
│   ├── js/                         # app.js, interfaz.js, iconos.js, subir.js, procesar.js, campana.js
│   ├── img/                        # logo.svg, logo.png, datasets/ (portadas)
│   ├── fuentes/                    # Tipografías locales (web y PDF)
│   └── graficos/<dataset>/         # Gráficos generados (PNG)
│
├── resultados/                     # predicciones, historial y evaluación de modelos
├── informes/                       # DataExpert_IA_Informe.pdf
├── datasets_subidos/               # Datasets que sube el usuario (se crea al usar la app, no se sube al repositorio)
├── analisis_guardados/             # Análisis guardado de cada dataset (se crea al usar la app, no se sube al repositorio)
│
└── pc instalador/                  # Todo lo necesario para crear el instalador de Windows
    ├── construir_instalador.bat    # Arma el instalador de principio a fin
    ├── DataExpertIA.spec           # Empaquetado de la aplicación
    ├── instalador.iss              # Guion del instalador (aquí va el número de versión)
    ├── lanzador.py                 # Arranca la aplicación instalada y abre el navegador
    ├── LEEME.txt                   # Pasos para generar el instalador
    ├── recursos/                   # Íconos e imágenes del instalador
    └── salida/                     # Instalar_DataExpert_IA.exe ya generado
```

## Instalación

```bash
python -m venv venv
venv\Scripts\activate          # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abre http://127.0.0.1:5050 en el navegador.

## Uso

1. Elige un dataset en la pantalla de inicio, o sube el tuyo con **Subir mi CSV / Excel**.
2. En el panel, ejecuta los pasos en orden: Explorar, Preprocesar, Álgebra lineal, Estadística, Valores atípicos, Gráficos, Entrenar, Evaluar.
3. Pulsa **Generar PDF** para obtener el informe con todo lo ejecutado.
4. Para varios datasets a la vez, usa **Procesar varios** (barra de arriba): marca los datasets y los pasos, elige 3 o 6 a la vez y toca **Procesar**. La campana avisa cuando cada uno termina.

## Créditos

Fotos de portada: Empleados y Estudiantes, de Shixart1985 en Wikimedia Commons (CC BY 2.0); Préstamos, de kschneider2991 en Pixabay (CC0).
