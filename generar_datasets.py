"""Genera los 11 datasets que usa DataExpert IA y los guarda en data/.

- iris: dataset público real, incluido en scikit-learn (sin descarga externa).
- semillas: dataset público real de semillas de trigo (UCI «seeds», Charytanowicz et al., 2010,
  licencia CC BY 4.0), tomado de data/fuentes/seeds_dataset.txt. Columnas en español; en el
  enunciado de la actividad se llaman Area, Perimeter, ..., Class.
- cafe: 300 granos de café simulados (Arábica, Robusta, Liberica) con las mismas 7 medidas de forma
  que piden las pautas (área, perímetro, compacidad...), relacionadas entre sí; semilla fija.
- diabetes, viviendas, vehiculos, clientes, sintetico, empleados, estudiantes, prestamos:
  generados con NumPy/Pandas usando una semilla fija (random_state=42) para que los
  resultados sean reproducibles, con relaciones estadísticas reales entre variables
  (no son números aleatorios sin sentido).

Ejecutar una sola vez: python generar_datasets.py
"""

import os
import numpy as np
import pandas as pd
from sklearn.datasets import load_iris

RANDOM_STATE = 42
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Los datos se generan con nombres cortos en inglés (como iris de scikit-learn) y se guardan con
# columnas y categorías en español, que es lo que ve la persona en tablas, gráficos y el PDF.
COLUMNAS_EN_ESPANOL = {
    # iris
    "sepal_length": "largo_sépalo", "sepal_width": "ancho_sépalo",
    "petal_length": "largo_pétalo", "petal_width": "ancho_pétalo", "species": "especie",
    # diabetes
    "Pregnancies": "embarazos", "Glucose": "glucosa", "BloodPressure": "presión_arterial",
    "SkinThickness": "grosor_piel", "Insulin": "insulina", "BMI": "imc",
    "DiabetesPedigreeFunction": "antecedentes_familiares", "Age": "edad", "Outcome": "diabetes",
    # viviendas
    "area": "superficie", "bedrooms": "dormitorios", "bathrooms": "baños",
    "location_score": "puntaje_ubicación",
    # vehículos
    "engine_size": "cilindrada", "horsepower": "caballos_fuerza", "weight": "peso",
    "fuel_consumption": "consumo_combustible", "year": "año", "category": "categoría",
    # clientes
    "income": "ingresos", "purchases": "compras", "visits": "visitas", "spending": "gasto",
    "membership": "membresía", "segment": "segmento",
    # empleados
    "monthly_income": "ingreso_mensual", "years_at_company": "años_en_empresa",
    "job_satisfaction": "satisfacción_laboral", "work_life_balance": "equilibrio_vida_trabajo",
    "distance_from_home": "distancia_al_trabajo", "num_companies_worked": "empresas_anteriores",
    "overtime": "horas_extra", "attrition": "renuncia",
    # estudiantes
    "study_hours": "horas_estudio", "attendance": "asistencia", "sleep_hours": "horas_sueño",
    "previous_grade": "nota_anterior", "parental_support": "apoyo_familiar",
    "extracurricular": "actividades_extra", "final_score": "nota_final",
    # préstamos
    "annual_income": "ingreso_anual", "loan_amount": "monto_préstamo", "credit_score": "puntaje_crédito",
    "debt_to_income": "deuda_sobre_ingreso", "employment_years": "años_empleo",
    "previous_defaults": "impagos_anteriores", "loan_purpose": "motivo_préstamo",
    "loan_approved": "préstamo_aprobado",
    # varios datasets
    "categoria": "categoría", "age": "edad", "price": "precio",
}
# Las viviendas tienen «age» (años de la casa), no la edad de una persona.
COLUMNAS_POR_ARCHIVO = {"viviendas.csv": {"age": "antigüedad"}}
CATEGORIAS_EN_ESPANOL = {
    "Si": "Sí", "Basica": "Básica", "Gold": "Oro", "Educacion": "Educación",
    "Vehiculo": "Vehículo", "Economico": "Económico",
}


