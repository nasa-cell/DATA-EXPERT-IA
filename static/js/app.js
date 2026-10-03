/**
 * DataExpert IA — lógica del dashboard de análisis.
 * Cada botón llama a un endpoint real del servidor y renderiza el resultado devuelto.
 */

function mostrarToast(mensaje, tipo = "info", enlace = null) {
    const contenedor = document.getElementById("toast-contenedor");
    if (!contenedor) return;
    const toast = document.createElement("div");
    toast.className = `toast toast-${tipo}`;
    toast.textContent = mensaje;
    if (enlace) {
        const a = document.createElement("a");
        a.className = "toast-enlace";
        a.href = enlace.url;
        a.textContent = enlace.texto;
        toast.appendChild(a);
    }
    contenedor.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add("mostrar"));
    setTimeout(() => {
        toast.classList.remove("mostrar");
        setTimeout(() => toast.remove(), 220);
    }, enlace ? 9000 : 3600);
}

function num(valor, decimales = 2) {
    if (valor === null || valor === undefined || Number.isNaN(valor)) return "—";
    return Number(valor).toFixed(decimales);
}

function entero(valor) {
    return Number.isFinite(valor) ? Number(valor).toLocaleString("es-ES") : valor;
}

/**
 * Achica la letra de un valor de tarjeta hasta que entre en su ancho (números de muchas
 * cifras, nombres de modelo largos), en vez de partirlo o salirse de la tarjeta.
 */
function ajustarTamano(elemento) {
    elemento.style.fontSize = "";
    let tamano = parseFloat(getComputedStyle(elemento).fontSize);
    const minimo = 11;
    const noCabe = () => elemento.scrollWidth > elemento.clientWidth + 1 || elemento.scrollHeight > elemento.clientHeight * 2.4;
    while (noCabe() && tamano > minimo) {
        tamano -= 1;
        elemento.style.fontSize = `${tamano}px`;
    }
}

function ajustarTarjetas(raiz = document) {
    raiz.querySelectorAll(".tarjeta-metrica .valor, .metrica-tarjeta .valor").forEach(ajustarTamano);
}

function pct(valor, decimales = 2) {
    if (valor === null || valor === undefined) return "—";
    return `${(valor * 100).toFixed(decimales)}%`;
}

