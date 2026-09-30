# DataExpert IA

**Plataforma Web de Análisis Matemático, Estadístico y Machine Learning**
*Fundamentos y Algoritmia para Inteligencia Artificial*

## Descripción

DataExpert IA es una plataforma web educativa que resuelve el caso práctico de la empresa
DataExpert: aplicar fundamentos de **Machine Learning**, **álgebra lineal** y **estadística**
sobre datos reales, de principio a fin y sin resultados simulados. El usuario elige uno de
9 datasets ya incluidos en el proyecto (no hace falta subir ningún CSV) y ejecuta, con un
clic por botón, cada etapa del análisis: exploración, preprocesamiento, álgebra lineal,
estadística, detección de outliers, gráficos, entrenamiento de modelos, evaluación y,
finalmente, un informe PDF que reúne todo lo anterior.

## Objetivo

Demostrar el flujo completo de un proyecto de ciencia de datos aplicado a IA: desde cargar
y explorar un dataset con Pandas, hasta entrenar y evaluar un modelo real con Scikit-learn,
pasando por operaciones de álgebra lineal con NumPy y estadística descriptiva (incluyendo
funciones de varianza y desviación estándar implementadas a mano, sin depender solo de
NumPy).

## Características

- 9 datasets incluidos en el proyecto — nada de subir archivos para poder usar el sistema.
- Exploración de datos con Pandas (`head`, `tail`, `describe`, nulos, duplicados, tipos).
- Preprocesamiento real: imputación de nulos (media/moda), eliminación de duplicados,
  codificación (`LabelEncoder`/`OneHotEncoder`) y normalización (`StandardScaler`), con un
  resumen "antes/después" y el detalle de cada transformación aplicada.
- Álgebra lineal con NumPy: vectores, producto punto, norma, operaciones con matrices y
  resolución de un sistema de ecuaciones lineales (`np.linalg.solve`).
- Estadística descriptiva (media, mediana, moda, varianza, desviación estándar) calculada
  con NumPy **y** con funciones propias implementadas matemáticamente, comparando ambas.
- Detección de valores atípicos por desviación estándar (media ± k·σ).
- Gráficos generados con Matplotlib/Seaborn: histogramas, dispersión, correlación y
  distribución de la variable objetivo.
- Entrenamiento y comparación de dos modelos de Scikit-learn (detecta automáticamente si
  el problema es de clasificación o regresión) con métricas reales: accuracy, precision,
  recall, F1 (clasificación) o MAE, MSE, RMSE, R² (regresión).
- Informe PDF profesional (ReportLab) con portada, tablas, gráficos y conclusiones basadas
  en los resultados reales del análisis en curso.
- Interfaz moderna, responsive y con animaciones sutiles (entrada de tarjetas, ripple al
  presionar botones, transiciones de estado) respetando `prefers-reduced-motion`.

## Diseño de la interfaz

Estilo «laboratorio pop»: cada página es un campo de color sólido (el color de cada dataset, que se define en `src/dataset_service.py`) con paneles
blancos de borde grueso y sombra dura. Tipografías locales en `static/fuentes/` (Unbounded, Instrument Sans y JetBrains Mono), así que no
necesita internet. Los íconos son SVG propios (`static/js/iconos.js`), el logo está en `static/img/logo.svg` y todo el estilo en `static/css/style.css`.
Los gráficos de Matplotlib usan la misma paleta (`src/visualization_service.py`). Los pasos del análisis están en una columna vertical con barra
de avance y cada gráfico se puede ampliar con un clic. La carpeta `copia_antes_del_rediseno/` guarda el diseño anterior por si quieres compararlo.

## Tecnologías

| Área | Tecnología |
|---|---|
| Backend | Python 3.11+, Flask |
| Análisis de datos | Pandas, NumPy |
| Machine Learning | Scikit-learn |
| Visualización | Matplotlib, Seaborn |
| PDF | ReportLab |
| Frontend | HTML5, CSS3, JavaScript (sin frameworks) |

## Estructura del proyecto

