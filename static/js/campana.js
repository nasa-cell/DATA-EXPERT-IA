/**
 * Campana de la barra de arriba (en todas las páginas): muestra lo que se está procesando —los
 * datasets de «Procesar varios» con el paso en que van, y los entrenamientos o informes pedidos
 * desde un dataset— con su avance. Cuando algo termina, suena, muestra cuántos hay listos y un
 * aviso con «Ver resultado →». La lista solo se abre al tocarla; la escoba limpia los terminados.
 *
 * Pregunta a /api/actividad cada 1,5 s mientras hay algo en curso y cada 6 s si no. Cada respuesta
 * se comparte con la página «Procesar varios» mediante el evento «actividad».
 */
(function () {
    const NOMBRES_PASO = {
        explorar: "Explorar", preprocesar: "Preprocesar", algebra: "Álgebra lineal", estadistica: "Estadística",
        outliers: "Valores atípicos", graficos: "Gráficos", entrenar: "Entrenar modelos", evaluar: "Evaluar",
        pdf: "Informe PDF",
    };
    const CLAVE_VISTO = `dataexpert:campana-vista:${window.ARRANQUE || ""}`;

    function leerVisto() {
        try { return Number(localStorage.getItem(CLAVE_VISTO)) || 0; } catch (e) { return 0; }
    }
    function guardarVisto(valor) {
        try { localStorage.setItem(CLAVE_VISTO, String(valor)); } catch (e) { /* sin almacenamiento */ }
    }
    const esc = (t) => (window.escapar ? window.escapar(t) : String(t ?? ""));

    let ultimo = null;
    let reloj = null;
    let primera = true;

    function barritas(trabajo) {
        return trabajo.pasos.map((paso) => {
            const hecho = trabajo.hechos.includes(paso);
            const ahora = trabajo.fase === "procesando" && trabajo.actual === paso;
            const clase = hecho ? "hecho" : ahora ? "ahora" : "";
            return `<i class="${clase}" title="${esc(NOMBRES_PASO[paso])}"${ahora ? ` style="--p:${trabajo.paso_pct || 8}%"` : ""}></i>`;
        }).join("");
    }

    function textoTrabajo(t) {
        if (t.fase === "listo") return "Análisis completo";
        if (t.fase === "error") return `No se pudo terminar: ${t.error || "error"}`;
        if (t.fase === "cola") return "En cola: empieza cuando termine otro";
        const n = t.pasos.indexOf(t.actual) + 1;
        return `Paso ${n} de ${t.pasos.length} · ${NOMBRES_PASO[t.actual] || ""}`;
    }

    function filas(data) {
        const lista = [];
        data.lotes.forEach((t) => lista.push({
            tipo: "lote", color: t.color, nombre: t.nombre_dataset, texto: textoTrabajo(t), url: t.url,
            listo: t.fase === "listo", error: t.fase === "error", activo: t.fase === "cola" || t.fase === "procesando",
            pct: t.fase === "procesando" ? t.avance : null, avance: t.avance, barritas: barritas(t),
        }));
        data.activos.filter((p) => !p.lote).forEach((p) => lista.push({
            tipo: "paso", nombre: p.nombre_dataset, url: p.url, activo: true,
            texto: p.en_cola ? `${NOMBRES_PASO[p.accion] || p.accion}: en cola` : `${NOMBRES_PASO[p.accion] || p.accion}…`,
            pct: p.accion === "entrenar" && !p.en_cola ? p.pct ?? 0 : null, avance: p.pct ?? 0,
        }));
        // Pasos terminados desde un dataset (quedan hasta limpiarlos); si ese paso se está volviendo a
        // calcular, se muestra solo la fila de «en curso».
        const enCurso = (a) => data.activos.some((p) => p.dataset === a.dataset && p.accion === a.accion);
        data.avisos.filter((a) => a.accion !== "lote" && !enCurso(a)).forEach((a) => lista.push({
            tipo: "aviso", nombre: a.nombre_dataset, url: a.url, listo: a.ok, error: !a.ok,
            texto: a.ok ? `${NOMBRES_PASO[a.accion]}: terminado` : `${NOMBRES_PASO[a.accion]}: ${a.error || "error"}`,
            avance: 100,
        }));
        return lista;
    }

    function pintar(data) {
        const boton = document.getElementById("campana");
        if (!boton) return;
        const lista = filas(data);
        const activos = lista.filter((f) => f.activo);
        const terminados = lista.filter((f) => f.listo || f.error);

        const avance = activos.length ? activos.reduce((s, f) => s + (f.avance || 0), 0) / activos.length : (terminados.length ? 100 : 0);
        document.getElementById("campana-avance").style.width = `${avance}%`;
        boton.classList.toggle("trabajando", activos.length > 0);
        const globo = document.getElementById("campana-globo");
        globo.hidden = !terminados.length;
        globo.textContent = terminados.length;
        boton.setAttribute("aria-label", activos.length
            ? `Procesando ${activos.length}; ${terminados.length} terminados`
            : terminados.length ? `${terminados.length} terminados` : "No hay nada procesándose");

        document.getElementById("campana-cuenta").textContent = lista.length
            ? `${terminados.length} de ${lista.length} listos` : "";
        document.getElementById("campana-escoba").disabled = !terminados.length;
        const caja = document.getElementById("campana-items");
        caja.innerHTML = lista.length ? "" : `<p class="campana-vacia">No hay nada procesándose. Desde «Procesar varios» puedes analizar varios datasets a la vez.</p>`;
        lista.forEach((f) => {
            const fila = document.createElement("div");
            fila.className = "campana-item" + (f.listo ? " listo" : "") + (f.error ? " error" : "");
            const derecha = f.listo
                ? `<a class="campana-ver" href="${esc(f.url)}">Ver resultado →</a>`
                : f.pct !== null && f.pct !== undefined ? `<span class="campana-pct">${Math.round(f.pct)} %</span>`
                : f.error ? `<a class="campana-ver" href="${esc(f.url)}">Ver</a>` : `<span class="spinner" aria-hidden="true"></span>`;
            fila.innerHTML = `<span class="punto-tema" style="--tema-a:${esc(f.color || "#ffffff")}"></span>
                <span class="campana-texto"><b></b><span></span></span>${derecha}
                ${f.barritas ? `<span class="pasos-barra">${f.barritas}</span>` : ""}`;
            fila.querySelector("b").textContent = f.nombre;
            fila.querySelector(".campana-texto > span").textContent = f.texto;
            caja.appendChild(fila);
        });

        // Avisos nuevos: suena; los de «Procesar varios» traen además su aviso con «Ver resultado →»
        // (los del dashboard ya los avisa app.js).
        const visto = leerVisto();
        const nuevos = data.avisos.filter((a) => a.id > visto);
        if (nuevos.length) {
            guardarVisto(Math.max(...nuevos.map((a) => a.id)));
            if (!primera) {
                boton.classList.remove("suena");
                void boton.offsetWidth;
                boton.classList.add("suena");
                nuevos.filter((a) => a.accion === "lote").forEach((a) => {
                    if (typeof mostrarToast !== "function") return;
                    mostrarToast(a.ok ? `✓ Terminó «${a.nombre_dataset}».` : `⚠ «${a.nombre_dataset}» no se pudo terminar: ${a.error}`,
                        a.ok ? "exito" : "error", { url: a.url, texto: "Ver resultado →" });
                });
            }
        }
        primera = false;
        return activos.length > 0;
    }

    async function preguntar() {
        clearTimeout(reloj);
        let hayActivos = false;
        try {
            const data = await (await fetch("/api/actividad", { cache: "no-store" })).json();
            if (data.ok) {
                ultimo = data;
                hayActivos = pintar(data);
                document.dispatchEvent(new CustomEvent("actividad", { detail: data }));
            }
        } catch (e) { /* el servidor se está cerrando o reiniciando: se vuelve a intentar */ }
        reloj = setTimeout(preguntar, hayActivos ? 1500 : 6000);
    }

    function abrir(abierta) {
        const lista = document.getElementById("campana-lista");
        lista.hidden = !abierta;
        document.getElementById("campana").setAttribute("aria-expanded", String(abierta));
    }

    document.addEventListener("DOMContentLoaded", () => {
        const boton = document.getElementById("campana");
        if (!boton) return;
        const lista = document.getElementById("campana-lista");
        boton.addEventListener("click", () => abrir(lista.hidden));
        document.addEventListener("click", (e) => {
            if (!lista.hidden && !lista.contains(e.target) && !boton.contains(e.target)) abrir(false);
        });
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && !lista.hidden) { abrir(false); boton.focus(); }
        });
        document.getElementById("campana-escoba").addEventListener("click", async () => {
            try { await fetch("/api/avisos/limpiar", { method: "POST" }); } catch (e) { /* se reintenta al preguntar */ }
            preguntar();
        });
        preguntar();
    });

    window.Campana = { refrescar: preguntar, ultimo: () => ultimo };
})();