def en_espanol(df: pd.DataFrame, nombre_archivo: str) -> pd.DataFrame:
    """Columnas y categorías en español (los números no cambian)."""
    nombres = {**COLUMNAS_EN_ESPANOL, **COLUMNAS_POR_ARCHIVO.get(nombre_archivo, {})}
    df = df.rename(columns=nombres)
    for columna in df.columns:
        if not pd.api.types.is_numeric_dtype(df[columna]):
            df[columna] = df[columna].replace(CATEGORIAS_EN_ESPANOL)
    return df


def generar_iris():
    """Dataset público real de especies de flores (Fisher, 1936), vía scikit-learn."""
    bunch = load_iris(as_frame=True)
    df = bunch.frame.copy()
    df.columns = ["sepal_length", "sepal_width", "petal_length", "petal_width", "species"]
    df["species"] = df["species"].map(dict(enumerate(bunch.target_names)))
    return df


def generar_semillas():
    """Semillas de trigo (UCI «seeds»): 210 granos de 3 variedades medidos con rayos X.
    7 características geométricas del grano y la variedad en «clase» (en el archivo original y
    en el enunciado de la actividad: Area, Perimeter, Compactness, ..., Class)."""
    ruta = os.path.join(DATA_DIR, "fuentes", "seeds_dataset.txt")
    df = pd.read_csv(ruta, sep=r"\s+", header=None)
    df.columns = ["área", "perímetro", "compacidad", "largo_grano", "ancho_grano", "coef_asimetría",
                  "largo_surco", "clase"]
    df["clase"] = df["clase"].map({1: "Kama", 2: "Rosa", 3: "Canadiense"})
    return df


def generar_cafe():
    """Granos de café simulados: 100 granos de cada variedad (Arábica, Robusta, Liberica).

    Medidas del grano verde en mm, mm² y gramos. Liberica es el más grande, Robusta el más chico
    y redondo, y Arábica el más alargado. Cada grano se arma a partir de su largo y su ancho: el
    área y el perímetro salen de la elipse que forman (con un poco de variación, porque un grano
    no es una elipse perfecta), la compacidad de su fórmula 4·π·área / perímetro² y el peso del
    volumen del grano. Así las medidas están relacionadas entre sí, como en un grano real."""
    rng = np.random.default_rng(RANDOM_STATE)
    #            largo (media, desvío)  ancho          grosor        densidad (g por mm³ de elipsoide)
    variedades = {
        "Arábica":  ((10.2, 0.65), (6.9, 0.45), (3.8, 0.28), 0.00122),
        "Robusta":  ((8.5, 0.60), (7.0, 0.45), (4.2, 0.28), 0.00118),
        "Liberica": ((12.1, 0.85), (7.9, 0.55), (4.4, 0.32), 0.00112),
    }
    partes = []
    for variedad, ((l_m, l_d), (a_m, a_d), (g_m, g_d), densidad) in variedades.items():
        n = 100
        tamano = rng.normal(0, 1, n)  # los granos grandes son grandes en todo
        largo = l_m + l_d * (0.7 * tamano + 0.71 * rng.normal(0, 1, n))
        ancho = a_m + a_d * (0.6 * tamano + 0.8 * rng.normal(0, 1, n))
        grosor = g_m + g_d * (0.5 * tamano + 0.87 * rng.normal(0, 1, n))
        a, b = largo / 2, ancho / 2
        area = np.pi * a * b * rng.normal(1, 0.025, n)
        # Perímetro de la elipse (fórmula de Ramanujan) con el borde un poco irregular.
        perimetro = np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b))) * rng.normal(1.01, 0.012, n)
        volumen = np.pi / 6 * largo * ancho * grosor
        peso = volumen * densidad * rng.normal(1, 0.06, n)
        partes.append(pd.DataFrame({
            "área": area, "perímetro": perimetro, "largo_grano": largo, "ancho_grano": ancho,
            "grosor": grosor, "peso": peso, "clase": variedad,
        }))
    df = pd.concat(partes, ignore_index=True)
    df["compacidad"] = 4 * np.pi * df["área"] / df["perímetro"] ** 2
    df = df[["área", "perímetro", "compacidad", "largo_grano", "ancho_grano", "grosor", "peso", "clase"]]
    df = df.round({"área": 2, "perímetro": 2, "compacidad": 4, "largo_grano": 2, "ancho_grano": 2,
                   "grosor": 2, "peso": 4})
    return df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)