function escapar(texto) {
    return String(texto).replace(/[&<>"']/g, (c) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
}

function tabla(encabezados, filas, claseFila = () => "") {
    const th = encabezados.map((h) => `<th>${escapar(h)}</th>`).join("");
    const tr = filas.map((fila) => {
        const tds = fila.map((c) => `<td>${c === null || c === undefined ? "—" : escapar(c)}</td>`).join("");
        return `<tr class="${claseFila(fila)}">${tds}</tr>`;
    }).join("");
    return `<div class="tabla-envoltorio"><table class="tabla-datos"><thead><tr>${th}</tr></thead><tbody>${tr}</tbody></table></div>`;
}

// ---------------------------------------------------------------------------
// Estado de carga
// ---------------------------------------------------------------------------

function actualizarAvance() {
    const botones = document.querySelectorAll(".boton-accion");
    if (!botones.length) return;
    const hechos = document.querySelectorAll(".boton-accion.hecho").length;
    const texto = document.getElementById("avance-texto");
    const relleno = document.getElementById("avance-relleno");
    if (texto) texto.textContent = `${hechos} de ${botones.length} ${botones.length === 1 ? "paso hecho" : "pasos hechos"}`;
    if (relleno) relleno.style.width = `${Math.round((hechos / botones.length) * 100)}%`;
}

function marcarActivo(boton) {
    document.querySelectorAll(".boton-accion.activo").forEach((b) => b.classList.remove("activo"));
    boton.classList.add("activo");
}

function marcarHecho(boton) {
    boton.classList.add("hecho");
    actualizarAvance();
}

function setCargando(boton, activo) {
    if (!boton) return;
    boton.classList.toggle("cargando", activo);
    const estado = document.getElementById("estado-proceso");
    if (!estado) return;
    if (activo) {
        estado.hidden = false;
        estado.innerHTML = `<span class="spinner"></span> Procesando datos...`;
    } else {
        estado.hidden = true;
    }
}

// ---------------------------------------------------------------------------
// Resumen (tarjetas superiores)
// ---------------------------------------------------------------------------

async function actualizarResumen() {
    try {
        const respuesta = await fetch("/api/resumen");
        const data = await respuesta.json();
        if (!data.ok) return;

        const valores = {
            registros: entero(data.registros),
            variables: entero(data.variables),
            nulos: entero(data.nulos),
            outliers: data.outliers === null || data.outliers === undefined ? "—" : entero(data.outliers),
            modelo: data.modelo ?? "—",
            metrica: data.metricas
                ? (data.problema === "clasificacion" ? pct(data.metricas.accuracy) : num(data.metricas.r2, 3))
                : "—",
        };

        Object.entries(valores).forEach(([clave, valor]) => {
            const tarjeta = document.querySelector(`.tarjeta-metrica[data-metrica="${clave}"]`);
            if (!tarjeta) return;
            tarjeta.querySelector(".valor").textContent = valor;
            tarjeta.classList.remove("actualizada");
            void tarjeta.offsetWidth; // reinicia la animación de destello
            tarjeta.classList.add("actualizada");
            ajustarTamano(tarjeta.querySelector(".valor"));
        });
    } catch (e) { /* silencioso: el resumen es un plus, no bloquea el flujo */ }
}

// ---------------------------------------------------------------------------
// Renderizado por tipo de resultado
// ---------------------------------------------------------------------------

function renderExplorar(d) {
    return `
        <div class="resultado-bloque">
            <h3>${icono("explorar")}Exploración de datos</h3>
            ${tabla(["Registros", "Columnas", "Nulos totales", "Duplicados"],
                [[d.filas, d.columnas, d.total_nulos, d.duplicados]])}
            <h4>Tipos de datos</h4>
            ${tabla(["Columna", "Tipo", "Nulos"],
                d.nombres_columnas.map((c) => [c, d.tipos_datos[c], d.nulos_por_columna[c]]))}
            <h4>Primeras filas (head)</h4>
            ${tabla(Object.keys(d.head[0] || {}), d.head.map((f) => Object.values(f)))}
            <h4>Últimas filas (tail)</h4>
            ${tabla(Object.keys(d.tail[0] || {}), d.tail.map((f) => Object.values(f)))}
        </div>`;
}

function renderPreprocesar(d) {
    const trans = d.transformaciones.length
        ? `<ul class="transformaciones-lista">${d.transformaciones.map((t) => `<li>${escapar(t)}</li>`).join("")}</ul>`
        : "<p>El dataset ya estaba limpio: no se necesitaron transformaciones de nulos ni duplicados.</p>";

    return `
        <div class="resultado-bloque">
            <h3>${icono("preprocesar")}Preprocesamiento</h3>
            ${tabla(["Métrica", "Antes", "Después"], [
                ["Filas", d.antes.filas, d.despues.filas],
                ["Columnas", d.antes.columnas, d.despues.columnas],
                ["Valores nulos", d.antes.nulos, d.despues.nulos],
                ["Duplicados", d.antes.duplicados, d.despues.duplicados],
            ])}
            <h4>Transformaciones realizadas</h4>
            ${trans}
        </div>`;
}

function renderAlgebra(d) {
    const fmtVec = (v) => `[${v.map((n) => num(n)).join(", ")}]`;
    const fmtMat = (m) => m.map((fila) => `[${fila.map((n) => num(n)).join(", ")}]`).join("<br>");

    return `
        <div class="resultado-bloque">
            <h3>${icono("algebra")}Álgebra lineal</h3>
            <h4>Vectores</h4>
            ${tabla(["Operación", "Resultado"], [
                ["v1", fmtVec(d.vectores.v1)],
                ["v2", fmtVec(d.vectores.v2)],
                ["v1 + v2", fmtVec(d.vectores.suma)],
                ["v1 - v2", fmtVec(d.vectores.resta)],
                [`v1 × ${d.vectores.escalar}`, fmtVec(d.vectores.multiplicacion_escalar)],
                ["Producto punto (v1 · v2)", num(d.producto_punto)],
                ["Norma de v1", num(d.normas.norma_v1)],
                ["Norma de v2", num(d.normas.norma_v2)],
            ])}
            <h4>Matrices</h4>
            ${tabla(["Operación", "Resultado"], [
                ["A", fmtMat(d.matrices.A)],
                ["B", fmtMat(d.matrices.B)],
                ["A + B", fmtMat(d.matrices.suma)],
                ["A - B", fmtMat(d.matrices.resta)],
                ["A × B", fmtMat(d.matrices.multiplicacion)],
                ["Transpuesta de A", fmtMat(d.matrices.transpuesta_A)],
            ])}
            <h4>Sistema de ecuaciones lineales</h4>
            <p>${d.sistema_ecuaciones.descripcion.join(" &nbsp;|&nbsp; ")}</p>
            ${tabla(["Matriz A", "Vector b", "Solución (x, y)", "Verificación (A·x)"], [[
                fmtMat(d.sistema_ecuaciones.matriz_A),
                fmtVec(d.sistema_ecuaciones.vector_b),
                `x = ${num(d.sistema_ecuaciones.solucion.x)}, y = ${num(d.sistema_ecuaciones.solucion.y)}`,
                fmtVec(d.sistema_ecuaciones.verificacion),
            ]])}
            ${algebraConDataset(d.con_dataset, fmtVec, fmtMat)}
        </div>`;
}

// Las mismas operaciones con registros reales del dataset (cada fila es un vector).
function algebraConDataset(c, fmtVec, fmtMat) {
    if (!c) return "";
    const nombres = c.columnas.join(", ");
    const pesos = c.solucion.map((w, i) => `w${i + 1} = ${num(w)}`).join(", ");
    return `
            <h4>Con los datos del dataset</h4>
            <p>Cada registro es un vector con sus medidas (${nombres}).</p>
            ${tabla(["Operación", "Resultado"], [
                [`Registro ${c.filas[0]} (v1)`, fmtVec(c.v1)],
                [`Registro ${c.filas[1]} (v2)`, fmtVec(c.v2)],
                ["Producto punto (v1 · v2)", num(c.producto_punto)],
                ["Norma de v1", num(c.norma_v1)],
                ["Norma de v2", num(c.norma_v2)],
                ["Distancia entre v1 y v2 (la que usa K-Vecinos)", num(c.distancia)],
                ["Matriz A (registros " + c.filas_matriz.join(", ") + ")", fmtMat(c.matriz)],
                ["Transpuesta de A", fmtMat(c.transpuesta)],
                ["A × Aᵀ", fmtMat(c.producto_matriz)],
            ])}
            <p>Sistema A · w = b: qué pesos combinan ${nombres} para dar «${c.columna_b}» en esos 3 registros.</p>
            ${tabla(["Vector b (" + c.columna_b + ")", "Solución (np.linalg.solve)", "Verificación (A·w)"], [[
                fmtVec(c.vector_b), pesos, fmtVec(c.verificacion),
            ]])}`;
}

function notaFuente(d) {
    return d.fuente_datos === "preprocesado"
        ? `<p class="badge badge-mejor">Calculado sobre los datos ya preprocesados (normalizados/codificados)</p>`
        : `<p class="badge">Calculado sobre los valores reales del dataset (sin normalizar)</p>`;
}

function renderEstadistica(d) {
    return `
        <div class="resultado-bloque">
            <h3>${icono("estadistica")}Estadística</h3>
            ${notaFuente(d)}
            ${tabla(
                ["Variable", "Media", "Mediana", "Moda", "Mín", "Máx", "Rango", "Var. NumPy", "Var. manual", "Desv. NumPy", "Desv. manual"],
                d.columnas.map((c) => [
                    c.columna, num(c.media), num(c.mediana), c.moda === null ? "—" : num(c.moda),
                    num(c.minimo), num(c.maximo), num(c.rango),
                    num(c.varianza_numpy, 3), num(c.varianza_manual, 3),
                    num(c.desviacion_numpy, 3), num(c.desviacion_manual, 3),
                ])
            )}
            <p style="color: var(--texto-tenue); font-size: 0.85rem;">
                Las columnas "manual" se calcularon paso a paso con una fórmula propia, sin usar la función
                ya hecha de NumPy — y dan exactamente el mismo resultado, confirmando que la fórmula está
                bien aplicada.
            </p>
        </div>`;
}

function renderOutliers(d) {
    return `
        <div class="resultado-bloque">
            <h3>${icono("outliers")}Valores atípicos (media ± ${d.k} desviaciones estándar)</h3>
            ${notaFuente(d)}
            ${tabla(
                ["Variable", "Media", "Desv. estándar", "Límite inferior", "Límite superior", "Cantidad"],
                d.columnas.map((c) => [
                    c.columna, num(c.media), num(c.desviacion_estandar),
                    num(c.limite_inferior), num(c.limite_superior), c.cantidad_outliers,
                ])
            )}
            ${d.columnas.filter((c) => c.cantidad_outliers > 0).map((c) => `
                <h4>Valores atípicos en "${escapar(c.columna)}"</h4>
                <p>${c.valores.map((v) => num(v)).join(", ")}${c.cantidad_outliers > c.valores.length ? "…" : ""}</p>
            `).join("")}
            ${d.boxplots_url ? `
                <h4>Diagramas de caja (boxplot)</h4>
                <figure class="grafico-solo"><img class="grafico-imagen" src="${d.boxplots_url}?t=${Date.now()}" alt="Boxplots por variable" title="Clic para ampliar"></figure>
                <p>${escapar(d.boxplots_explicacion || "")}</p>
            ` : ""}
        </div>`;
}

function renderGraficos(d) {
    if (!d.graficos.length) {
        return `<div class="resultado-bloque"><h3>${icono("graficos")}Gráficos</h3><p>No hay suficientes variables numéricas para graficar.</p></div>`;
    }
    return `
        <div class="resultado-bloque">
            <h3>${icono("graficos")}Gráficos generados</h3>
            ${notaFuente(d)}
            <div class="galeria-graficos">
                ${d.graficos.map((g) => `
                <figure class="grafico-tarjeta">
                    <figcaption>${escapar(g.titulo)}</figcaption>
                    <img class="grafico-imagen" src="${g.url}?t=${Date.now()}" alt="${escapar(g.titulo)}" title="Clic para ampliar">
                </figure>`).join("")}
            </div>
        </div>`;
}

function formatoParametros(parametros) {
    if (!parametros || !Object.keys(parametros).length) return "(no tiene configuración para ajustar — usa la fórmula matemática exacta)";
    return Object.entries(parametros).map(([k, v]) => `${k}=${v}`).join(", ");
}

function renderEntrenar(d) {
    const parametros = d.parametros || {};
    const filasComparacion = Object.entries(d.comparacion).map(([nombre, m]) => {
        const esMejor = nombre === d.mejor_modelo;
        const base = [esMejor ? `${nombre} ★` : nombre];
        if (d.problema === "clasificacion") {
            base.push(pct(m.accuracy), pct(m.precision), pct(m.recall), pct(m.f1));
        } else {
            base.push(num(m.mae, 3), num(m.rmse, 3), num(m.r2, 3));
        }
        base.push(m.cv === null || m.cv === undefined ? "—" : num(m.cv, 3));
        base.push(formatoParametros(parametros[nombre]));
        return base;
    });

    const encabezados = (d.problema === "clasificacion"
        ? ["Modelo", "Accuracy", "Precision", "Recall", "F1-score"]
        : ["Modelo", "MAE", "RMSE", "R²"]).concat([`Validación cruzada (${d.metrica_cv || (d.problema === "clasificacion" ? "F1" : "R²")})`, "Mejor configuración encontrada"]);

    const modelos = d.modelos_disponibles || Object.keys(d.comparacion);
    const menuModelos = `
        <div class="menu-modelos">
            <button type="button" class="boton-tab activo" data-tab="comparar">${icono("comparar")}Comparar modelos</button>
            ${modelos.map((m) => `
                <button type="button" class="boton-tab" data-tab="modelo" data-modelo="${escapar(m)}">
                    ${icono("ver")}Ver ${escapar(m)}${m === d.mejor_modelo ? " ★" : ""}
                </button>`).join("")}
            <button type="button" class="boton-tab" data-tab="predecir">${icono("predecir")}Predecir caso nuevo</button>
            <button type="button" class="boton-tab" data-tab="lote">${icono("lote")}Predecir varios (CSV)</button>
        </div>`;

    const campos = (d.info_columnas_originales || []).map((col) => {
        if (col.tipo === "categorica") {
            const opciones = (col.categorias || [])
                .map((c) => `<option value="${escapar(c)}">${escapar(c)}</option>`).join("");
            return `
                <label class="campo-prediccion">
                    <span>${escapar(col.columna)}</span>
                    <select data-campo="${escapar(col.columna)}">${opciones}</select>
                </label>`;
        }
        return `
            <label class="campo-prediccion">
                <span>${escapar(col.columna)}</span>
                <input type="number" step="any" data-campo="${escapar(col.columna)}" placeholder="0">
            </label>`;
    }).join("");

    const vistaPrediccion = `
        <div id="vista-prediccion" hidden>
            <p class="aviso-objetivo">${icono("evaluar")}Se va a predecir: <strong>${escapar(d.objetivo)}</strong></p>
            <p>
                Carga los valores de un caso nuevo (no tiene por qué estar en el dataset) y el modelo
                ya entrenado predecirá el resultado para ese caso puntual.
            </p>
            <div class="form-prediccion">
                ${campos}
                <label class="campo-prediccion">
                    <span>Modelo a usar</span>
                    <select id="select-modelo-prediccion">
                        ${modelos.map((m) => `<option value="${escapar(m)}" ${m === d.mejor_modelo ? "selected" : ""}>${escapar(m)}${m === d.mejor_modelo ? " ★" : ""}</option>`).join("")}
                    </select>
                </label>
            </div>
            <button type="button" class="boton boton-primario" id="boton-predecir">Predecir →</button>
            <div id="resultado-prediccion"></div>
        </div>`;

    const vistaLote = `
        <div id="vista-lote" hidden>
            <p>
                Sube un archivo CSV con casos nuevos (las mismas columnas del dataset, sin la columna
                objetivo). El modelo ya entrenado predice el resultado de todos.
            </p>
            <div class="form-prediccion">
                <label class="campo-prediccion">
                    <span>Archivo CSV / Excel</span>
                    <input type="file" id="archivo-lote" accept=".csv,.xlsx">
                </label>
            </div>
            <button type="button" class="boton boton-primario" id="boton-predecir-lote">Predecir todos →</button>
            <div id="resultado-lote"></div>
        </div>`;

    return `
        <div class="resultado-bloque" data-mejor-modelo="${escapar(d.mejor_modelo)}">
            <h3>${icono("entrenar")}Entrenamiento de modelos</h3>
            <p>Tipo de problema detectado: <span class="badge badge-mejor">${d.problema === "clasificacion" ? "Clasificación" : "Regresión"}</span>
               &nbsp;·&nbsp; Entrenamiento: ${d.filas_entrenamiento} filas &nbsp;·&nbsp; Prueba: ${d.filas_prueba} filas</p>
            <p style="color: var(--texto-tenue); font-size: 0.85rem;">
                Antes de compararlos, cada modelo se probó con varias configuraciones distintas (sus
                "hiperparámetros": ajustes que se eligen antes de entrenar, no algo que el modelo aprenda
                solo), usando siempre datos de entrenamiento — nunca los de prueba — para elegir cuál
                configuración funcionó mejor. El mejor modelo (★) es el de mayor puntuación en esa
                validación cruzada; las demás columnas miden cómo le fue después con los datos de prueba.
            </p>
            ${menuModelos}
            <div id="vista-comparacion">
                ${tabla(encabezados, filasComparacion)}
                ${d.comparacion_chart_url ? `
                    <h4>Comparación visual</h4>
                    <figure class="grafico-solo"><img class="grafico-imagen" src="${d.comparacion_chart_url}?t=${Date.now()}" alt="Comparación de modelos" title="Clic para ampliar"></figure>
                    <p>${escapar(d.comparacion_chart_explicacion || "")}</p>
                ` : ""}
                ${d.importancia_url ? `
                    <h4>Variables más influyentes (mejor modelo)</h4>
                    <figure class="grafico-solo"><img class="grafico-imagen" src="${d.importancia_url}?t=${Date.now()}" alt="Importancia de variables" title="Clic para ampliar"></figure>
                    <p>${escapar(d.importancia_explicacion || "")}</p>
                ` : d.importancia_disponible === false ? `
                    <p class="badge">
                        KNN no tiene un equivalente directo a "importancia de variables" (no usa coeficientes ni divisiones por variable), por eso no se muestra este gráfico para ese modelo.
                    </p>
                ` : ""}
                <p>Mejor modelo: <strong>${escapar(d.mejor_modelo)}</strong> — usa el menú de arriba para ver cada modelo por separado (matriz de confusión / predicciones).</p>
            </div>
            <div id="vista-modelo-individual" hidden></div>
            ${vistaPrediccion}
            ${vistaLote}
        </div>`;
}

function renderResultadoPrediccion(d) {
    const objetivo = `<p class="resultado-prediccion-etiqueta">Predicción de ${escapar(d.objetivo)}</p>`;
    if (d.problema === "clasificacion") {
        const filasProba = d.probabilidades
            ? Object.entries(d.probabilidades).sort((a, b) => b[1] - a[1])
            : [];
        return `
            <div class="resultado-prediccion-caja">
                ${objetivo}
                <p class="resultado-prediccion-valor">${escapar(d.prediccion)}</p>
                ${filasProba.length ? `
                    <ul class="lista-probabilidades">
                        ${filasProba.map(([et, p]) => `<li><span>${escapar(et)}</span><span>${pct(p)}</span></li>`).join("")}
                    </ul>` : ""}
                <p class="texto-tenue">Modelo usado: ${escapar(d.modelo)}</p>
            </div>`;
    }
    return `
        <div class="resultado-prediccion-caja">
            ${objetivo}
            <p class="resultado-prediccion-valor">${num(d.prediccion, 3)}</p>
            <p class="texto-tenue">Modelo usado: ${escapar(d.modelo)}</p>
        </div>`;
}

async function manejarPredecirLote(boton) {
    const contenedor = boton.closest("#vista-lote");
    if (!contenedor) return;
    const archivo = contenedor.querySelector("#archivo-lote").files[0];
    const resultadoDiv = contenedor.querySelector("#resultado-lote");
    if (!archivo) {
        resultadoDiv.innerHTML = `<p style="color: var(--rojo);">Elige primero un archivo.</p>`;
        return;
    }

    const form = new FormData();
    form.append("archivo", archivo);

    boton.disabled = true;
    resultadoDiv.innerHTML = `<p class="placeholder"><span class="spinner"></span> Calculando...</p>`;
    try {
        const respuesta = await fetch("/api/predecir-lote", { method: "POST", body: form });
        const d = await respuesta.json();
        if (!d.ok) {
            resultadoDiv.innerHTML = `<p style="color: var(--rojo);">${escapar(d.error || "No se pudo predecir")}</p>`;
            return;
        }
        const esReg = d.problema === "regresion";
        const filas = d.filas.map((f) => [f.fila, esReg ? num(f.prediccion, 3) : f.prediccion]);
        resultadoDiv.innerHTML = `<p>${d.total} casos — predicción de <strong>${escapar(d.objetivo)}</strong></p>`
            + tabla(["Fila", `Predicción de ${d.objetivo}`], filas)
            + `<p class="texto-tenue">Modelo usado: ${escapar(d.modelo)}</p>`;
    } catch (e) {
        resultadoDiv.innerHTML = `<p style="color: var(--rojo);">Error de conexión con el servidor.</p>`;
    } finally {
        boton.disabled = false;
    }
}

async function manejarPredecir(boton) {
    const contenedor = boton.closest("#vista-prediccion");
    if (!contenedor) return;

    const valores = {};
    contenedor.querySelectorAll("[data-campo]").forEach((campo) => {
        valores[campo.dataset.campo] = campo.value;
    });
    const selectModelo = contenedor.querySelector("#select-modelo-prediccion");
    const resultadoDiv = contenedor.querySelector("#resultado-prediccion");

    boton.disabled = true;
    resultadoDiv.innerHTML = `<p class="placeholder"><span class="spinner"></span> Calculando...</p>`;

    try {
        const respuesta = await fetch("/api/predecir", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ valores, modelo: selectModelo ? selectModelo.value : null }),
        });
        const data = await respuesta.json();
        if (!data.ok) {
            resultadoDiv.innerHTML = `<p style="color: var(--rojo);">${escapar(data.error || "No se pudo predecir")}</p>`;
            return;
        }
        resultadoDiv.innerHTML = renderResultadoPrediccion(data);
    } catch (e) {
        resultadoDiv.innerHTML = `<p style="color: var(--rojo);">Error de conexión con el servidor.</p>`;
    } finally {
        boton.disabled = false;
    }
}

