/**
 * Detalles de interfaz comunes a todas las páginas: lista «Datasets» que se cierra al pulsar fuera o Escape,
 * y visor para ampliar los gráficos.
 */
(function () {
    document.addEventListener("DOMContentLoaded", () => {
        const lista = document.getElementById("cambiar-dataset");
        if (lista) {
            document.addEventListener("click", (e) => { if (lista.open && !lista.contains(e.target)) lista.open = false; });
            document.addEventListener("keydown", (e) => { if (e.key === "Escape" && lista.open) { lista.open = false; lista.querySelector("summary").focus(); } });
        }

        // Ampliar un gráfico al hacer clic (sirve también para los que se crean después, por eso se escucha en el documento).
        document.addEventListener("click", (e) => {
            const imagen = e.target.closest("img.grafico-imagen");
            if (!imagen) return;
            const visor = document.createElement("div");
            visor.className = "visor";
            visor.setAttribute("role", "dialog");
            visor.setAttribute("aria-label", "Gráfico ampliado");
            const ampliada = document.createElement("img");
            ampliada.src = imagen.src;
            ampliada.alt = imagen.alt;
            const cerrar = document.createElement("button");
            cerrar.type = "button";
            cerrar.setAttribute("aria-label", "Cerrar");
            cerrar.innerHTML = window.icono ? window.icono("cerrar") : "×";
            const quitar = () => { visor.remove(); document.removeEventListener("keydown", alTeclear); };
            const alTeclear = (ev) => { if (ev.key === "Escape") quitar(); };
            visor.addEventListener("click", quitar);
            document.addEventListener("keydown", alTeclear);
            visor.append(ampliada, cerrar);
            document.body.appendChild(visor);
            cerrar.focus();
        });
    });
})();
