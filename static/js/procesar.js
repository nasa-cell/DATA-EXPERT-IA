/**
 * Página «Procesar varios»: elegir datasets, pasos y cuántos a la vez, mandarlos al servidor y
 * mostrar el avance de cada uno. El avance llega de la campana (evento «actividad»), que ya
 * pregunta al servidor; así hay un solo pedido aunque estén las dos cosas en pantalla.
 */
(function () {
    const PASOS = [
        ["explorar", "Explorar"], ["preprocesar", "Preprocesar"], ["algebra", "Álgebra lineal"],
        ["estadistica", "Estadística"], ["outliers", "Valores atípicos"], ["graficos", "Gráficos"],
        ["entrenar", "Entrenar modelos"], ["evaluar", "Evaluar"], ["pdf", "Informe PDF"],
    ];
    const NOMBRE = Object.fromEntries(PASOS);
    // Igual que en el servidor: no se puede entrenar sin preprocesar, ni evaluar sin entrenar.
    const NECESITA = { entrenar: ["preprocesar"], evaluar: ["preprocesar", "entrenar"] };
    const PREAJUSTES = {
        todo: PASOS.map((p) => p[0]),
        entrenar: ["preprocesar", "entrenar", "evaluar"],
        explorar: ["explorar", "estadistica", "graficos"],
    };

    let pasosElegidos = new Set(PREAJUSTES.todo);
    let aLaVez = Number(document.querySelector("#varios-a-la-vez [aria-pressed='true']")?.dataset.vez || 3);

    const $ = (id) => document.getElementById(id);
    const casillas = () => Array.from(document.querySelectorAll("#varios-elegir input[type=checkbox]"));

    function conNecesarios() {
        const s = new Set(pasosElegidos);
        pasosElegidos.forEach((p) => (NECESITA[p] || []).forEach((n) => s.add(n)));
        return PASOS.map((p) => p[0]).filter((p) => s.has(p));
    }

    function armarPasos() {
        const caja = $("varios-pasos");
        PASOS.forEach(([clave, nombre]) => {
            const etiqueta = document.createElement("label");
            etiqueta.className = "varios-paso";
            etiqueta.innerHTML = `<input type="checkbox" value="${clave}">${window.icono ? window.icono(clave) : ""}<span>${nombre}</span>`;
            etiqueta.querySelector("input").addEventListener("change", (e) => {
                e.target.checked ? pasosElegidos.add(clave) : pasosElegidos.delete(clave);
                marcarPreajuste("elegir");
                actualizar();
            });
            caja.appendChild(etiqueta);
        });
    }

    function marcarPreajuste(nombre) {
        document.querySelectorAll("#varios-preajustes [data-preajuste]").forEach((b) =>
            b.setAttribute("aria-pressed", String(b.dataset.preajuste === nombre)));
    }

    function actualizar() {
        const finales = conNecesarios();
        const agregados = finales.filter((p) => !pasosElegidos.has(p));
        document.querySelectorAll("#varios-pasos input").forEach((chk) => {
            chk.checked = finales.includes(chk.value);
            chk.closest(".varios-paso").classList.toggle("obligado", agregados.includes(chk.value));
        });
        $("nota-pasos").textContent = agregados.length
            ? `Se agregó «${agregados.map((p) => NOMBRE[p]).join("» y «")}» porque los otros pasos lo necesitan antes.`
            : `${finales.length} de 9 pasos elegidos.`;
        const n = casillas().filter((c) => c.checked).length;
        const boton = $("boton-procesar");
        boton.disabled = !n || !finales.length;
        $("texto-procesar").textContent = !n ? "Elige al menos un dataset"
            : !finales.length ? "Elige al menos un paso"
            : `Procesar ${n} ${n === 1 ? "dataset" : "datasets"} · ${finales.length} ${finales.length === 1 ? "paso" : "pasos"}`;
    }

    function barritas(t) {
        return PASOS.map(([clave, nombre]) => {
            if (!t.pasos.includes(clave)) return `<i class="omitido" title="${nombre}: no elegido"></i>`;
            const hecho = t.hechos.includes(clave);
            const ahora = t.fase === "procesando" && t.actual === clave;
            return `<i class="${hecho ? "hecho" : ahora ? "ahora" : ""}" title="${nombre}"${ahora ? ` style="--p:${t.paso_pct || 8}%"` : ""}></i>`;
        }).join("");
    }

    function pintarAvance(data) {
        const trabajos = data.lotes || [];
        const caja = $("varios-trabajos");
        if (!trabajos.length) {
            caja.innerHTML = `<p class="varios-vacio">Todavía no hay nada procesándose. Elige datasets y pasos arriba y toca el botón.</p>`;
            $("varios-resumen").innerHTML = "";
            return;
        }
        const cuenta = (f) => trabajos.filter((t) => t.fase === f).length;
        $("varios-resumen").innerHTML = [
            `<span class="badge">${cuenta("listo")} de ${trabajos.length} listos</span>`,
            cuenta("procesando") ? `<span class="badge">${cuenta("procesando")} procesando</span>` : "",
            cuenta("cola") ? `<span class="badge">${cuenta("cola")} en cola</span>` : "",
            cuenta("error") ? `<span class="badge badge-aviso">${cuenta("error")} con error</span>` : "",
            `<span class="badge">${data.a_la_vez} a la vez</span>`,
        ].join("");
        caja.innerHTML = "";
        trabajos.forEach((t) => {
            const tarjeta = document.createElement("article");
            tarjeta.className = `varios-trabajo fase-${t.fase}`;
            tarjeta.style.setProperty("--tema-a", t.color || "#ffffff");
            const estado = { cola: "En cola", procesando: "Procesando", listo: "Listo", error: "Error" }[t.fase];
            let texto;
            if (t.fase === "listo") {
                texto = t.omitidos.length
                    ? `Terminado · ${t.pasos.length - t.omitidos.length} pasos nuevos, ${t.omitidos.length} ya estaban hechos`
                    : `Los ${t.pasos.length} pasos terminados`;
            } else if (t.fase === "error") {
                texto = `Se detuvo: ${t.error}`;
            } else if (t.fase === "cola") {
                texto = "Empieza cuando termine otro";
            } else {
                texto = `Paso ${t.pasos.indexOf(t.actual) + 1} de ${t.pasos.length} · ${NOMBRE[t.actual] || ""}`;
            }
            tarjeta.innerHTML = `
                <div class="varios-trabajo-cabeza"><span class="punto-tema"></span><b class="varios-trabajo-nombre"></b><span class="estado-chip">${estado}</span></div>
                <div class="pasos-barra">${barritas(t)}</div>
                <div class="varios-trabajo-paso"><span></span><b>${t.fase === "procesando" ? `${t.avance} %` : ""}</b></div>
                <a class="boton boton-primario varios-ver" href="${escapar(t.url)}"${t.fase === "listo" || t.fase === "error" ? "" : ' aria-disabled="true" tabindex="-1"'}>${t.fase === "error" ? "Ver el dataset" : "Ver resultado"}${window.icono ? window.icono("flecha") : " →"}</a>`;
            tarjeta.querySelector(".varios-trabajo-nombre").textContent = t.nombre_dataset;
            tarjeta.querySelector(".varios-trabajo-paso span").textContent = texto;
            caja.appendChild(tarjeta);
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        armarPasos();
        actualizar();
        casillas().forEach((c) => c.addEventListener("change", actualizar));
        $("elegir-todos").addEventListener("click", () => { casillas().forEach((c) => { c.checked = true; }); actualizar(); });
        $("elegir-ninguno").addEventListener("click", () => { casillas().forEach((c) => { c.checked = false; }); actualizar(); });

        document.querySelectorAll("#varios-preajustes [data-preajuste]").forEach((b) => b.addEventListener("click", () => {
            marcarPreajuste(b.dataset.preajuste);
            if (PREAJUSTES[b.dataset.preajuste]) pasosElegidos = new Set(PREAJUSTES[b.dataset.preajuste]);
            actualizar();
        }));

        document.querySelectorAll("#varios-a-la-vez [data-vez]").forEach((b) => b.addEventListener("click", async () => {
            aLaVez = Number(b.dataset.vez);
            document.querySelectorAll("#varios-a-la-vez [data-vez]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
            try {
                await fetch("/api/lote/a-la-vez", {
                    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ a_la_vez: aLaVez }),
                });
            } catch (e) { /* se manda de nuevo al tocar «Procesar» */ }
            if (window.Campana) window.Campana.refrescar();
        }));

        $("boton-procesar").addEventListener("click", async () => {
            const boton = $("boton-procesar");
            const datasets = casillas().filter((c) => c.checked).map((c) => c.value);
            boton.disabled = true;
            try {
                const respuesta = await fetch("/api/lote", {
                    method: "POST", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ datasets, pasos: conNecesarios(), a_la_vez: aLaVez }),
                });
                const data = await respuesta.json();
                if (!data.ok) {
                    mostrarToast(data.error || "No se pudo empezar", "error");
                } else {
                    let nota = data.agregados === 1 ? "Se agregó 1 dataset al avance." : `Se agregaron ${data.agregados} datasets al avance.`;
                    if (data.ya_estaban.length) nota += ` Ya se estaban procesando: ${data.ya_estaban.join(", ")}.`;
                    $("nota-procesar").textContent = `${nota} Puedes cambiar de página: siguen procesándose y la campana te avisa.`;
                    mostrarToast("✓ Procesando: mira el avance abajo o en la campana", "exito");
                    $("t-avance").scrollIntoView({ behavior: "smooth", block: "start" });
                }
            } catch (e) {
                mostrarToast("Error de conexión con el servidor", "error");
            }
            actualizar();
            if (window.Campana) window.Campana.refrescar();
        });

        document.addEventListener("actividad", (e) => pintarAvance(e.detail));
        if (window.Campana && window.Campana.ultimo()) pintarAvance(window.Campana.ultimo());
    });
})();