function contenidoEvaluar(d) {
    let tarjetasMetricas;
    if (d.problema === "clasificacion") {
        tarjetasMetricas = [
            ["Accuracy", pct(d.metricas.accuracy)], ["Precision", pct(d.metricas.precision)],
            ["Recall", pct(d.metricas.recall)], ["F1-score", pct(d.metricas.f1)],
        ];
    } else {
        tarjetasMetricas = [
            ["MAE", num(d.metricas.mae, 3)], ["MSE", num(d.metricas.mse, 3)],
            ["RMSE", num(d.metricas.rmse, 3)], ["R²", num(d.metricas.r2, 3)],
        ];
    }

    const imagen = d.matriz_confusion_url
        ? `<h4>Matriz de confusión</h4><figure class="grafico-solo"><img class="grafico-imagen" src="${d.matriz_confusion_url}?t=${Date.now()}" alt="Matriz de confusión" title="Clic para ampliar"></figure>`
        : d.real_vs_prediccion_url
            ? `<h4>Real vs. predicho</h4><figure class="grafico-solo"><img class="grafico-imagen" src="${d.real_vs_prediccion_url}?t=${Date.now()}" alt="Real vs predicho" title="Clic para ampliar"></figure>`
            : "";

    const filasPred = d.predicciones.map((p) => [p.real, p.prediccion, p.resultado]);
    const claseFila = (fila) => (fila[2] === "Correcto" ? "fila-correcta" : fila[2] === "Incorrecto" ? "fila-incorrecta" : "");

    return `
        <h3>${icono("evaluar")}Evaluación del modelo: ${escapar(d.modelo)}${d.es_mejor_modelo ? " ★" : ""}</h3>
        <div class="metricas-tarjetas">
            ${tarjetasMetricas.map(([et, val]) => `<div class="metrica-tarjeta"><span class="valor">${val}</span><span class="etiqueta">${et}</span></div>`).join("")}
        </div>
        ${imagen}
        <h4>Predicciones (muestra)</h4>
        ${tabla(["Real", "Predicción", "Resultado"], filasPred, claseFila)}`;
}

