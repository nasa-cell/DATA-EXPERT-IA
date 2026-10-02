# DataExpert IA

**Plataforma web de análisis matemático, estadístico y Machine Learning**
*Fundamentos y Algoritmia para Inteligencia Artificial*

Plataforma educativa que recorre un proyecto de ciencia de datos completo sobre datos reales: exploración, preprocesamiento, álgebra lineal, estadística, valores atípicos, gráficos, entrenamiento y evaluación de modelos, y un informe PDF final. Incluye 9 datasets listos para usar.

## Aplicación de Windows

**[Descargar el instalador para Windows (versión 1.2)](https://github.com/nasa-cell/DATA-EXPERT-IA/releases/download/v1.2/Instalar_DataExpert_IA.exe)**: no necesita Python. Abre `Instalar_DataExpert_IA.exe`, elige la carpeta y sigue los pasos; queda un acceso directo en el escritorio.

Para generar el instalador desde el código se usa `pc instalador/construir_instalador.bat` (detalles en `pc instalador/LEEME.txt`).

## Características

- Subida de datasets propios (CSV o Excel .xlsx/.xls), de a uno o varios a la vez: cada archivo dice cuántas columnas y filas se detectaron (y si hay columnas vacías o repetidas), con una vista previa para elegir qué columnas usar y cuál es el objetivo («Viendo columnas 1–6 de 60», buscador, «Usar todas»). Quedan guardados en el equipo, con foto de portada opcional (sale también en el PDF).
- **Procesar varios**: botón general en la barra (y tarjeta en Inicio) para elegir varios datasets —incluidos, CSV o Excel— y los pasos (todo, solo entrenar, solo explorar o uno por uno), y procesarlos solos, 3 o 6 a la vez; los demás esperan en cola. Cada dataset hace sus pasos en orden, los ya hechos no se repiten y siguen aunque se cambie de página.
- Se pueden entrenar varios datasets al mismo tiempo (también desde el panel de cada uno).
- Campana en la barra: muestra lo que se está procesando con su avance y, al terminar, suena y ofrece «Ver resultado →». La escoba limpia los terminados.
- Los 9 datasets incluidos tienen las columnas y categorías en español (tablas, gráficos, predicción y PDF).
- El análisis de cada dataset se guarda: al volver (o al abrir otra vez la aplicación) los pasos hechos siguen marcados y se muestran sin recalcular, hasta pulsar «Reiniciar análisis». Los pasos siguen calculando aunque se cambie de página, y la aplicación avisa al terminar.
- Color elegible para cada dataset (página e informe PDF).
- Exploración y preprocesamiento con Pandas (nulos, duplicados, codificación, normalización).
- Álgebra lineal con NumPy: vectores, matrices, producto punto, norma y sistemas de ecuaciones.
- Estadística descriptiva, con varianza y desviación estándar también implementadas a mano.
- Detección de valores atípicos (media ± k·σ).
- Gráficos con Matplotlib y Seaborn.
- Modelos de Scikit-learn para clasificación o regresión (se detecta automáticamente), con métricas reales. Cada modelo es un Pipeline que rellena, codifica y escala aprendiendo solo de la parte de entrenamiento, y el mejor se elige por validación cruzada.
- Informe PDF con ReportLab.

## Tecnologías

Python 3.11+, Flask, Pandas, NumPy, Scikit-learn, Matplotlib, Seaborn, ReportLab, HTML/CSS/JavaScript.

## Estructura del proyecto

```text
DataExpert_IA/
├── app.py                          # Rutas Flask (páginas y endpoints JSON)
├── generar_datasets.py             # Genera los 9 CSV de data/
├── generar_logo.py                 # Genera static/img/logo.png
├── requirements.txt
├── README.md
├── INFORME_DATAEXPERT.md
│
├── data/                           # Los 9 datasets + alumnos_nuevos_prueba.csv
├── src/
│   ├── dataset_service.py          # Metadatos, datasets subidos, portadas, colores y análisis guardado
│   ├── preprocessing_service.py    # Exploración y preprocesamiento
│   ├── statistics_service.py       # Estadística + varianza/desviación manuales
│   ├── linear_algebra_service.py   # Vectores, matrices, sistema de ecuaciones
│   ├── visualization_service.py    # Histogramas, dispersión, correlación, matriz de confusión
│   ├── machine_learning_service.py # Entrenamiento, evaluación y comparación de modelos
│   ├── pdf_service.py              # Generación del informe PDF
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
└── pc instalador/                  # Scripts para crear el instalador de Windows
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