def generar_diabetes():
    """Indicadores clínicos y diagnóstico de diabetes (clasificación binaria).

    Estructura inspirada en el conocido dataset Pima Indians Diabetes, generada
    sintéticamente para evitar restricciones de redistribución. El resultado (Outcome)
    depende realmente de las variables clínicas mediante una función logística, no es
    una etiqueta aleatoria.
    """
    rng = np.random.default_rng(RANDOM_STATE)
    n = 768

    pregnancies = rng.poisson(3.3, n).clip(0, 17)
    glucose = rng.normal(120, 32, n).clip(0, 200)
    blood_pressure = rng.normal(69, 19, n).clip(0, 122)
    skin_thickness = rng.normal(20, 16, n).clip(0, 99)
    insulin = rng.normal(80, 115, n).clip(0, 846)
    bmi = rng.normal(32, 7.9, n).clip(0, 67)
    pedigree = rng.gamma(2.0, 0.24, n).clip(0.08, 2.5)
    age = rng.normal(33, 11.8, n).clip(21, 81).astype(int)

    # Combinación lineal real de factores de riesgo clínicos conocidos + ruido, pasada
    # por una función logística para obtener una probabilidad de diagnóstico positivo.
    z = (
        0.035 * (glucose - 120)
        + 0.09 * (bmi - 32)
        + 0.025 * (age - 33)
        + 0.4 * (pedigree - 0.5)
        + 0.01 * (pregnancies - 3)
        - 1.2
    )
    prob = 1 / (1 + np.exp(-z))
    outcome = (rng.random(n) < prob).astype(int)

    df = pd.DataFrame({
        "Pregnancies": pregnancies,
        "Glucose": glucose.round(1),
        "BloodPressure": blood_pressure.round(1),
        "SkinThickness": skin_thickness.round(1),
        "Insulin": insulin.round(1),
        "BMI": bmi.round(1),
        "DiabetesPedigreeFunction": pedigree.round(3),
        "Age": age,
        "Outcome": outcome,
    })

    # Nulos controlados (ceros clínicamente imposibles convertidos a NaN) para demostrar
    # el preprocesamiento de valores faltantes.
    for columna, tasa in [("SkinThickness", 0.05), ("Insulin", 0.07), ("BloodPressure", 0.02)]:
        idx_nulos = rng.choice(n, size=int(n * tasa), replace=False)
        df.loc[idx_nulos, columna] = np.nan

    return df


def generar_viviendas():
    """Precio de viviendas en función de área, habitaciones, baños, antigüedad y ubicación."""
    rng = np.random.default_rng(RANDOM_STATE)
    n = 600

    area = rng.normal(140, 55, n).clip(35, 400)
    bedrooms = rng.integers(1, 6, n)
    bathrooms = rng.integers(1, 4, n)
    age = rng.integers(0, 50, n)
    location_score = rng.uniform(1, 10, n)

    price = (
        1800 * area
        + 12000 * bedrooms
        + 9000 * bathrooms
        - 900 * age
        + 15000 * location_score
        + rng.normal(0, 18000, n)
        + 20000
    ).clip(20000, None)

    df = pd.DataFrame({
        "area": area.round(1),
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "age": age,
        "location_score": location_score.round(2),
        "price": price.round(0),
    })
    return df