function renderEvaluar(d) {
    return `<div class="resultado-bloque">${contenidoEvaluar(d)}</div>`;
}

function renderPdf(d) {
    return `
        <div class="resultado-bloque">
            <h3>${icono("pdf")}Informe PDF</h3>
            <p>${escapar(d.mensaje)}</p>
            <a class="boton boton-primario" href="${escapar(d.ver_url)}" target="_blank" rel="noopener">Ver informe PDF</a>
            &nbsp;
            <a class="boton boton-fantasma" href="${escapar(d.descargar_url)}">Descargar</a>
        </div>`;
}

const RENDERERS = {
    explorar: renderExplorar,
    preprocesar: renderPreprocesar,
    algebra: renderAlgebra,
    estadistica: renderEstadistica,
    outliers: renderOutliers,
    graficos: renderGraficos,
    entrenar: renderEntrenar,
    evaluar: renderEvaluar,
    pdf: renderPdf,
};

const ENDPOINTS = {
    explorar: "/api/explorar",
    preprocesar: "/api/preprocesar",
    algebra: "/api/algebra",
    estadistica: "/api/estadistica",
    outliers: "/api/outliers",
    graficos: "/api/graficos",
    evaluar: "/api/evaluar",
    pdf: "/generar-pdf",
};

// ---------------------------------------------------------------------------
// Pasos ya calculados: se guardan en el servidor por dataset. Al volver a la página (o al
// pulsar un paso ya hecho) se muestran tal cual, sin recalcular; "Volver a calcular" lo repite.
// ---------------------------------------------------------------------------

