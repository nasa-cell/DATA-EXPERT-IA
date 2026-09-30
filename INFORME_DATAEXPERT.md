# Informe Académico — DataExpert IA

**Fundamentos y Algoritmia para Inteligencia Artificial**

## 1. Problemática

La empresa DataExpert, especializada en soluciones de Inteligencia Artificial, enfrenta un
reto: la falta de una base sólida en los fundamentos matemáticos y algorítmicos de sus
equipos limita su capacidad de desarrollar, optimizar y escalar soluciones de Machine
Learning y Deep Learning. Sin dominio de álgebra lineal, estadística y los fundamentos del
preprocesamiento y entrenamiento de modelos, cualquier solución de IA que construyan
corre el riesgo de ser frágil, difícil de depurar o de interpretar mal sus resultados.

## 2. Propuesta

Se propone una plataforma web (DataExpert IA) que sirva simultáneamente como herramienta de
análisis y como demostración práctica y verificable de esos fundamentos. En vez de una
serie de notebooks aislados, el sistema integra en un solo flujo interactivo: exploración
de datos, preprocesamiento, álgebra lineal, estadística (incluyendo implementaciones
manuales de varianza y desviación estándar, para verificar el resultado de NumPy),
detección de valores atípicos, visualización, entrenamiento y evaluación de modelos, y
generación automática de un informe PDF con los resultados reales de cada ejecución.

## 3. Objetivos

- Implementar un modelo básico de Machine Learning (clasificación o regresión) con
  exploración y preprocesamiento reales de un dataset.
- Resolver operaciones fundamentales de álgebra lineal aplicadas a IA con NumPy: vectores,
  matrices, producto punto, norma y sistemas de ecuaciones lineales.
- Realizar un análisis estadístico completo (medidas de tendencia central, dispersión y
  valores atípicos) con gráficos de apoyo.
- Calcular varianza y desviación estándar tanto con NumPy como con funciones propias,
  para verificar su correspondencia matemática.

## 4. Metodología

El sistema sigue el flujo estándar de un proyecto de ciencia de datos, expuesto como una
serie de acciones independientes que el usuario dispara desde la interfaz:

1. **Selección del dataset**: el usuario elige uno de los 9 datasets incluidos (o sube el suyo
   en CSV/Excel); no se requiere preparar archivos externos.
2. **Exploración** (`pandas`): dimensiones, tipos de datos, nulos, duplicados y
   estadísticas descriptivas iniciales.
3. **Preprocesamiento**: imputación de nulos (media para variables numéricas, moda para
   categóricas), eliminación de duplicados, codificación de variables categóricas
   (`LabelEncoder` para binarias, `OneHotEncoder` para el resto) y normalización
   (`StandardScaler`).
4. **Álgebra lineal** (`NumPy`): operaciones con vectores y matrices fijos, y resolución de
   un sistema de dos ecuaciones lineales con `np.linalg.solve`, verificando la solución.
5. **Estadística**: media, mediana, moda, varianza y desviación estándar por variable
   numérica, calculadas con NumPy y con funciones manuales propias, comparando ambos
   resultados.
6. **Valores atípicos**: identificados fuera del rango media ± 2 desviaciones estándar.
7. **Visualización** (`Matplotlib`/`Seaborn`): histogramas, dispersión, mapa de correlación
   y distribución de la variable objetivo.
8. **Entrenamiento** (`Scikit-learn`): el sistema detecta automáticamente si el problema es
   de clasificación o regresión según la variable objetivo, y entrena los modelos
   candidatos con `train_test_split` (80/20, semilla fija), ajustando los hiperparámetros de
   cada uno con validación cruzada solo sobre el conjunto de entrenamiento.
9. **Evaluación**: métricas reales — accuracy, precision, recall y F1 para clasificación;
   MAE, MSE, RMSE y R² para regresión — más matriz de confusión o gráfico real-vs-predicho.
10. **Informe**: un PDF que reúne todos los resultados anteriores de la sesión de análisis
    en curso.

## 5. Datasets

Se incluyen 9 datasets: uno público real (Iris, vía scikit-learn) y ocho generados
sintéticamente con NumPy/Pandas usando una semilla fija (`random_state=42`) para que sean
reproducibles. Los datasets sintéticos no son ruido aleatorio sin sentido: cada uno se
construye a partir de una relación matemática real entre sus variables (por ejemplo, el
precio de una vivienda depende linealmente del área, número de habitaciones, baños,
antigüedad y ubicación, más ruido gaussiano), de forma que el modelo entrenado sobre ellos
efectivamente aprende un patrón real y no memoriza etiquetas arbitrarias.

## 6. Pandas y NumPy

Pandas se usa para cargar, explorar, limpiar y transformar cada dataset (`read_csv`,
`describe`, `isnull`, `duplicated`, `get_dummies`, etc.). NumPy sustenta tanto la sección
educativa de álgebra lineal (vectores, matrices, `np.dot`, `np.linalg.norm`,
`np.linalg.solve`) como el cálculo estadístico (`np.mean`, `np.median`, `np.var`,
`np.std`) y las funciones manuales de varianza/desviación estándar implementadas sin
depender de esas funciones internamente.