def generar_vehiculos():
    """Precio y categoría de vehículos según sus características técnicas."""
    rng = np.random.default_rng(RANDOM_STATE)
    n = 500

    engine_size = rng.uniform(1.0, 5.0, n)
    horsepower = 40 * engine_size + rng.normal(0, 18, n) + 60
    weight = 900 + 250 * engine_size + rng.normal(0, 120, n)
    fuel_consumption = 4 + 1.6 * engine_size + rng.normal(0, 0.6, n)
    year = rng.integers(2005, 2025, n)

    price = (
        3500 * engine_size
        + 55 * horsepower
        + 6 * weight
        - 250 * (2025 - year)
        + rng.normal(0, 2200, n)
        + 4000
    ).clip(2500, None)

    categoria = pd.cut(
        price, bins=[0, 15000, 30000, np.inf], labels=["Economico", "Medio", "Lujo"]
    ).astype(str)

    df = pd.DataFrame({
        "engine_size": engine_size.round(2),
        "horsepower": horsepower.round(1),
        "weight": weight.round(1),
        "fuel_consumption": fuel_consumption.round(2),
        "year": year,
        "category": categoria,
        "price": price.round(0),
    })
    return df


def generar_clientes():
    """Comportamiento de clientes y su segmento de valor."""
    rng = np.random.default_rng(RANDOM_STATE)
    n = 700

    age = rng.integers(18, 75, n)
    income = rng.normal(2800, 1300, n).clip(400, 12000)
    membership = rng.choice(["Basica", "Premium", "Gold"], size=n, p=[0.5, 0.35, 0.15])
    membership_bonus = pd.Series(membership).map({"Basica": 0, "Premium": 1, "Gold": 2}).to_numpy()

    visits = rng.poisson(6 + membership_bonus * 3, n)
    purchases = (visits * rng.uniform(0.2, 0.6, n)).round().astype(int)
    spending = (
        purchases * rng.normal(45, 15, n).clip(5, None)
        + membership_bonus * 200
        + rng.normal(0, 80, n)
    ).clip(0, None)

    score = 0.5 * spending / (spending.std() + 1e-9) + 0.3 * membership_bonus + 0.2 * (income / income.std())
    segmento = pd.qcut(score, q=3, labels=["Bajo", "Medio", "Alto"]).astype(str)

    df = pd.DataFrame({
        "age": age,
        "income": income.round(1),
        "purchases": purchases,
        "visits": visits,
        "spending": spending.round(1),
        "membership": membership,
        "segment": segmento,
    })
    return df


def generar_sintetico():
    """Dataset sintético genérico: numéricas, categóricas, objetivo y nulos controlados."""
    rng = np.random.default_rng(RANDOM_STATE)
    n = 1000

    variable_1 = rng.normal(50, 12, n)
    variable_2 = rng.normal(0, 1, n) * 20 + 100
    variable_3 = rng.exponential(8, n)
    categoria = rng.choice(["A", "B", "C"], size=n, p=[0.4, 0.35, 0.25])
    bonus_categoria = pd.Series(categoria).map({"A": 0, "B": 8, "C": -5}).to_numpy()

    # Coeficientes x6 respecto a la version original: con los pesos chicos de antes, la
    # probabilidad quedaba casi siempre cerca de 0.5 y ningun modelo lograba superar ~65-70%
    # de accuracy (la señal se perdia en el ruido). Con esta escala el patron es lo bastante
    # fuerte para que los modelos lo aprendan bien (~85-90% accuracy) sin ser 100% predecible.
    z = 0.24 * (variable_1 - 50) + 0.18 * (variable_2 - 100) - 0.12 * variable_3 + 0.6 * bonus_categoria
    prob = 1 / (1 + np.exp(-z))
    objetivo = (rng.random(n) < prob).astype(int)

    df = pd.DataFrame({
        "variable_1": variable_1.round(2),
        "variable_2": variable_2.round(2),
        "variable_3": variable_3.round(2),
        "categoria": categoria,
        "objetivo": objetivo,
    })

    # Nulos controlados (~4%) en dos columnas numéricas, para demostrar el preprocesamiento.
    for columna in ("variable_1", "variable_3"):
        idx_nulos = rng.choice(n, size=int(n * 0.04), replace=False)
        df.loc[idx_nulos, columna] = np.nan

    return df