const RESPUESTAS = {};

function botonDe(accion) {
    return document.querySelector(`.boton-accion[data-accion="${accion}"]`);
}

function claveUltimoPaso() {
    return `dataexpert:ultimo-paso:${window.DATASET_ACTUAL}`;
}

function recordarPaso(accion) {
    try { localStorage.setItem(claveUltimoPaso(), accion); } catch (e) { /* sin almacenamiento: no pasa nada */ }
}

function pasoRecordado() {
    try { return localStorage.getItem(claveUltimoPaso()); } catch (e) { return null; }
}

function sincronizarPasos(respuestas) {
    Object.keys(RESPUESTAS).forEach((clave) => delete RESPUESTAS[clave]);
    Object.assign(RESPUESTAS, respuestas || {});
    document.querySelectorAll(".boton-accion").forEach((b) => b.classList.toggle("hecho", Boolean(RESPUESTAS[b.dataset.accion])));
    actualizarAvance();
}

// ---------------------------------------------------------------------------
// Pautas de la actividad (dataset de semillas): una fila por pauta con su resultado; se abre con
// su tabla, sus gráficos y su conclusión. Se actualiza sola cada vez que termina un paso.
// ---------------------------------------------------------------------------
const PAUTAS_ABIERTAS = new Set();

function htmlPauta(p) {
    const abierta = PAUTAS_ABIERTAS.has(p.numero) ? " open" : "";
    const resumen = p.hecha ? escapar(p.resultado) : `Falta: «${escapar(p.falta)}»`;
    let cuerpo = "";
    if (!p.hecha) {
        cuerpo = `<p>Para cumplir esta pauta, hacé el paso <b>«${escapar(p.falta)}»</b> del flujo de análisis.</p>`;
    } else {
        if (p.caracteristicas) cuerpo += `<div class="pauta-chips">${p.caracteristicas.map((c) => `<span>${escapar(c)}</span>`).join("")}</div>`;
        if (p.tabla) cuerpo += tabla(p.tabla.encabezados, p.tabla.filas);
        if (p.graficos) cuerpo += `<div class="pauta-graficos">${p.graficos.map((u) => `<img src="${escapar(u)}" alt="" loading="lazy">`).join("")}</div>`;
        if (p.barras) {
            cuerpo += `<div class="pauta-barras">${p.barras.map(([nombre, valor]) => `
                <div class="pauta-barra"><span>${escapar(nombre)}</span><span class="riel"><i style="width:${(valor * 100).toFixed(1)}%"></i></span><span>${(valor * 100).toFixed(2).replace(".", ",")} %</span></div>`).join("")}</div>`;
        }
        cuerpo += `<p class="pauta-conclusion"><b>Conclusión:</b> ${escapar(p.conclusion)}</p>`;
    }
    return `
        <details class="pauta${p.hecha ? "" : " pendiente"}" data-numero="${p.numero}"${abierta}>
            <summary>
                <span class="pauta-numero">${p.numero}</span>
                <span class="pauta-titulo">${escapar(p.titulo)}</span>
                <span class="pauta-resultado">${resumen}</span>
                <span class="pauta-marca" aria-label="${p.hecha ? "Cumplida" : "Pendiente"}">${p.hecha ? "✔" : "…"}</span>
            </summary>
            <div class="pauta-cuerpo">${cuerpo}</div>
        </details>`;
}

async function cargarPautas() {
    const seccion = document.getElementById("pautas-actividad");
    if (!seccion) return;
    try {
        const respuesta = await fetch("/api/pautas");
        const data = await respuesta.json();
        if (!data.ok || !data.aplica) { seccion.hidden = true; return; }
        seccion.hidden = false;
        const sello = document.getElementById("pautas-sello");
        sello.textContent = `${data.cumplidas} de ${data.total} cumplidas`;
        sello.classList.toggle("incompleto", data.cumplidas < data.total);
        document.getElementById("pautas-lista").innerHTML = data.pautas.map(htmlPauta).join("") +
            (data.conclusion_general ? `<p class="pautas-conclusion-general"><b>Conclusión general:</b> ${escapar(data.conclusion_general)}</p>` : "");
        document.querySelectorAll("#pautas-lista .pauta").forEach((d) => {
            d.addEventListener("toggle", () => {
                const n = Number(d.dataset.numero);
                if (d.open) PAUTAS_ABIERTAS.add(n); else PAUTAS_ABIERTAS.delete(n);
            });
        });
    } catch (e) {
        /* sin conexión: se vuelve a intentar al terminar el próximo paso */
    }
}