## 7. Álgebra lineal aplicada

Los vectores y matrices que se manipulan (suma, resta, escalamiento, producto punto,
norma, producto matricial, transpuesta) son la base de cómo los algoritmos de Machine
Learning representan y transforman datos internamente: cada fila de un dataset preprocesado
es, en esencia, un vector; el escalado y la codificación son transformaciones matriciales.
Resolver un sistema de ecuaciones lineales con `np.linalg.solve` demuestra el mismo
principio matemático que subyace, por ejemplo, a la solución cerrada de una regresión
lineal.

## 8. Estadística aplicada a IA

Media, mediana y moda resumen la tendencia central de cada variable; varianza y desviación
estándar cuantifican su dispersión, información clave para decidir si normalizar los datos
antes de entrenar un modelo (variables con escalas muy distintas pueden dominar
injustamente el entrenamiento de algoritmos sensibles a la escala, como KNN, la regresión
logística o la regresión lineal). La detección de valores atípicos por desviación estándar ayuda a anticipar qué
registros podrían distorsionar ese entrenamiento.

## 9. Machine Learning

Se entrenan y comparan varios modelos por tipo de problema: **KNN, Decision Tree, Random
Forest y Logistic Regression** para clasificación, y **Linear Regression, Decision Tree y
Random Forest** para regresión. A cada uno se le buscan los mejores hiperparámetros con
validación cruzada usando solo los datos de entrenamiento, y luego se evalúa con métricas
estándar de Scikit-learn sobre un conjunto de prueba separado. El "mejor modelo" se
determina automáticamente por F1-score (clasificación) o R² (regresión), y es el que se usa
para las predicciones mostradas en el informe.

La Regresión logística se incorporó después de medir, con validación cruzada anidada (la
configuración se elige solo con datos de entrenamiento y se juzga con datos que el modelo no
vio), que aprendía mejor de los mismos datos que los otros tres modelos de clasificación
(por ejemplo, en Clientes pasó de 94,3 % a 98,7 % de acierto). Se probaron además grillas de
hiperparámetros más amplias para los modelos existentes y no redujeron los errores en total,
así que se dejaron como estaban.

## 10. Resultados

Los resultados varían según el dataset seleccionado (se calculan en tiempo real, no están
fijos). A modo de referencia, esta es la última ejecución completa sobre los 9 datasets, con
la misma partición 80/20 (semilla 42) y el mejor modelo que elige el sistema en cada uno:

| Dataset | Tipo | Mejor modelo | Resultado en el conjunto de prueba |
|---|---|---|---|
| Iris | Clasificación | Decision Tree | accuracy 93.3 %, recall 93.3 % (2 errores de 30 filas) |
| Diabetes | Clasificación | Logistic Regression | accuracy 71.4 %, recall 69.6 % (44 errores de 154 filas) |
| Viviendas | Regresión | Linear Regression | R² 0.977, MAE 13 195.14 |
| Vehículos | Regresión | Linear Regression | R² 0.949, MAE 1 649.24 |
| Clientes | Clasificación | Logistic Regression | accuracy 99.3 %, recall 99.3 % (1 error de 140 filas) |
| Sintético | Clasificación | Logistic Regression | accuracy 92.0 %, recall 92.0 % (16 errores de 200 filas) |
| Empleados | Clasificación | Random Forest | accuracy 72.3 %, recall 73.9 % (36 errores de 130 filas) |
| Estudiantes | Regresión | Linear Regression | R² 0.726, MAE 5.22 |
| Préstamos | Clasificación | Logistic Regression | accuracy 73.3 %, recall 76.5 % (32 errores de 120 filas) |

Los errores de clasificación sobre las filas de prueba de los seis datasets de clasificación
bajaron de **145 a 131** al incorporar la Regresión logística (por ejemplo, Clientes pasó de 9
errores de 140 a 1). En Diabetes hay un compromiso: comete 3 errores más en total (44 frente
a 41), pero detecta el 69,6 % de los casos positivos en vez del 37 %, lo que en un problema de
salud suele importar más que el número total de errores. En regresión, Linear Regression sigue
siendo el mejor modelo en Viviendas, Vehículos y Estudiantes — coherente con que esos
datasets sintéticos fueron generados con una relación mayoritariamente lineal entre sus
variables y el objetivo. Con conjuntos de prueba de 30 a 200 filas, diferencias de uno o dos
puntos equivalen a pocas filas y pueden deberse al azar de la partición.

## 11. Conclusiones

El caso práctico de DataExpert se resuelve de forma completa y verificable: cada cálculo
—desde una simple media hasta el entrenamiento de un modelo— se ejecuta en tiempo real
sobre datos reales o generados con relaciones reales, sin resultados escritos a mano. La
comparación sistemática entre implementaciones manuales y las de NumPy/Scikit-learn refuerza
la comprensión de los fundamentos matemáticos detrás de las herramientas que la empresa usa
a diario, cerrando la brecha de base sólida que motivó este desarrollo.