```text
DataExpert_IA/
├── app.py                        # Rutas Flask (páginas y endpoints JSON)
├── generar_datasets.py           # Genera los 6 CSV de data/
├── requirements.txt
├── README.md
├── INFORME_DATAEXPERT.md
│
├── data/                         # Los 9 datasets (ya incluidos)
├── src/
│   ├── dataset_service.py        # Metadatos, carga y estado del análisis en curso
│   ├── preprocessing_service.py  # Exploración y preprocesamiento
│   ├── statistics_service.py     # Estadística + varianza/desviación manuales
│   ├── linear_algebra_service.py # Vectores, matrices, sistema de ecuaciones
│   ├── visualization_service.py  # Histogramas, dispersión, correlación, matriz de confusión
│   ├── machine_learning_service.py # Entrenamiento, evaluación y comparación de modelos
│   ├── pdf_service.py            # Generación del informe PDF
│   └── configuracion.py          # Rutas: código (solo lectura) y datos del usuario (se escriben)
│
├── templates/                    # base.html, index.html, dashboard.html
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   └── graficos/<dataset>/       # Gráficos generados (PNG)
│
├── resultados/                   # predicciones.csv, historial.json
├── informes/                     # DataExpert_IA_Informe.pdf
└── pc instalador/                # Aplicación instalable para Windows (ver más abajo)
```

## Instalar como aplicación de Windows

La carpeta `pc instalador/` convierte el proyecto en un programa que se instala con doble clic, sin Python ni comandos:

1. Abre `pc instalador\salida\Instalar_DataExpert_IA.exe`.
2. Elige el disco y la carpeta donde instalarlo (por defecto propone el disco con más espacio libre) y pulsa Siguiente.
3. Se abre una ventana pequeña de DataExpert IA y la página en el navegador. Después queda un icono en el escritorio y en el menú Inicio.

Los informes PDF, los resultados, el historial y los gráficos se guardan en la subcarpeta `datos_usuario` dentro de la carpeta de instalación:
actualizar o reinstalar no la borra, y al desinstalar se pregunta si quieres conservarla.
Para generar de nuevo el instalador (quien mantiene el proyecto) se ejecuta `pc instalador\construir_instalador.bat`; los detalles están en `pc instalador\LEEME.txt`.
El código funciona igual desde `python app.py`: `src/configuracion.py` decide si los archivos generados van a la carpeta del proyecto o a `datos_usuario`.

## Instalación (Windows)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python generar_datasets.py
python app.py
```

Abre el navegador en **http://127.0.0.1:5050**.

## Instalación (Linux/Mac)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python generar_datasets.py
python app.py
```

## Uso

1. Elige uno de los 9 datasets en la pantalla de inicio.
2. En el dashboard, usa los botones en este orden sugerido:
   `Explorar` → `Preprocesar` → `Álgebra lineal` → `Estadística` → `Valores atípicos` →
   `Gráficos` → `Entrenar modelo` → `Evaluar modelo` → `Generar PDF`.
3. Cada botón ejecuta el análisis real sobre el dataset actual y muestra el resultado
   debajo, sin recargar la página.
4. El botón **Generar PDF** arma el informe con todo lo que ya se ejecutó en la sesión
   actual (mientras más pasos hayas corrido antes, más completo sale el informe).

## Los 9 datasets

| Dataset | Objetivo | Tipo de problema | Origen |
|---|---|---|---|
| Iris | Clasificar especie de flor | Clasificación | Público (scikit-learn, Fisher 1936) |
| Diabetes | Diagnóstico de diabetes | Clasificación | Generado sintéticamente (estructura tipo Pima Indians) |
| Viviendas | Precio de una vivienda | Regresión | Generado sintéticamente |
| Vehículos | Precio de un vehículo | Regresión | Generado sintéticamente |
| Clientes | Segmento de valor del cliente | Clasificación | Generado sintéticamente |
| Sintético | Variable objetivo binaria genérica | Clasificación | Generado con NumPy/Pandas, con nulos controlados |
| Empleados | Renuncia (attrition) de un empleado | Clasificación | Generado sintéticamente |
| Estudiantes | Nota final de un estudiante | Regresión | Generado sintéticamente |
| Préstamos | Aprobación de un préstamo bancario | Clasificación | Generado sintéticamente |