async function generarPdfPautas(boton) {
    const enlaces = document.getElementById("pautas-enlaces");
    const original = boton.innerHTML;
    boton.disabled = true;
    boton.textContent = "⏳ Generando PDF…";
    enlaces.hidden = true;
    try {
        const respuesta = await fetch("/generar-pdf-pautas");
        const data = await respuesta.json();
        if (!data.ok) { mostrarToast(data.error || "No se pudo generar el PDF", "error"); return; }
        enlaces.innerHTML = `<a class="boton" href="${data.ver_url}" target="_blank" rel="noopener">👁 Ver PDF de las pautas</a>
            <a class="boton" href="${data.descargar_url}">⬇ Descargar</a>`;
        enlaces.hidden = false;
        mostrarToast(`✓ PDF de las pautas listo (${data.cumplidas} de 7 cumplidas)`, "exito");
    } catch (e) {
        mostrarToast("Error de conexión con el servidor", "error");
    } finally {
        boton.disabled = false;
        boton.innerHTML = original;
    }
}

async function recargarEstado() {
    cargarPautas();
    try {
        const respuesta = await fetch("/api/estado");
        const data = await respuesta.json();
        if (data.ok) sincronizarPasos(data.respuestas);
        return data;
    } catch (e) {
        return null;
    }
}

// ---------------------------------------------------------------------------
// Procesos que siguen en el servidor aunque se cambie de página: cualquier página pregunta
// qué está corriendo, muestra un aviso flotante mientras tanto y avisa cuando termina (con
// un enlace para volver al dataset). La página que lanzó el paso ya lo muestra ella misma.
// ---------------------------------------------------------------------------

const EN_CURSO_AQUI = new Set();
const NOMBRES_PASO = {
    explorar: "Explorar datos", preprocesar: "Preprocesar", algebra: "Álgebra lineal",
    estadistica: "Estadística", outliers: "Valores atípicos", graficos: "Gráficos",
    entrenar: "Entrenamiento", evaluar: "Evaluación", pdf: "Informe PDF", pdf_pautas: "PDF de las pautas",
};
const CLAVE_VISTO = `dataexpert:actividad-vista:${window.ARRANQUE || ""}`;
let vistoEnMemoria = null;
let vigilando = false;

function leerVisto() {
    try {
        const valor = localStorage.getItem(CLAVE_VISTO);
        if (valor !== null) return Number(valor);
    } catch (e) { /* sin almacenamiento: se usa la memoria de esta página */ }
    return vistoEnMemoria ?? 0;
}

function marcarVisto(secuencia) {
    if (!secuencia) return;
    if (secuencia <= leerVisto()) return;
    vistoEnMemoria = secuencia;
    try { localStorage.setItem(CLAVE_VISTO, String(secuencia)); } catch (e) { /* idem */ }
}

