/* ==========================================================================
   SISTEMA ERP WINIE — MÓDULO DE DASHBOARD Y MÉTRICAS (static/js/modules/dashboard.js)
   Reloj en tiempo real y gráficos dinámicos con Chart.js
   ========================================================================== */

(function (window, document) {
    'use strict';

    window.ERP = window.ERP || {};

    window.ERP.Dashboard = {

        /**
         * Inicializa el reloj en tiempo real
         */
        initReloj: function () {
            var horaActualEl = document.getElementById("horaActual");
            if (!horaActualEl) return;

            var actualizarHora = function () {
                var ahora = new Date();
                horaActualEl.textContent = ahora.toLocaleTimeString("es-NI", {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit"
                });
            };

            actualizarHora();
            setInterval(actualizarHora, 1000);
        },

        /**
         * Inicializa los gráficos Chart.js a partir de los datos JSON en #dashboardChartData
         */
        initCharts: function () {
            var chartDataEl = document.getElementById("dashboardChartData");
            if (!chartDataEl || typeof Chart === 'undefined') return;

            var chartData;
            try {
                chartData = JSON.parse(chartDataEl.textContent);
            } catch (e) {
                console.error("Error parseando datos del Dashboard:", e);
                return;
            }

            var colors = ["#00b0ff", "#00e676", "#ffb74d", "#ff5252", "#a78bfa"];

            // 1. Gráfico Principal: Crecimiento Anual
            var canvasAnual = document.getElementById("chartCrecimientoAnual");
            if (canvasAnual && chartData.crecimiento_anual) {
                var ctxAnual = canvasAnual.getContext("2d");
                var gradientAnual = ctxAnual.createLinearGradient(0, 0, 0, 300);
                gradientAnual.addColorStop(0, "rgba(0, 230, 118, 0.35)");
                gradientAnual.addColorStop(1, "rgba(0, 230, 118, 0.0)");

                new Chart(ctxAnual, {
                    type: "line",
                    data: {
                        labels: chartData.crecimiento_anual.labels,
                        datasets: [{
                            label: "Ventas (C$)",
                            data: chartData.crecimiento_anual.values,
                            borderColor: "#00e676",
                            borderWidth: 3,
                            backgroundColor: gradientAnual,
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: "#00e676",
                            pointBorderColor: "#13141c",
                            pointBorderWidth: 2,
                            pointRadius: 5,
                            pointHoverRadius: 8
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                backgroundColor: "#181922",
                                titleColor: "#9496a1",
                                bodyColor: "#00e676",
                                bodyFont: { weight: "bold", size: 14 },
                                borderColor: "rgba(255,255,255,0.1)",
                                borderWidth: 1,
                                padding: 12,
                                displayColors: false,
                                callbacks: {
                                    label: function (context) {
                                        return "Ventas: C$ " + context.raw.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: { color: "rgba(255, 255, 255, 0.05)" },
                                ticks: {
                                    color: "#9496a1",
                                    callback: function (value) { return "C$ " + value.toLocaleString(); }
                                }
                            },
                            x: {
                                grid: { display: false },
                                ticks: { color: "#9496a1" }
                            }
                        }
                    }
                });
            }

            // 2. Gráfico Donut: Facturas por Tipo
            var canvasTipo = document.getElementById("chartFacturasTipo");
            if (canvasTipo && chartData.facturas_tipo) {
                new Chart(canvasTipo, {
                    type: "doughnut",
                    data: {
                        labels: chartData.facturas_tipo.labels,
                        datasets: [{ data: chartData.facturas_tipo.values, backgroundColor: [colors[0], colors[2]], borderWidth: 0 }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { position: "bottom", labels: { color: "#9496a1" } } },
                        cutout: "68%"
                    }
                });
            }

            // 3. Gráfico Donut: Pagos por Estado
            var canvasPagos = document.getElementById("chartPagosEstado");
            if (canvasPagos && chartData.pagos_estado) {
                new Chart(canvasPagos, {
                    type: "doughnut",
                    data: {
                        labels: chartData.pagos_estado.labels,
                        datasets: [{ data: chartData.pagos_estado.values, backgroundColor: [colors[1], colors[3]], borderWidth: 0 }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { position: "bottom", labels: { color: "#9496a1" } } },
                        cutout: "68%"
                    }
                });
            }

            // 4. Gráfico Línea: Ventas últimos 7 días
            var canvasVentas7 = document.getElementById("chartVentas7");
            if (canvasVentas7 && chartData.ventas_7_dias) {
                new Chart(canvasVentas7, {
                    type: "line",
                    data: {
                        labels: chartData.ventas_7_dias.labels,
                        datasets: [{ data: chartData.ventas_7_dias.values, borderColor: colors[0], backgroundColor: "rgba(0,176,255,.12)", fill: true, tension: .35, pointRadius: 4 }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { beginAtZero: true, grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#9496a1" } },
                            x: { grid: { display: false }, ticks: { color: "#9496a1" } }
                        }
                    }
                });
            }

            // 5. Gráfico Barras: Top Productos más vendidos
            var canvasTopProd = document.getElementById("chartTopProductos");
            if (canvasTopProd && chartData.top_productos) {
                new Chart(canvasTopProd, {
                    type: "bar",
                    data: {
                        labels: chartData.top_productos.labels,
                        datasets: [{ data: chartData.top_productos.values, backgroundColor: colors[1], borderRadius: 6 }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { beginAtZero: true, grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#9496a1" } },
                            x: { grid: { display: false }, ticks: { color: "#9496a1" } }
                        }
                    }
                });
            }
        },

        init: function () {
            this.initReloj();
            this.initCharts();
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        window.ERP.Dashboard.init();
    });

})(window, document);