Las fotos de portada de Empleados y Estudiantes son de **Shixart1985** en Wikimedia Commons
(licencia [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/)); la de Préstamos es de
**kschneider2991** en [Pixabay](https://pixabay.com/photos/money-money-tower-coins-euro-2180330/)
(licencia CC0, dominio público).

Todos se generan con `random_state=42` (o una semilla equivalente), así que los resultados
son reproducibles entre ejecuciones.

## Machine Learning

El sistema detecta automáticamente el tipo de problema según la variable objetivo
(`machine_learning_service.detectar_tipo_problema`): si es texto o tiene pocos valores
distintos, es clasificación; si no, regresión. Según eso entrena y compara:

- **Clasificación**: KNN, Decision Tree, Random Forest y Logistic Regression (esta última se agregó porque aprendió mejor de los mismos CSV:
  bajó los errores de clasificación de 145 a 131 sobre las filas de prueba; en Clientes, de 9 a 1 de 140).
- **Regresión**: Linear Regression, Decision Tree y Random Forest (la regresión lineal ya era la mejor y nada la superó en las pruebas).
- Las tablas con las métricas de cada modelo en cada dataset están en `resultados/evaluacion_todos_los_modelos.csv` (después del cambio) y
  `resultados/evaluacion_antes_del_cambio.csv` (antes).

Ambos se entrenan con `train_test_split` (80/20, `random_state=42`) y se evalúan con
métricas reales de Scikit-learn — nada se escribe a mano.

## Álgebra lineal

La sección de álgebra lineal es independiente del dataset seleccionado: usa vectores y
matrices fijos para demostrar de forma clara cada operación (suma, resta, producto punto,
norma, producto matricial, transpuesta y resolución de un sistema de ecuaciones lineales
con `np.linalg.solve`).

## Estadística y varianza manual

Además de `np.mean`, `np.median`, `np.var` y `np.std`, el proyecto implementa
`varianza_manual()` y `desviacion_estandar_manual()` en `statistics_service.py`, calculando
la fórmula matemática paso a paso (sin usar las funciones de NumPy en el cálculo), y
compara el resultado con NumPy para verificar que coinciden.

## Generación del informe PDF

El botón "Generar PDF" arma `informes/DataExpert_IA_Informe.pdf` con ReportLab. El diseño sigue el de la página
(«laboratorio pop»): portada a todo color con el color y la foto del dataset, cabecera y pie con número de página en cada hoja,
secciones numeradas, tarjetas de resumen, tablas con cabecera oscura, gráficos enmarcados y las mismas tipografías de la web
(Unbounded, Instrument Sans y JetBrains Mono, en `static/fuentes/pdf/`). Cada informe usa el color del dataset analizado.
Contenido: portada,
introducción, dataset seleccionado, exploración, preprocesamiento, álgebra lineal,
estadística (con la comparación manual vs. NumPy), valores atípicos, gráficos generados,
entrenamiento, evaluación, comparación de modelos, resultados (predicciones) y
conclusiones — todo con los datos reales de la sesión de análisis actual.

## Solución de errores comunes

| Problema | Causa probable | Solución |
|---|---|---|
| `FileNotFoundError` al seleccionar un dataset | No se generaron los CSV | Ejecuta `python generar_datasets.py` |
| "No hay un dataset seleccionado" | Se llamó a un endpoint sin pasar por `/dataset/<nombre>` | Entra al dashboard desde la pantalla de inicio |
| "⚠ Preprocesa el dataset antes de entrenar" | Se presionó "Entrenar modelo" sin "Preprocesar" antes | Presiona "Preprocesar" primero |
| Emojis rotos / `UnicodeEncodeError` en consola (Windows) | La consola usa cp1252 en vez de UTF-8 | Ya está resuelto en `app.py` (fuerza `stdout`/`stderr` a UTF-8); si persiste, usa Windows Terminal |
| El PDF sale con secciones "No ejecutada" | Aún no se corrieron esos botones en la sesión actual | Ejecuta primero los botones correspondientes, luego "Generar PDF" |
| Puerto 5050 ocupado | Otro proceso lo está usando | Define la variable de entorno `PORT` con otro valor antes de correr `python app.py` |

## Matriz de cumplimiento

| Requisito | Cumplimiento |
|---|:---:|
| Dataset público/sintético | ✓ |
| Pandas | ✓ |
| Exploración | ✓ |
| Valores nulos | ✓ |
| Normalización | ✓ |
| Codificación | ✓ |
| Scikit-learn | ✓ |
| Clasificación/regresión | ✓ |
| Vectores NumPy | ✓ |
| Matrices NumPy | ✓ |
| Producto punto | ✓ |
| Norma | ✓ |
| Sistema de ecuaciones | ✓ |
| Media | ✓ |
| Mediana | ✓ |
| Varianza | ✓ |
| Desviación estándar | ✓ |
| Varianza manual | ✓ |
| Desviación manual | ✓ |
| Valores atípicos | ✓ |
| Histogramas | ✓ |
| Gráficos de dispersión | ✓ |
| Seaborn | ✓ |
| Evaluación ML | ✓ |
| PDF | ✓ |