function esperar(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function marcarProcesosRemotos(activos) {
    document.querySelectorAll(".boton-accion").forEach((boton) => {
        const accion = boton.dataset.accion;
        if (EN_CURSO_AQUI.has(accion)) return;
        const remoto = activos.some((p) => p.dataset === window.DATASET_ACTUAL && p.accion === accion);
        boton.classList.toggle("cargando", remoto);
    });
}

async function alTerminarAqui(evento) {
    const boton = botonDe(evento.accion);
    if (boton) boton.classList.remove("cargando");
    await recargarEstado();
    actualizarResumen();
    const panel = document.getElementById("panel-resultado");
    if (panel && panel.dataset.esperando === evento.accion) {
        delete panel.dataset.esperando;
        if (evento.ok && RESPUESTAS[evento.accion]) mostrarGuardado(evento.accion, boton);
        else panel.innerHTML = `<div class="resultado-bloque"><p style="color: var(--rojo);">${escapar(evento.error || "No se pudo completar")}</p></div>`;
    }
    mostrarToast(evento.ok ? `✓ ${NOMBRES_PASO[evento.accion]} terminado` : `⚠ ${NOMBRES_PASO[evento.accion]}: ${evento.error}`, evento.ok ? "exito" : "error");
}

async function vigilarActividad() {
    if (vigilando) return;
    vigilando = true;
    try {
        for (;;) {
            let data;
            try {
                data = await (await fetch("/api/actividad")).json();
            } catch (e) {
                break;
            }
            if (!data.ok) break;
            const visto = leerVisto();

            for (const evento of data.terminados) {
                if (evento.secuencia <= visto) continue;
                marcarVisto(evento.secuencia);
                const esAqui = window.DATASET_ACTUAL === evento.dataset;
                if (esAqui && EN_CURSO_AQUI.has(evento.accion)) continue;
                // Los pasos de «Procesar varios» los avisa la campana una vez por dataset; aquí solo
                // se actualiza el dataset abierto, sin un aviso por cada paso.
                if (evento.lote) {
                    if (esAqui) { await recargarEstado(); actualizarResumen(); }
                    continue;
                }
                if (esAqui) {
                    await alTerminarAqui(evento);
                } else {
                    const texto = evento.ok
                        ? `✓ ${NOMBRES_PASO[evento.accion]} de «${evento.nombre_dataset}» terminado.`
                        : `⚠ ${NOMBRES_PASO[evento.accion]} de «${evento.nombre_dataset}» no se pudo completar: ${evento.error}`;
                    mostrarToast(texto, evento.ok ? "exito" : "error", { url: evento.url, texto: "Ver resultado →" });
                }
            }

            marcarProcesosRemotos(data.activos);
            if (!data.activos.length) break;
            await esperar(1500);
        }
    } finally {
        vigilando = false;
    }
}

async function reiniciarAnalisis() {
    const nombre = document.querySelector(".panel-dataset-info h1")?.textContent || "este dataset";
    if (!window.confirm(`¿Reiniciar todo el análisis de «${nombre}»?\n\nSe borra lo calculado (pasos, modelos e informe PDF) para empezar de nuevo. El dataset y su portada no se borran.`)) return;
    try {
        const respuesta = await fetch("/api/reiniciar", { method: "POST" });
        const data = await respuesta.json();
        if (!data.ok) {
            mostrarToast(data.error || "No se pudo reiniciar", "error");
            return;
        }
        try { localStorage.removeItem(claveUltimoPaso()); } catch (e) { /* idem */ }
        sincronizarPasos({});
        document.querySelectorAll(".boton-accion.activo").forEach((b) => b.classList.remove("activo"));
        document.getElementById("panel-resultado").innerHTML =
            `<p class="placeholder">Análisis reiniciado. Elige un paso del flujo para empezar de nuevo.</p>`;
        actualizarResumen();
        mostrarToast("✓ Análisis reiniciado", "exito");
    } catch (e) {
        mostrarToast("Error de conexión con el servidor", "error");
    }
}

function mostrarGuardado(accion, boton) {
    const panel = document.getElementById("panel-resultado");
    marcarActivo(boton);
    panel.innerHTML = `
        <div class="aviso-guardado">
            <span>${icono("check")}Resultado guardado: se muestra sin volver a calcular.</span>
            <button type="button" class="boton boton-fantasma boton-recalcular" data-recalcular="${escapar(accion)}">${icono("recalcular")}Volver a calcular</button>
        </div>
        ${RENDERERS[accion](RESPUESTAS[accion])}`;
    recordarPaso(accion);
}

function ejecutar(accion, boton) {
    if (accion === "entrenar") ejecutarEntrenamiento(boton);
    else ejecutarAccion(accion, boton);
}

/**
 * "Entrenar modelo" no es un fetch único: arranca la búsqueda de hiperparámetros en el
 * servidor (que corre en un hilo aparte) y va preguntando el avance cada 300ms para
 * mostrar una barra de progreso con el porcentaje EXACTO (pasos hechos / pasos totales).
 * Si se sale de la página mientras entrena, al volver se retoma la barra donde iba.
 */
async function ejecutarEntrenamiento(boton, yaEnCurso = false) {
    const panel = document.getElementById("panel-resultado");
    EN_CURSO_AQUI.add("entrenar");
    marcarActivo(boton);
    setCargando(boton, true);
    recordarPaso("entrenar");
    panel.innerHTML = `
        <div class="resultado-bloque">
            <h3>${icono("entrenar")}Entrenando modelos…</h3>
            <div class="barra-progreso-contenedor">
                <div class="barra-progreso-relleno" style="width: 0%"></div>
            </div>
            <p class="barra-progreso-texto">Iniciando búsqueda de hiperparámetros...</p>
        </div>`;

    const relleno = panel.querySelector(".barra-progreso-relleno");
    const texto = panel.querySelector(".barra-progreso-texto");
    let intervalo = null;

    try {
        if (!yaEnCurso) {
            const inicio = await fetch("/api/entrenar/iniciar");
            const dataInicio = await inicio.json();
            if (!dataInicio.ok) throw new Error(dataInicio.error || "Ocurrió un error");
        }

        await new Promise((resolve, reject) => {
            intervalo = setInterval(async () => {
                try {
                    const respuesta = await fetch("/api/entrenar/progreso");
                    const data = await respuesta.json();
                    if (!data.ok) throw new Error(data.error || "Ocurrió un error");

                    if (relleno) relleno.style.width = `${data.pct}%`;
                    if (texto) {
                        texto.textContent = data.en_cola
                            ? "En cola: empieza cuando termine otro entrenamiento (se entrenan varios a la vez)."
                            : data.total
                            ? `${data.hecho} / ${data.total} combinaciones probadas (${data.pct}%)`
                            : "Preparando los datos...";
                    }

                    if (data.listo) {
                        clearInterval(intervalo);
                        marcarVisto(data.secuencia);
                        await recargarEstado();
                        if (document.body.contains(relleno)) panel.innerHTML = RENDERERS.entrenar(data);
                        mostrarToast("✓ Modelos entrenados", "exito");
                        actualizarResumen();
                        resolve();
                    }
                } catch (errorInterno) {
                    clearInterval(intervalo);
                    reject(errorInterno);
                }
            }, 300);
        });
    } catch (e) {
        if (intervalo) clearInterval(intervalo);
        mostrarToast(e.message || "Error de conexión con el servidor", "error");
        panel.innerHTML = `<div class="resultado-bloque"><p style="color: var(--rojo);">${escapar(e.message || "Error de conexión")}</p></div>`;
    } finally {
        setCargando(boton, false);
        EN_CURSO_AQUI.delete("entrenar");
        vigilarActividad();
    }
}

async function ejecutarAccion(accion, boton) {
    const panel = document.getElementById("panel-resultado");
    EN_CURSO_AQUI.add(accion);
    marcarActivo(boton);
    setCargando(boton, true);
    recordarPaso(accion);
    try {
        const respuesta = await fetch(ENDPOINTS[accion]);
        const data = await respuesta.json();
        marcarVisto(data.secuencia);

        if (!data.ok) {
            mostrarToast(data.error || "Ocurrió un error", "error");
            panel.innerHTML = `<div class="resultado-bloque"><p style="color: var(--rojo);">${escapar(data.error || "Error desconocido")}</p></div>`;
            return;
        }

        const render = RENDERERS[accion];
        panel.innerHTML = render ? render(data) : "<p>Sin renderer para esta acción.</p>";
        recordarPaso(accion);
        await recargarEstado();
        mostrarToast("✓ Análisis completado", "exito");
        actualizarResumen();
    } catch (e) {
        mostrarToast("Error de conexión con el servidor", "error");
    } finally {
        setCargando(boton, false);
        EN_CURSO_AQUI.delete(accion);
    }
}

async function cambiarColor(color) {
    try {
        const respuesta = await fetch(`/api/dataset/${encodeURIComponent(window.DATASET_ACTUAL)}/color`, {
            method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ color }),
        });
        const data = await respuesta.json();
        if (!data.ok) {
            mostrarToast(data.error || "No se pudo cambiar el color", "error");
            return;
        }
        document.body.style.setProperty("--tema-a", data.color_a);
        document.body.style.setProperty("--tema-b", data.color_b);
        document.querySelectorAll(".muestra-color").forEach((m) => m.classList.toggle("activa", m.dataset.color === data.color_a));
        const personal = document.querySelector(".muestra-personal");
        if (personal && !document.querySelector(`.muestra-color[data-color="${data.color_a}"]`)) {
            personal.classList.add("activa");
            personal.style.setProperty("--muestra", data.color_a);
        }
        document.querySelectorAll(`.cambiar-lista a[href$="/${window.DATASET_ACTUAL}"]`).forEach((a) => a.style.setProperty("--tema-a", data.color_a));
        await recargarEstado();
        mostrarToast("✓ Color guardado (también se usa en el informe PDF)", "exito");
    } catch (e) {
        mostrarToast("Error de conexión con el servidor", "error");
    }
}

async function subirPortada(archivo) {
    const boton = document.getElementById("boton-portada");
    const form = new FormData();
    form.append("portada", archivo);
    boton.disabled = true;
    try {
        const respuesta = await fetch(`/api/dataset/${encodeURIComponent(window.DATASET_ACTUAL)}/portada`, { method: "POST", body: form });
        const data = await respuesta.json();
        if (!data.ok) {
            mostrarToast(data.error || "No se pudo guardar la portada", "error");
            return;
        }
        let imagen = document.getElementById("imagen-portada");
        if (!imagen) {
            imagen = document.createElement("img");
            imagen.id = "imagen-portada";
            imagen.alt = "";
            document.getElementById("zona-portada").prepend(imagen);
        }
        imagen.src = data.imagen_url;
        const zona = document.getElementById("zona-portada");
        zona.style.setProperty("--foto", `url("${data.imagen_url}")`);
        zona.classList.toggle("foto-contener", data.ajuste === "contener");
        boton.innerHTML = `${icono("subir")}Cambiar portada`;
        await recargarEstado();
        if (data.aviso) mostrarToast(data.aviso, "info");
        else mostrarToast("✓ Portada guardada (también sale en el informe PDF)", "exito");
    } catch (e) {
        mostrarToast("Error de conexión con el servidor", "error");
    } finally {
        boton.disabled = false;
    }
}

