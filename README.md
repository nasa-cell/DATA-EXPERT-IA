# DataExpert IA

**Plataforma web de análisis matemático, estadístico y Machine Learning**
*Fundamentos y Algoritmia para Inteligencia Artificial*

Plataforma educativa que recorre un proyecto de ciencia de datos completo sobre datos reales: exploración, preprocesamiento, álgebra lineal, estadística, valores atípicos, gráficos, entrenamiento y evaluación de modelos, y un informe PDF final. Incluye 9 datasets listos para usar.

## Características

- Exploración y preprocesamiento con Pandas (nulos, duplicados, codificación, normalización).
- Álgebra lineal con NumPy: vectores, matrices, producto punto, norma y sistemas de ecuaciones.
- Estadística descriptiva, con varianza y desviación estándar también implementadas a mano.
- Detección de valores atípicos (media ± k·σ).
- Gráficos con Matplotlib y Seaborn.
- Modelos de Scikit-learn para clasificación o regresión (se detecta automáticamente), con métricas reales.
- Informe PDF con ReportLab.

## Tecnologías

Python 3.11+, Flask, Pandas, NumPy, Scikit-learn, Matplotlib, Seaborn, ReportLab, HTML/CSS/JavaScript.

## Instalación

```bash
python -m venv venv
venv\Scripts\activate          # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abre http://127.0.0.1:5050 en el navegador.

## Uso

1. Elige un dataset en la pantalla de inicio.
2. En el panel, ejecuta los pasos en orden: Explorar, Preprocesar, Álgebra lineal, Estadística, Valores atípicos, Gráficos, Entrenar, Evaluar.
3. Pulsa **Generar PDF** para obtener el informe con todo lo ejecutado.

## Aplicación de Windows

La carpeta `pc instalador/` contiene lo necesario para generar un instalador de Windows (`construir_instalador.bat`). Los detalles están en `pc instalador/LEEME.txt`.

## Créditos

Fotos de portada: Empleados y Estudiantes, de Shixart1985 en Wikimedia Commons (CC BY 2.0); Préstamos, de kschneider2991 en Pixabay (CC0).