def generar_empleados():
    """Empleados de una empresa y si dejaron el puesto (attrition, clasificación binaria).

    La renuncia (Attrition) depende realmente de la satisfacción laboral, el salario, las
    horas extra, la distancia al trabajo y la antigüedad, combinadas mediante una función
    logística (no es una etiqueta aleatoria).
    """
    rng = np.random.default_rng(RANDOM_STATE)
    n = 650

    age = rng.integers(19, 60, n)
    monthly_income = rng.normal(3200, 1400, n).clip(900, 12000)
    years_at_company = rng.exponential(4.5, n).clip(0, 30).round(1)
    job_satisfaction = rng.integers(1, 6, n)  # escala 1-5
    work_life_balance = rng.integers(1, 5, n)  # escala 1-4
    distance_from_home = rng.exponential(9, n).clip(1, 60).round(1)
    num_companies_worked = rng.poisson(2.1, n).clip(0, 9)
    overtime = rng.choice(["Si", "No"], size=n, p=[0.3, 0.7])
    overtime_bonus = pd.Series(overtime).map({"Si": 1, "No": 0}).to_numpy()

    # Combinación lineal real de factores de riesgo de renuncia conocidos + ruido, pasada
    # por una función logística para obtener una probabilidad de renuncia.
    z = (
        1.3 * overtime_bonus
        - 0.75 * (job_satisfaction - 3)
        - 0.6 * (work_life_balance - 2.5)
        - 0.00045 * (monthly_income - 3200)
        + 0.035 * distance_from_home
        - 0.1 * years_at_company
        - 0.5
    )
    prob = 1 / (1 + np.exp(-z))
    attrition = np.where(rng.random(n) < prob, "Si", "No")

    df = pd.DataFrame({
        "age": age,
        "monthly_income": monthly_income.round(1),
        "years_at_company": years_at_company,
        "job_satisfaction": job_satisfaction,
        "work_life_balance": work_life_balance,
        "distance_from_home": distance_from_home,
        "num_companies_worked": num_companies_worked,
        "overtime": overtime,
        "attrition": attrition,
    })

    # Nulos controlados para demostrar el preprocesamiento (imputación por media/moda).
    for columna, tasa in [("monthly_income", 0.04), ("distance_from_home", 0.03)]:
        idx_nulos = rng.choice(n, size=int(n * tasa), replace=False)
        df.loc[idx_nulos, columna] = np.nan

    return df


def generar_estudiantes():
    """Rendimiento académico: nota final de un estudiante (regresión).

    La nota final depende realmente de las horas de estudio, la asistencia, las horas de
    sueño, la nota previa y el apoyo familiar, combinadas linealmente con ruido — no es un
    número inventado sin relación con las demás columnas.
    """
    rng = np.random.default_rng(RANDOM_STATE)
    n = 550

    study_hours = rng.normal(12, 5, n).clip(0, 35)
    attendance = rng.normal(82, 14, n).clip(30, 100)
    sleep_hours = rng.normal(6.8, 1.4, n).clip(3, 11)
    previous_grade = rng.normal(68, 14, n).clip(20, 100)
    parental_support = rng.choice(["Bajo", "Medio", "Alto"], size=n, p=[0.25, 0.45, 0.3])
    support_bonus = pd.Series(parental_support).map({"Bajo": 0, "Medio": 4, "Alto": 8}).to_numpy()
    extracurricular = rng.choice(["Si", "No"], size=n, p=[0.4, 0.6])
    extracurricular_bonus = pd.Series(extracurricular).map({"Si": 2, "No": 0}).to_numpy()

    final_score = (
        1.35 * study_hours
        + 0.22 * attendance
        + 1.8 * sleep_hours
        + 0.32 * previous_grade
        + support_bonus
        + extracurricular_bonus
        + rng.normal(0, 6, n)
        - 5
    ).clip(0, 100)

    df = pd.DataFrame({
        "study_hours": study_hours.round(1),
        "attendance": attendance.round(1),
        "sleep_hours": sleep_hours.round(1),
        "previous_grade": previous_grade.round(1),
        "parental_support": parental_support,
        "extracurricular": extracurricular,
        "final_score": final_score.round(1),
    })

    # Nulos controlados para demostrar el preprocesamiento.
    for columna, tasa in [("attendance", 0.05), ("sleep_hours", 0.03)]:
        idx_nulos = rng.choice(n, size=int(n * tasa), replace=False)
        df.loc[idx_nulos, columna] = np.nan

    return df


