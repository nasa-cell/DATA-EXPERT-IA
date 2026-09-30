# DataExpert IA

**Plataforma web de análisis matemático, estadístico y Machine Learning**
*Fundamentos y Algoritmia para Inteligencia Artificial*

Plataforma educativa que recorre un proyecto de ciencia de datos completo sobre datos reales: exploración, preprocesamiento, álgebra lineal, estadística, valores atípicos, gráficos, entrenamiento y evaluación de modelos, y un informe PDF final. Incluye 9 datasets listos para usar.

## Aplicación de Windows

**[Descargar el instalador para Windows](https://drive.google.com/file/d/1ozK9bwAEOEEofJel41qRQI4mLuACOVdJ/view?usp=sharing)**: no necesita Python. Abre `Instalar_DataExpert_IA.exe`, elige la carpeta y sigue los pasos; queda un acceso directo en el escritorio.

Para generar el instalador desde el código se usa `pc instalador/construir_instalador.bat` (detalles en `pc instalador/LEEME.txt`).

## Características

- Subida de datasets propios (CSV o Excel .xlsx/.xls): vista previa para elegir qué columnas usar y cuál es el objetivo; después se analiza en el mismo panel que los datasets incluidos.
- Exploración y preprocesamiento con Pandas (nulos, duplicados, codificación, normalización).
- Álgebra lineal con NumPy: vectores, matrices, producto punto, norma y sistemas de ecuaciones.
- Estadística descriptiva, con varianza y desviación estándar también implementadas a mano.
- Detección de valores atípicos (media ± k·σ).
- Gráficos con Matplotlib y Seaborn.
- Modelos de Scikit-learn para clasificación o regresión (se detecta automáticamente), con métricas reales.
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
│   ├── dataset_service.py          # Metadatos, carga y estado del análisis en curso
│   ├── preprocessing_service.py    # Exploración y preprocesamiento
│   ├── statistics_service.py       # Estadística + varianza/desviación manuales
│   ├── linear_algebra_service.py   # Vectores, matrices, sistema de ecuaciones
│   ├── visualization_service.py    # Histogramas, dispersión, correlación, matriz de confusión
│   ├── machine_learning_service.py # Entrenamiento, evaluación y comparación de modelos
│   ├── pdf_service.py              # Generación del informe PDF
│   └── configuracion.py            # Rutas: código (solo lectura) y datos del usuario
│
├── templates/                      # base.html, index.html, dashboard.html, subir.html
├── static/
│   ├── css/style.css
│   ├── js/                         # app.js, interfaz.js, iconos.js, subir.js
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

## Créditos

Fotos de portada: Empleados y Estudiantes, de Shixart1985 en Wikimedia Commons (CC BY 2.0); Préstamos, de kschneider2991 en Pixabay (CC0).
