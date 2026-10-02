/**
 * Página "Subir dataset": lee uno o varios archivos (CSV/Excel) y dice cuántas columnas y filas
 * se detectaron en cada uno. Con un archivo, muestra la vista previa donde se elige a mano qué
 * columnas usar y cuál predecir, y una foto de portada opcional. Con varios, muestra una fila por
 * archivo con la columna a predecir ya sugerida (la última) y su vista previa al tocar «Ver
 * columnas»; se agregan todos juntos y se pueden mandar a «Procesar varios».
 *
 * Usa `mostrarToast`, `escapar` e `icono`, ya definidos globalmente (app.js e iconos.js).
 */

function cssEscape(valor) {
    return (window.CSS && CSS.escape) ? CSS.escape(valor) : String(valor).replace(/["\\]/g, "\\$&");
}

const MAXIMO_ARCHIVOS = 10;

function numeroLindo(n) {
    return Number(n).toLocaleString("es-ES");
}

/** Mensaje de lo detectado: columnas y filas, y si hay columnas vacías o repetidas. */
function mensajeDetectado(data) {
    const avisos = [];
    if (data.columnas_vacias.length) {
        avisos.push(`${data.columnas_vacias.length === 1 ? "La columna" : "Las columnas"} «${data.columnas_vacias.join("», «")}» ` +
            `${data.columnas_vacias.length === 1 ? "está vacía" : "están vacías"}: conviene no usarla${data.columnas_vacias.length === 1 ? "" : "s"}.`);
    }
    if (data.columnas_repetidas.length) {
        avisos.push(`Hay encabezados repetidos; se renombraron como «${data.columnas_repetidas.join("», «")}».`);
    }
    const caja = document.createElement("div");
    caja.className = "resultado-bloque";
    caja.innerHTML = `
        <div class="detectado${avisos.length ? " con-aviso" : ""}" role="status">${icono("check")}
            <span>Archivo leído: se detectaron <b>${numeroLindo(data.total_columnas)} ${data.total_columnas === 1 ? "columna" : "columnas"}</b>
            y <b>${numeroLindo(data.filas)} filas</b> en «${escapar(data.nombre_archivo)}».
            ${avisos.length ? `<br>${escapar(avisos.join(" "))}` : "Revisa abajo la vista previa y elige las columnas."}</span>
        </div>
        <div class="cifras-subida">
            <div class="cifra-subida principal"><b>${numeroLindo(data.total_columnas)}</b><span>columnas detectadas</span></div>
            <div class="cifra-subida"><b>${numeroLindo(data.filas)}</b><span>filas de datos</span></div>
            <div class="cifra-subida"><b>${data.filas_vista_previa}</b><span>filas en la vista previa</span></div>
        </div>`;
    return caja;
}

/**
 * Tabla para elegir columnas: «Usar» y «Predecir esto» por columna, contador, buscador, botones
 * «Usar todas» / «No usar ninguna» y «Viendo columnas 1–6 de 60» que cambia al deslizar.
 */
function crearTablaColumnas(contenedor, data, opciones = {}) {
    const excluir = new Set([...data.sugeridas_excluir, ...data.columnas_vacias]);
    const usar = new Set(data.columnas.filter((c) => !excluir.has(c)));
    let objetivo = null;

    contenedor.innerHTML = `
        <div class="cuenta-columnas" aria-live="polite"></div>
        <div class="herramientas-columnas">
            <label class="buscar-columna">${icono("buscar")}<input type="search" placeholder="Buscar una columna por nombre…" aria-label="Buscar una columna"></label>
            <button type="button" class="boton" data-todas>Usar todas</button>
            <button type="button" class="boton" data-ninguna>No usar ninguna</button>
        </div>
        <div class="posicion-columnas"><span>Vista previa · primeras ${data.filas_vista_previa} filas de ${numeroLindo(data.filas)}</span>
            <span>Viendo columnas <b data-desde>1</b>–<b data-hasta>1</b> de <b>${numeroLindo(data.total_columnas)}</b></span></div>
        <div class="riel-columnas" aria-hidden="true"><span></span></div>
        <div class="tabla-subida-wrap"><table class="tabla-subida"></table></div>
        <p class="texto-ayuda">Desliza la tabla a la derecha para ver todas las columnas: ninguna se esconde.</p>`;
    const tabla = contenedor.querySelector("table");
    const envoltura = contenedor.querySelector(".tabla-subida-wrap");
    const nombreRadio = `col-objetivo-${Math.random().toString(36).slice(2)}`;

    const filaEncabezado = document.createElement("tr");
    data.columnas.forEach((columna, i) => {
        const th = document.createElement("th");
        th.dataset.columna = columna;
        th.innerHTML = `
            <span class="num-columna">${i + 1} de ${data.total_columnas}</span>
            <div class="col-nombre">${escapar(columna)}</div>
            <label class="col-check"><input type="checkbox" class="chk-usar" data-columna="${escapar(columna)}"> Usar</label>
            <label class="col-radio"><input type="radio" name="${nombreRadio}" class="rad-objetivo" data-columna="${escapar(columna)}"> Predecir esto</label>`;
        filaEncabezado.appendChild(th);
    });
    const thead = document.createElement("thead");
    thead.appendChild(filaEncabezado);
    tabla.appendChild(thead);
    const tbody = document.createElement("tbody");
    data.preview.forEach((fila) => {
        const tr = document.createElement("tr");
        data.columnas.forEach((columna) => {
            const td = document.createElement("td");
            const valor = fila[columna];
            td.textContent = (valor === null || valor === undefined || valor === "") ? "—" : valor;
            td.dataset.columna = columna;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    tabla.appendChild(tbody);

    function pintar() {
        data.columnas.forEach((columna) => {
            const esObjetivo = columna === objetivo;
            tabla.querySelectorAll(`[data-columna="${cssEscape(columna)}"]`).forEach((celda) => {
                if (celda.tagName !== "TH" && celda.tagName !== "TD") return;
                celda.classList.toggle("col-objetivo", esObjetivo);
                celda.classList.toggle("col-seleccionada", !esObjetivo && usar.has(columna));
            });
            const chk = tabla.querySelector(`.chk-usar[data-columna="${cssEscape(columna)}"]`);
            chk.checked = !esObjetivo && usar.has(columna);
            chk.disabled = esObjetivo;
            tabla.querySelector(`.rad-objetivo[data-columna="${cssEscape(columna)}"]`).checked = esObjetivo;
        });
        const enUso = data.columnas.filter((c) => c !== objetivo && usar.has(c)).length;
        const sinUsar = data.columnas.length - enUso - (objetivo ? 1 : 0);
        contenedor.querySelector(".cuenta-columnas").innerHTML =
            `<span class="chip-columna chip-usar"><i></i>${enUso} para usar</span>` +
            (objetivo ? `<span class="chip-columna chip-predecir"><i></i>Predecir: ${escapar(objetivo)}</span>`
                : `<span class="chip-columna chip-falta">Falta elegir qué predecir</span>`) +
            `<span class="chip-columna"><i></i>${sinUsar} sin usar</span>`;
        if (opciones.alCambiar) opciones.alCambiar();
    }

    function posicion() {
        const ths = Array.from(tabla.querySelectorAll("th"));
        const izquierda = envoltura.scrollLeft;
        const derecha = izquierda + envoltura.clientWidth;
        const visibles = ths.map((th, i) => [th.offsetLeft, th.offsetLeft + th.offsetWidth, i])
            .filter(([a, b]) => b > izquierda + 20 && a < derecha - 20).map((x) => x[2]);
        if (!visibles.length) return;
        contenedor.querySelector("[data-desde]").textContent = visibles[0] + 1;
        contenedor.querySelector("[data-hasta]").textContent = visibles[visibles.length - 1] + 1;
        const riel = contenedor.querySelector(".riel-columnas span");
        riel.style.width = `${Math.min(100, (envoltura.clientWidth / envoltura.scrollWidth) * 100)}%`;
        riel.style.marginLeft = `${(izquierda / envoltura.scrollWidth) * 100}%`;
    }

    tabla.addEventListener("change", (e) => {
        const columna = e.target.dataset.columna;
        if (e.target.classList.contains("chk-usar")) {
            e.target.checked ? usar.add(columna) : usar.delete(columna);
        } else if (e.target.classList.contains("rad-objetivo")) {
            objetivo = columna;
        }
        pintar();
    });
    contenedor.querySelector("[data-todas]").addEventListener("click", () => { data.columnas.forEach((c) => usar.add(c)); pintar(); });
    contenedor.querySelector("[data-ninguna]").addEventListener("click", () => { usar.clear(); pintar(); });
    contenedor.querySelector("input[type=search]").addEventListener("input", (e) => {
        const buscado = e.target.value.trim().toLowerCase();
        if (!buscado) return;
        const th = Array.from(tabla.querySelectorAll("th")).find((x) => x.dataset.columna.toLowerCase().includes(buscado));
        if (th) envoltura.scrollTo({ left: Math.max(0, th.offsetLeft - 8), behavior: "smooth" });
    });
    envoltura.addEventListener("scroll", posicion);
    window.addEventListener("resize", posicion);

    if (opciones.objetivo) objetivo = opciones.objetivo;
    pintar();
    requestAnimationFrame(posicion);

    return {
        objetivo: () => objetivo,
        features: () => data.columnas.filter((c) => c !== objetivo && usar.has(c)),
        elegirObjetivo: (columna) => { objetivo = columna; pintar(); },
        reubicar: posicion,
    };
}

/** Columna a predecir sugerida cuando se suben varios: la última que no parece identificador ni está vacía. */
function objetivoSugerido(data) {
    const excluir = new Set([...data.sugeridas_excluir, ...data.columnas_vacias]);
    const candidatas = data.columnas.filter((c) => !excluir.has(c));
    return candidatas.length ? candidatas[candidatas.length - 1] : data.columnas[data.columnas.length - 1];
}

async function confirmar(token, objetivo, columnasFeatures) {
    const respuesta = await fetch("/api/subir-dataset/confirmar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, objetivo, columnas_features: columnasFeatures }),
    });
    return respuesta.json();
}

document.addEventListener("DOMContentLoaded", () => {
    const inputArchivo = document.getElementById("input-archivo");
    const zonaSoltar = document.getElementById("zona-soltar");
    const nombreArchivoElegido = document.getElementById("nombre-archivo-elegido");
    const estadoSubida = document.getElementById("estado-subida");
    const panelConfiguracion = document.getElementById("panel-configuracion");
    const panelVarios = document.getElementById("panel-varios");
    const panelAgregados = document.getElementById("panel-agregados");
    const avisoPocasFilas = document.getElementById("aviso-pocas-filas");
    const botonConfirmar = document.getElementById("boton-confirmar-subida");
    const botonAgregarVarios = document.getElementById("boton-agregar-varios");

    const inputPortada = document.getElementById("input-portada-subida");
    const zonaPortada = document.getElementById("zona-portada-subida");
    const vistaPortada = document.getElementById("vista-portada-subida");
    const nombrePortada = document.getElementById("nombre-portada-elegida");

    let unico = null;          // { data, tabla } cuando se sube un solo archivo
    let varios = [];           // [{ data, error, tabla, objetivo, tarjeta }] cuando se suben varios
    let portadaElegida = null;

    // Foto de portada opcional: se muestra al momento y se envía después de confirmar el dataset.
    zonaPortada.addEventListener("click", () => inputPortada.click());
    zonaPortada.addEventListener("keydown", (e) => { if (e.key === "Enter") inputPortada.click(); });
    ["dragenter", "dragover"].forEach((ev) => zonaPortada.addEventListener(ev, (e) => {
        e.preventDefault(); zonaPortada.classList.add("arrastrando");
    }));
    ["dragleave", "drop"].forEach((ev) => zonaPortada.addEventListener(ev, (e) => {
        e.preventDefault(); zonaPortada.classList.remove("arrastrando");
    }));
    zonaPortada.addEventListener("drop", (e) => {
        if (e.dataTransfer.files.length) elegirPortada(e.dataTransfer.files[0]);
    });
    inputPortada.addEventListener("change", () => {
        if (inputPortada.files[0]) elegirPortada(inputPortada.files[0]);
    });

    function elegirPortada(archivo) {
        if (!/\.(jpe?g|png|webp)$/i.test(archivo.name)) {
            mostrarToast("La portada debe ser una imagen .jpg, .png o .webp", "error");
            return;
        }
        if (archivo.size > 8 * 1024 * 1024) {
            mostrarToast("La imagen pesa más de 8 MB", "error");
            return;
        }
        portadaElegida = archivo;
        nombrePortada.textContent = archivo.name;
        vistaPortada.src = URL.createObjectURL(archivo);
        vistaPortada.hidden = false;
        zonaPortada.classList.add("con-imagen");
    }

    zonaSoltar.addEventListener("click", () => inputArchivo.click());
    zonaSoltar.addEventListener("keydown", (e) => { if (e.key === "Enter") inputArchivo.click(); });
    ["dragenter", "dragover"].forEach((ev) => zonaSoltar.addEventListener(ev, (e) => {
        e.preventDefault(); zonaSoltar.classList.add("arrastrando");
    }));
    ["dragleave", "drop"].forEach((ev) => zonaSoltar.addEventListener(ev, (e) => {
        e.preventDefault(); zonaSoltar.classList.remove("arrastrando");
    }));
    zonaSoltar.addEventListener("drop", (e) => {
        if (e.dataTransfer.files.length) leerArchivos(Array.from(e.dataTransfer.files));
    });
    inputArchivo.addEventListener("change", () => {
        if (inputArchivo.files.length) leerArchivos(Array.from(inputArchivo.files));
        inputArchivo.value = "";
    });

    async function leerUno(archivo) {
        const formData = new FormData();
        formData.append("archivo", archivo);
        try {
            const respuesta = await fetch("/api/subir-dataset", { method: "POST", body: formData });
            return await respuesta.json();
        } catch (e) {
            return { ok: false, error: "Error de conexión con el servidor" };
        }
    }

    async function leerArchivos(archivos) {
        if (archivos.length > MAXIMO_ARCHIVOS) {
            mostrarToast(`Se pueden subir hasta ${MAXIMO_ARCHIVOS} archivos a la vez: se leen los primeros ${MAXIMO_ARCHIVOS}.`, "error");
            archivos = archivos.slice(0, MAXIMO_ARCHIVOS);
        }
        nombreArchivoElegido.textContent = archivos.length === 1 ? archivos[0].name : `${archivos.length} archivos elegidos`;
        panelConfiguracion.hidden = true;
        panelVarios.hidden = true;
        panelAgregados.hidden = true;
        unico = null;
        varios = [];
        estadoSubida.hidden = false;

        if (archivos.length === 1) {
            estadoSubida.innerHTML = `<span class="spinner"></span> Leyendo archivo...`;
            const data = await leerUno(archivos[0]);
            estadoSubida.hidden = true;
            if (!data.ok) {
                mostrarToast(data.error || "No se pudo leer el archivo", "error");
                return;
            }
            // Separado del fetch a propósito: si esto falla, es un error de la interfaz al mostrar
            // la vista previa (no de conexión), y conviene que se note distinto para poder arreglarlo.
            try {
                mostrarUnico(data);
                mostrarToast(`✓ Se detectaron ${data.total_columnas} columnas y ${numeroLindo(data.filas)} filas`, "exito");
            } catch (e) {
                console.error("Fallo al armar la vista previa:", e);
                mostrarToast("El archivo se leyó, pero hubo un problema mostrando la vista previa.", "error");
            }
            return;
        }

        const lista = document.getElementById("lista-archivos");
        lista.innerHTML = "";
        panelVarios.hidden = false;
        for (let i = 0; i < archivos.length; i++) {
            estadoSubida.innerHTML = `<span class="spinner"></span> Leyendo archivo ${i + 1} de ${archivos.length}: ${escapar(archivos[i].name)}…`;
            const data = await leerUno(archivos[i]);
            const item = { data: data.ok ? data : null, error: data.ok ? null : (data.error || "No se pudo leer"), nombre: archivos[i].name, tabla: null };
            if (item.data) item.objetivo = objetivoSugerido(item.data);
            varios.push(item);
            lista.appendChild(tarjetaArchivo(item));
            revisarVarios();
        }
        estadoSubida.hidden = true;
        const leidos = varios.filter((v) => v.data).length;
        mostrarToast(`✓ ${leidos} de ${archivos.length} archivos leídos`, leidos ? "exito" : "error");
    }

    function mostrarUnico(data) {
        if (data.pocas_filas) {
            avisoPocasFilas.hidden = false;
            avisoPocasFilas.textContent =
                `⚠ Este archivo tiene ${data.filas} filas. Con pocos datos el resultado puede no ` +
                "ser confiable — funciona igual, pero tómalo como orientativo.";
        } else {
            avisoPocasFilas.hidden = true;
        }
        const detectado = document.getElementById("detectado-unico");
        detectado.innerHTML = "";
        detectado.appendChild(mensajeDetectado(data));
        panelConfiguracion.hidden = false;
        unico = { data, tabla: crearTablaColumnas(document.getElementById("columnas-unico"), data) };
    }

    function tarjetaArchivo(item) {
        const tarjeta = document.createElement("article");
        tarjeta.className = "archivo-subido" + (item.error ? " error" : "");
        item.tarjeta = tarjeta;
        if (item.error) {
            tarjeta.innerHTML = `<div class="archivo-subido-cabeza"><span class="archivo-subido-nombre"></span></div>
                <p class="archivo-subido-error"></p>`;
            tarjeta.querySelector(".archivo-subido-nombre").textContent = item.nombre;
            tarjeta.querySelector(".archivo-subido-error").textContent = `No se agregará: ${item.error}`;
            return tarjeta;
        }
        const d = item.data;
        const opciones = d.columnas.map((c) => `<option value="${escapar(c)}"${c === item.objetivo ? " selected" : ""}>${escapar(c)}</option>`).join("");
        tarjeta.innerHTML = `
            <div class="archivo-subido-cabeza">
                <span class="archivo-subido-nombre"></span>
                <span class="archivo-subido-detectado">Se detectaron <b>${numeroLindo(d.total_columnas)}</b> columnas · <b>${numeroLindo(d.filas)}</b> filas</span>
                <label class="archivo-subido-objetivo">Predecir:
                    <select aria-label="Columna a predecir de ${escapar(item.nombre)}"><option value="">— elegir —</option>${opciones}</select></label>
                <button type="button" class="boton" aria-expanded="false">Ver columnas</button>
            </div>
            <div class="archivo-subido-detalle" hidden></div>`;
        tarjeta.querySelector(".archivo-subido-nombre").textContent = item.nombre;
        tarjeta.querySelector(".archivo-subido-nombre").title = item.nombre;
        const select = tarjeta.querySelector("select");
        const detalle = tarjeta.querySelector(".archivo-subido-detalle");
        const boton = tarjeta.querySelector("button");
        select.addEventListener("change", () => {
            item.objetivo = select.value || null;
            if (item.tabla) item.tabla.elegirObjetivo(item.objetivo);
            revisarVarios();
        });
        boton.addEventListener("click", () => {
            detalle.hidden = !detalle.hidden;
            boton.textContent = detalle.hidden ? "Ver columnas" : "Ocultar columnas";
            boton.setAttribute("aria-expanded", String(!detalle.hidden));
            if (!detalle.hidden && !item.tabla) {
                detalle.appendChild(mensajeDetectado(d));
                const contenedor = document.createElement("div");
                contenedor.className = "resultado-bloque";
                detalle.appendChild(contenedor);
                item.tabla = crearTablaColumnas(contenedor, d, {
                    objetivo: item.objetivo,
                    alCambiar: () => {
                        if (!item.tabla) return;
                        item.objetivo = item.tabla.objetivo();
                        select.value = item.objetivo || "";
                        revisarVarios();
                    },
                });
            } else if (!detalle.hidden) {
                item.tabla.reubicar();
            }
        });
        return tarjeta;
    }

    function featuresDe(item) {
        if (item.tabla) return item.tabla.features();
        const excluir = new Set([...item.data.sugeridas_excluir, ...item.data.columnas_vacias]);
        return item.data.columnas.filter((c) => c !== item.objetivo && !excluir.has(c));
    }

    function revisarVarios() {
        const validos = varios.filter((v) => v.data && !v.agregado);
        const faltan = validos.filter((v) => !v.objetivo);
        validos.forEach((v) => v.tarjeta.classList.toggle("falta", !v.objetivo));
        botonAgregarVarios.disabled = !validos.length || faltan.length > 0;
        botonAgregarVarios.textContent = validos.length === 1 ? "Agregar 1 dataset" : `Agregar los ${validos.length} datasets`;
        document.getElementById("nota-varios").textContent = faltan.length
            ? `Falta elegir qué predecir en «${faltan.map((v) => v.nombre).join("», «")}».`
            : validos.length ? "Listo: todos tienen su columna a predecir." : "";
    }

    botonAgregarVarios.addEventListener("click", async () => {
        botonAgregarVarios.disabled = true;
        const agregados = [];
        for (const item of varios.filter((v) => v.data && !v.agregado)) {
            const columnas = featuresDe(item);
            if (!columnas.length) {
                mostrarToast(`«${item.nombre}»: elige al menos una columna para usar (distinta de la que se predice).`, "error");
                continue;
            }
            let data;
            try {
                data = await confirmar(item.data.token, item.objetivo, columnas);
            } catch (e) {
                data = { ok: false, error: "Error de conexión con el servidor" };
            }
            if (data.ok) {
                item.agregado = true;
                agregados.push(data.dataset);
                item.tarjeta.classList.add("agregado");
                item.tarjeta.querySelector(".archivo-subido-detectado").textContent = "✓ Agregado";
            } else {
                mostrarToast(`«${item.nombre}»: ${data.error || "no se pudo agregar"}`, "error");
            }
        }
        revisarVarios();
        if (agregados.length) {
            document.getElementById("titulo-agregados").textContent =
                agregados.length === 1 ? "Se agregó 1 dataset" : `Se agregaron ${agregados.length} datasets`;
            document.getElementById("texto-agregados").textContent =
                "Ya están en Inicio y en «Procesar varios». Puedes analizarlos todos a la vez ahora.";
            const enlace = document.getElementById("enlace-procesar-agregados");
            enlace.href = `/procesar-varios?elegir=${agregados.map(encodeURIComponent).join(",")}`;
            enlace.lastChild.textContent = agregados.length === 1 ? "Procesarlo ahora" : `Procesar estos ${agregados.length} ahora`;
            panelAgregados.hidden = false;
            panelAgregados.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    });

    botonConfirmar.addEventListener("click", async () => {
        if (!unico) return;
        const objetivo = unico.tabla.objetivo();
        if (!objetivo) {
            mostrarToast("Elige cuál columna es el objetivo", "error");
            return;
        }
        const columnasFeatures = unico.tabla.features();
        if (!columnasFeatures.length) {
            mostrarToast("Elige al menos una columna para usar en la predicción", "error");
            return;
        }

        botonConfirmar.disabled = true;
        try {
            const data = await confirmar(unico.data.token, objetivo, columnasFeatures);
            if (!data.ok) {
                mostrarToast(data.error || "No se pudo confirmar", "error");
                botonConfirmar.disabled = false;
                return;
            }
            if (portadaElegida) {
                const formPortada = new FormData();
                formPortada.append("portada", portadaElegida);
                const r = await fetch(`/api/dataset/${encodeURIComponent(data.dataset)}/portada`, { method: "POST", body: formPortada });
                const d = await r.json().catch(() => ({ ok: false }));
                if (!d.ok) mostrarToast(d.error || "El dataset se guardó, pero no se pudo poner la portada.", "error");
                else if (d.aviso) window.alert(d.aviso);
            }
            window.location.href = data.redirect;
        } catch (e) {
            mostrarToast("Error de conexión con el servidor", "error");
            botonConfirmar.disabled = false;
        }
    });
});