def generar_prestamos():
    """Riesgo crediticio: aprobación de un préstamo bancario (clasificación binaria).

    La aprobación depende realmente del puntaje crediticio, la relación deuda/ingreso, los
    incumplimientos previos y los años de empleo, combinados mediante una función logística.
    """
    rng = np.random.default_rng(RANDOM_STATE)
    n = 600

    age = rng.integers(21, 70, n)
    annual_income = rng.normal(38000, 16000, n).clip(8000, 150000)
    loan_amount = rng.normal(15000, 8000, n).clip(1000, 60000)
    credit_score = rng.normal(650, 90, n).clip(300, 850)
    debt_to_income = rng.uniform(0, 0.65, n)
    employment_years = rng.exponential(6, n).clip(0, 40).round(1)
    previous_defaults = rng.poisson(0.4, n).clip(0, 6)
    loan_purpose = rng.choice(
        ["Vivienda", "Vehiculo", "Educacion", "Personal"], size=n, p=[0.3, 0.25, 0.2, 0.25]
    )

    z = (
        0.012 * (credit_score - 650)
        - 3.2 * (debt_to_income - 0.3)
        - 0.55 * previous_defaults
        + 0.05 * employment_years
        - 0.00002 * (loan_amount - 15000)
        + 0.4
    )
    prob = 1 / (1 + np.exp(-z))
    loan_approved = np.where(rng.random(n) < prob, "Aprobado", "Rechazado")

    df = pd.DataFrame({
        "age": age,
        "annual_income": annual_income.round(1),
        "loan_amount": loan_amount.round(1),
        "credit_score": credit_score.round(0),
        "debt_to_income": debt_to_income.round(3),
        "employment_years": employment_years,
        "previous_defaults": previous_defaults,
        "loan_purpose": loan_purpose,
        "loan_approved": loan_approved,
    })

    # Nulos controlados para demostrar el preprocesamiento.
    for columna, tasa in [("annual_income", 0.04), ("employment_years", 0.03)]:
        idx_nulos = rng.choice(n, size=int(n * tasa), replace=False)
        df.loc[idx_nulos, columna] = np.nan

    return df


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    generadores = {
        "iris.csv": generar_iris,
        "semillas.csv": generar_semillas,
        "cafe.csv": generar_cafe,
        "diabetes.csv": generar_diabetes,
        "viviendas.csv": generar_viviendas,
        "vehiculos.csv": generar_vehiculos,
        "clientes.csv": generar_clientes,
        "sintetico.csv": generar_sintetico,
        "empleados.csv": generar_empleados,
        "estudiantes.csv": generar_estudiantes,
        "prestamos.csv": generar_prestamos,
    }
    for nombre_archivo, generador in generadores.items():
        df = en_espanol(generador(), nombre_archivo)
        ruta = os.path.join(DATA_DIR, nombre_archivo)
        df.to_csv(ruta, index=False)
        print(f"  {nombre_archivo}: {df.shape[0]} filas x {df.shape[1]} columnas -> {ruta}")


if __name__ == "__main__":
    main()
