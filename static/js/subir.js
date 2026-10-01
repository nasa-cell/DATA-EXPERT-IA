/**
 * Página "Subir dataset": lee el archivo (CSV/Excel), muestra una vista previa donde el
 * usuario elige a mano qué columnas usar (amarillo) y cuál es el objetivo (azul), puede elegir
 * una foto de portada, y confirma para que el servidor guarde el dataset y lo mande al mismo
 * dashboard que cualquier otro.
 *
 * Usa `mostrarToast` y `escapar`, ya definidos globalmente en app.js (cargado antes que este
 * script desde base.html).
 */

function cssEscape(valor) {
    return (window.CSS && CSS.escape) ? CSS.escape(valor) : String(valor).replace(/["\\]/g, "\\$&");
}

document.addEventListener("DOMContentLoaded", () => {
    const inputArchivo = document.getElementById("input-archivo");
    const zonaSoltar = document.getElementById("zona-soltar");
    const nombreArchivoElegido = document.getElementById("nombre-archivo-elegido");
    const estadoSubida = document.getElementById("estado-subida");
    const panelConfiguracion = document.getElementById("panel-configuracion");
    const tabla = document.getElementById("tabla-subida");
    const avisoPocasFilas = document.getElementById("aviso-pocas-filas");
    const botonConfirmar = document.getElementById("boton-confirmar-subida");

    const inputPortada = document.getElementById("input-portada-subida");
    const zonaPortada = document.getElementById("zona-portada-subida");
    const vistaPortada = document.getElementById("vista-portada-subida");
    const nombrePortada = document.getElementById("nombre-portada-elegida");

    let columnaObjetivo = null;
    let datosSubida = null;
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
        if (e.dataTransfer.files.length) {
            inputArchivo.files = e.dataTransfer.files;
            inputArchivo.dispatchEvent(new Event("change"));
        }
    });

    inputArchivo.addEventListener("change", () => {
        const archivo = inputArchivo.files[0];
        if (!archivo) return;
        nombreArchivoElegido.textContent = archivo.name;

        const formData = new FormData();
        formData.append("archivo", archivo);
        enviarYMostrar(() => fetch("/api/subir-dataset", { method: "POST", body: formData }));
    });

    async function enviarYMostrar(peticion) {
        estadoSubida.hidden = false;
        estadoSubida.innerHTML = `<span class="spinner"></span> Leyendo archivo...`;
        panelConfiguracion.hidden = true;

        let data;
        try {
            const respuesta = await peticion();
            data = await respuesta.json();
        } catch (e) {
            estadoSubida.hidden = true;
            console.error("Fallo la subida del archivo:", e);
            mostrarToast("Error de conexión con el servidor", "error");
            return;
        }

        estadoSubida.hidden = true;
        if (!data.ok) {
            mostrarToast(data.error || "No se pudo leer el archivo", "error");
            return;
        }

        // Separado del fetch a propósito: si esto falla, es un error de la interfaz al mostrar
        // la vista previa (no de conexión), y conviene que se note distinto para poder arreglarlo.
        try {
            datosSubida = data;
            construirTabla(data);
            panelConfiguracion.hidden = false;
            mostrarToast("✓ Archivo leído — elige las columnas", "exito");
        } catch (e) {
            console.error("Fallo al armar la vista previa:", e);
            mostrarToast("El archivo se leyó, pero hubo un problema mostrando la vista previa.", "error");
        }
    }

    function construirTabla(data) {
        columnaObjetivo = null;

        if (data.pocas_filas) {
            avisoPocasFilas.hidden = false;
            avisoPocasFilas.textContent =
                `⚠ Este archivo tiene ${data.filas} filas. Con pocos datos el resultado puede no ` +
                "ser confiable — funciona igual, pero tómalo como orientativo.";
        } else {
            avisoPocasFilas.hidden = true;
        }

        const filaEncabezado = document.createElement("tr");
        data.columnas.forEach((columna) => {
            const th = document.createElement("th");
            const usarPorDefecto = !data.sugeridas_excluir.includes(columna);
            const idBase = cssEscape(columna);

            th.innerHTML = `
                <div class="col-nombre">${escapar(columna)}</div>
                <label class="col-check">
                    <input type="checkbox" class="chk-usar" data-columna="${escapar(columna)}" ${usarPorDefecto ? "checked" : ""}>
                    Usar
                </label>
                <label class="col-radio">
                    <input type="radio" name="col-objetivo" class="rad-objetivo" data-columna="${escapar(columna)}">
                    Predecir esto
                </label>
            `;
            if (usarPorDefecto) th.classList.add("col-seleccionada");
            th.dataset.columna = columna;
            filaEncabezado.appendChild(th);
        });

        tabla.innerHTML = "";
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
                if (!data.sugeridas_excluir.includes(columna)) td.classList.add("col-seleccionada");
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        tabla.appendChild(tbody);

        tabla.querySelectorAll(".chk-usar").forEach((chk) => {
            chk.addEventListener("change", () => alternarColumna(chk.dataset.columna, chk.checked));
        });
        tabla.querySelectorAll(".rad-objetivo").forEach((rad) => {
            rad.addEventListener("change", () => marcarObjetivo(rad.dataset.columna));
        });
    }

    function celdasDeColumna(columna) {
        return tabla.querySelectorAll(`[data-columna="${cssEscape(columna)}"]`);
    }

    function alternarColumna(columna, usar) {
        celdasDeColumna(columna).forEach((celda) => {
            if (celda.tagName === "TH" || celda.tagName === "TD") celda.classList.toggle("col-seleccionada", usar);
        });
    }

    function marcarObjetivo(columna) {
        if (columnaObjetivo && columnaObjetivo !== columna) {
            celdasDeColumna(columnaObjetivo).forEach((celda) => {
                if (celda.tagName === "TH" || celda.tagName === "TD") celda.classList.remove("col-objetivo");
            });
            const chkAnterior = tabla.querySelector(`.chk-usar[data-columna="${cssEscape(columnaObjetivo)}"]`);
            if (chkAnterior) chkAnterior.disabled = false;
        }

        columnaObjetivo = columna;
        celdasDeColumna(columna).forEach((celda) => {
            if (celda.tagName === "TH" || celda.tagName === "TD") {
                celda.classList.add("col-objetivo");
                celda.classList.remove("col-seleccionada");
            }
        });
        const chk = tabla.querySelector(`.chk-usar[data-columna="${cssEscape(columna)}"]`);
        if (chk) { chk.checked = false; chk.disabled = true; }
    }

    botonConfirmar.addEventListener("click", async () => {
        if (!datosSubida) return;
        if (!columnaObjetivo) {
            mostrarToast("Elige cuál columna es el objetivo", "error");
            return;
        }
        const columnasFeatures = Array.from(tabla.querySelectorAll(".chk-usar:checked")).map((chk) => chk.dataset.columna);
        if (!columnasFeatures.length) {
            mostrarToast("Elige al menos una columna para usar en la predicción", "error");
            return;
        }

        botonConfirmar.disabled = true;
        try {
            const respuesta = await fetch("/api/subir-dataset/confirmar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ objetivo: columnaObjetivo, columnas_features: columnasFeatures }),
            });
            const data = await respuesta.json();
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
