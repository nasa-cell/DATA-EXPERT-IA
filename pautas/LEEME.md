# Pautas de la actividad — Semillas de trigo

Entregable de la actividad: las **7 pautas** resueltas sobre el dataset de semillas de trigo.

**Dataset** (`datos/semillas.csv`): 210 granos de trigo de **3 variedades** (Kama, Rosa y Canadiense), 70 de cada una, con **7 medidas** del grano tomadas con rayos X. Es el dataset «seeds» de UCI (Charytanowicz y otros, 2010, licencia CC BY 4.0). En el enunciado las columnas se llaman *Area, Perimeter, Compactness, …, Class*; acá están en español:

| En el enunciado | Acá |
|---|---|
| Area | `área` |
| Perimeter | `perímetro` |
| Compactness | `compacidad` |
| Length of kernel | `largo_grano` |
| Width of kernel | `ancho_grano` |
| Asymmetry coefficient | `coef_asimetría` |
| Length of kernel groove | `largo_surco` |
| Class | `clase` |

## Qué hay en esta carpeta

| Archivo | Para qué |
|---|---|
| `pautas.ipynb` | **El entregable principal**: cuaderno de Jupyter con las 7 pautas, cada una con su enunciado, código, resultado y conclusión. Ya está ejecutado (se ven los resultados y los gráficos sin correrlo). |
| `pautas.py` | El mismo código en un solo archivo. Se corre con `python pautas.py` y deja todo en `resultados/`. |
| `datos/semillas.csv` | El dataset. |
| `resultados/` | Lo que genera el código: gráficos, tablas, la salida completa (`salida_pautas.txt`) y el **PDF de las pautas** que arma la aplicación DataExpert IA. |
| `codigo_de_la_app/` | Las partes de la aplicación DataExpert IA que resuelven las pautas (ver abajo). |

## Dónde se cumple cada pauta

| # | Pauta | En `pautas.py` / `pautas.ipynb` | En la aplicación (`codigo_de_la_app/`) | Resultado |
|---|---|---|---|---|
| 1 | Cargar y explorar con Pandas: 7 características y nulos | `pauta_1()`: `read_csv`, `head`, `dtypes`, `isnull().sum()`, `describe` | `preprocessing_service.py` → `explorar_dataset` | 7 características, 0 nulos, 70 granos por variedad |
| 2 | Separar `clase` y normalizar con StandardScaler | `pauta_2()`: `X = datos.drop(...)`, `StandardScaler().fit_transform(X)` | `preprocessing_service.py` → `preprocesar` | Media 0 y desviación 1 en las 7 características |
| 3 | NumPy: vectores, matrices, producto punto, norma, sistema | `pauta_3()`: `np.dot`, `np.linalg.norm`, `A.T`, `np.linalg.solve` | `linear_algebra_service.py` → `ejecutar_algebra_lineal`, `_con_dataset` | v1 · v2 = 444,06; sistema resuelto y verificado |
| 4 | Media, mediana, varianza y desviación de área y perímetro; varianza y desviación de área **a mano** | `pauta_4()` con `varianza_manual()` y `desviacion_manual()` | `statistics_service.py` → `varianza_manual`, `desviacion_estandar_manual`, `calcular_estadisticas` | Área: media 14,848, mediana 14,355, varianza 8,426 (igual a mano y con NumPy) |
| 5 | Atípicos de área con 2 desviaciones estándar | `pauta_5()`: media ± 2σ | `statistics_service.py` → `detectar_outliers(k=2)` | 4 atípicos (20,71 · 20,88 · 20,97 · 21,18), todos de Rosa |
| 6 | Histograma de área y dispersión área contra perímetro por variedad | `pauta_6()` → `resultados/pauta6_*.png` | `visualization_service.py` → `generar_graficos` | Las 3 variedades forman grupos separados |
| 7 | K-Vecinos contra Árbol de Decisión por Accuracy | `pauta_7()` → `resultados/pauta7_*` | `machine_learning_service.py` (entrenamiento) y `pautas_service.py` (arma las 7 pautas) | Ver la nota de abajo |

**Nota sobre la pauta 7.** `pautas.py` usa los modelos con su configuración básica (K-Vecinos con 5 vecinos y un Árbol de Decisión sin límite) y da **K-Vecinos 90,48 %** y **Árbol de Decisión 92,86 %**. La aplicación además prueba varias configuraciones de cada modelo y elige la mejor por validación cruzada, por eso su PDF puede mostrar números un poco distintos (88,10 % y 92,86 %). Los dos usan el mismo 80 % de los datos para entrenar y el 20 % restante para probar.

## Cómo correrlo

```
pip install pandas numpy scikit-learn matplotlib
python pautas.py
```

Para abrir el cuaderno: `jupyter notebook pautas.ipynb` (o subirlo a Google Colab junto con la carpeta `datos/`).

## Conclusión general

El dataset está completo (sin nulos) y equilibrado. Área y perímetro van casi juntos (correlación 0,99) y separan bien las tres variedades: los granos de Rosa son los más grandes, los de Canadiense los más chicos y los de Kama quedan en el medio. Los dos modelos aciertan alrededor de 9 de cada 10 granos que no vieron al entrenar.
