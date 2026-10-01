/**
 * Íconos de DataExpert IA: dibujos propios en SVG (trazo grueso, sin emojis del sistema, que se ven distintos en cada equipo).
 * Los elementos con data-icono="nombre" se rellenan solos; en el JavaScript se usa icono("nombre").
 */
(function () {
    const D = {
        // Pasos del análisis
        explorar: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
        preprocesar: '<path d="M4 5h16l-6.2 7.4v5.6l-3.6 1.8v-7.4z"/>',
        algebra: '<path d="M8 4H5v16h3M16 4h3v16h-3"/><path d="M9.5 9h.01M12 9h.01M14.5 9h.01M9.5 12h.01M12 12h.01M14.5 12h.01M9.5 15h.01M12 15h.01M14.5 15h.01" stroke-width="2.8"/>',
        estadistica: '<path d="M18 5H6.5l6 7-6 7H18"/>',
        outliers: '<path d="M12 4l9 15.5H3z"/><path d="M12 10v4.2M12 17.2h.01"/>',
        graficos: '<path d="M4 20V4M4 20h16"/><path d="M8.5 16v-4M12.5 16V8M16.5 16v-6"/>',
        entrenar: '<rect x="6.5" y="6.5" width="11" height="11" rx="2"/><path d="M10 10h4v4h-4zM9.5 3.5v3M14.5 3.5v3M9.5 17.5v3M14.5 17.5v3M3.5 9.5h3M3.5 14.5h3M17.5 9.5h3M17.5 14.5h3"/>',
        evaluar: '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><path d="M12 12h.01" stroke-width="3"/>',
        pdf: '<path d="M7 3.5h7.5L19 8v12.5H7z"/><path d="M14.5 3.5V8H19M9.5 13h6M9.5 16.5h6"/>',
        // Interfaz
        cerrar: '<path d="M6 6l12 12M18 6L6 18"/>',
        subir: '<path d="M12 16V5M7.5 9.5L12 5l4.5 4.5M4.5 15v3.5h15V15"/>',
        archivo: '<path d="M7 3.5h7.5L19 8v12.5H7z"/><path d="M14.5 3.5V8H19"/>',
        flecha: '<path d="M5 12h14M13 6l6 6-6 6"/>',
        abajo: '<path d="M6 9l6 6 6-6"/>',
        volver: '<path d="M19 12H5M11 6l-6 6 6 6"/>',
        check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
        casa: '<path d="M3.5 11L12 4l8.5 7M6 9.5V20h12V9.5M10 20v-5.5h4V20"/>',
        comparar: '<path d="M4 20V4M4 20h16"/><path d="M8.5 16v-4M12.5 16V8M16.5 16v-6"/>',
        ver: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="2.8"/>',
        predecir: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/>',
        lote: '<path d="M4 7.5h6l1.8 2H20V19H4z"/>',
        recalcular: '<path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3"/><path d="M19.5 4.5v4h-4"/>',
        estrella: '<path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.8 6.8 19.6l1-5.8L3.5 9.7l5.9-.8z"/>',
        // Un ícono por dataset
        iris: '<circle cx="12" cy="12" r="2.2"/><path d="M12 9.8c-2.6-1.2-2.6-5.2 0-6.3 2.6 1.1 2.6 5.1 0 6.3zM14.2 12c1.2-2.6 5.2-2.6 6.3 0-1.1 2.6-5.1 2.6-6.3 0zM12 14.2c2.6 1.2 2.6 5.2 0 6.3-2.6-1.1-2.6-5.1 0-6.3zM9.8 12c-1.2 2.6-5.2 2.6-6.3 0 1.1-2.6 5.1-2.6 6.3 0z"/>',
        diabetes: '<path d="M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0 1 12 7.6 4.3 4.3 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10z"/><path d="M6.5 12h3l1.5-2.5 2 4 1.5-1.5h3"/>',
        viviendas: '<path d="M3.5 11L12 4l8.5 7M6 9.5V20h12V9.5M10 20v-5.5h4V20"/>',
        vehiculos: '<path d="M5 16.5V12l1.8-4.5h10.4L19 12v4.5M3.5 16.5h17M5 12h14"/><circle cx="7.8" cy="17" r="1.6"/><circle cx="16.2" cy="17" r="1.6"/>',
        clientes: '<path d="M3.5 4.5h2.2l2.2 10.5h9.6l1.8-7.5H7"/><circle cx="9.5" cy="19" r="1.4"/><circle cx="16.5" cy="19" r="1.4"/>',
        sintetico: '<path d="M9.5 3.5h5M10.3 3.5v6L5 18.6a1.6 1.6 0 0 0 1.4 2.4h11.2a1.6 1.6 0 0 0 1.4-2.4L13.7 9.5v-6"/><path d="M7.8 15h8.4"/>',
        empleados: '<rect x="3.5" y="7.5" width="17" height="12" rx="2"/><path d="M9 7.5V5.5h6v2M3.5 13h17"/>',
        estudiantes: '<path d="M2.5 9.5L12 5l9.5 4.5L12 14z"/><path d="M6.5 11.8v4.3c0 1.3 2.5 2.7 5.5 2.7s5.5-1.4 5.5-2.7v-4.3M21.5 9.5V15"/>',
        prestamos: '<path d="M3.5 9.5L12 4l8.5 5.5"/><path d="M6 12v6M10 12v6M14 12v6M18 12v6M3.5 20.5h17"/>',
        subido: '<path d="M7 3.5h7.5L19 8v12.5H7z"/><path d="M14.5 3.5V8H19"/>',
    };
    window.ICONOS = D;
    window.icono = (nombre) =>
        `<span class="icono" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false">${D[nombre] || D.archivo}</svg></span>`;

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll("span.icono[data-icono]").forEach((el) => {
            el.setAttribute("aria-hidden", "true");
            el.innerHTML = `<svg viewBox="0 0 24 24" focusable="false">${D[el.dataset.icono] || D.archivo}</svg>`;
        });
    });
})();