/**
 * Menú "Comparar modelos" / "Ver <modelo>" que aparece tras entrenar: alterna entre la
 * vista de comparación (tabla + gráficos, ya renderizada) y la evaluación individual de
 * un modelo puntual, que se pide al servidor recién al hacer clic (no todos de una).
 */
async function verModeloEnMenu(boton) {
    const contenedor = boton.closest(".resultado-bloque");
    if (!contenedor) return;
    const vistaComparacion = contenedor.querySelector("#vista-comparacion");
    const vistaIndividual = contenedor.querySelector("#vista-modelo-individual");
    const vistaPrediccion = contenedor.querySelector("#vista-prediccion");
    const vistaLote = contenedor.querySelector("#vista-lote");

    contenedor.querySelectorAll(".boton-tab").forEach((b) => b.classList.remove("activo"));
    boton.classList.add("activo");

    if (boton.dataset.tab === "comparar") {
        vistaIndividual.hidden = true;
        if (vistaPrediccion) vistaPrediccion.hidden = true;
        if (vistaLote) vistaLote.hidden = true;
        vistaComparacion.hidden = false;
        return;
    }

    if (boton.dataset.tab === "predecir" || boton.dataset.tab === "lote") {
        vistaComparacion.hidden = true;
        vistaIndividual.hidden = true;
        if (vistaPrediccion) vistaPrediccion.hidden = boton.dataset.tab !== "predecir";
        if (vistaLote) vistaLote.hidden = boton.dataset.tab !== "lote";
        return;
    }

    vistaComparacion.hidden = true;
    if (vistaPrediccion) vistaPrediccion.hidden = true;
    if (vistaLote) vistaLote.hidden = true;
    vistaIndividual.hidden = false;
    vistaIndividual.innerHTML = `<p class="placeholder"><span class="spinner"></span> Evaluando modelo...</p>`;

    try {
        const respuesta = await fetch(`/api/evaluar?modelo=${encodeURIComponent(boton.dataset.modelo)}`);
        const data = await respuesta.json();
        if (!data.ok) {
            vistaIndividual.innerHTML = `<p style="color: var(--rojo);">${escapar(data.error || "Error desconocido")}</p>`;
            return;
        }
        vistaIndividual.innerHTML = contenidoEvaluar(data);
    } catch (e) {
        vistaIndividual.innerHTML = `<p style="color: var(--rojo);">Error de conexión con el servidor.</p>`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const botonPdfPautas = document.getElementById("boton-pdf-pautas");
    if (botonPdfPautas) botonPdfPautas.addEventListener("click", () => generarPdfPautas(botonPdfPautas));

    document.querySelectorAll(".boton-accion").forEach((boton) => {
        boton.addEventListener("click", () => {
            if (boton.classList.contains("cargando")) return;
            const accion = boton.dataset.accion;
            if (RESPUESTAS[accion]) mostrarGuardado(accion, boton);
            else ejecutar(accion, boton);
        });
    });

    const panelResultado = document.getElementById("panel-resultado");
    if (panelResultado) {
        panelResultado.addEventListener("click", (evento) => {
            const botonRecalcular = evento.target.closest(".boton-recalcular");
            if (botonRecalcular) {
                const accion = botonRecalcular.dataset.recalcular;
                ejecutar(accion, botonDe(accion));
                return;
            }

            const botonTab = evento.target.closest(".boton-tab");
            if (botonTab) { verModeloEnMenu(botonTab); return; }

            const botonPredecir = evento.target.closest("#boton-predecir");
            if (botonPredecir) manejarPredecir(botonPredecir);

            const botonLote = evento.target.closest("#boton-predecir-lote");
            if (botonLote) manejarPredecirLote(botonLote);
        });
    }

    // Las tarjetas de métricas se ajustan cada vez que el panel cambia y al cambiar el tamaño de la ventana.
    if (panelResultado) new MutationObserver(() => ajustarTarjetas(panelResultado)).observe(panelResultado, { childList: true, subtree: true });
    let esperaAjuste = null;
    window.addEventListener("resize", () => {
        clearTimeout(esperaAjuste);
        esperaAjuste = setTimeout(() => ajustarTarjetas(), 120);
    });

    document.querySelectorAll(".muestra-color[data-color]").forEach((muestra) => {
        muestra.addEventListener("click", () => cambiarColor(muestra.dataset.color));
    });
    const colorPersonal = document.getElementById("color-personal");
    if (colorPersonal) colorPersonal.addEventListener("change", () => cambiarColor(colorPersonal.value));

    const inputPortada = document.getElementById("input-portada");
    if (inputPortada) {
        document.getElementById("boton-portada").addEventListener("click", () => inputPortada.click());
        inputPortada.addEventListener("change", () => {
            if (inputPortada.files[0]) subirPortada(inputPortada.files[0]);
            inputPortada.value = "";
        });
    }

    if (document.getElementById("resumen-tarjetas")) {
        actualizarResumen();
        // Recupera lo ya calculado para este dataset y vuelve a mostrar el último paso visto.
        const botonReiniciar = document.getElementById("boton-reiniciar");
        if (botonReiniciar) botonReiniciar.addEventListener("click", reiniciarAnalisis);

        recargarEstado().then((data) => {
            if (!data || !data.ok) return;
            const enCurso = data.en_curso || [];
            enCurso.forEach((accion) => { if (botonDe(accion)) botonDe(accion).classList.add("cargando"); });
            const ultimo = pasoRecordado();
            if (enCurso.includes("entrenar") && (ultimo === "entrenar" || !RESPUESTAS[ultimo])) {
                ejecutarEntrenamiento(botonDe("entrenar"), true);
            } else if (ultimo && enCurso.includes(ultimo) && botonDe(ultimo)) {
                const panel = document.getElementById("panel-resultado");
                marcarActivo(botonDe(ultimo));
                panel.dataset.esperando = ultimo;
                panel.innerHTML = `<div class="resultado-bloque"><p class="placeholder"><span class="spinner"></span> Se sigue calculando «${escapar(NOMBRES_PASO[ultimo])}»… aparecerá aquí al terminar.</p></div>`;
            } else if (ultimo && RESPUESTAS[ultimo] && botonDe(ultimo)) {
                mostrarGuardado(ultimo, botonDe(ultimo));
            }
            vigilarActividad();
        });
    } else {
        vigilarActividad();
    }
});
