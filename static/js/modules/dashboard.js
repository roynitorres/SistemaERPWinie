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



            // 6. Gráfico Donut: Recaudación del Mes
            var canvasRecaudacion = document.getElementById("chartRecaudacionMes");
            if (canvasRecaudacion && chartData.recaudacion_mes) {
                new Chart(canvasRecaudacion, {
                    type: "doughnut",
                    data: {
                        labels: chartData.recaudacion_mes.labels,
                        datasets: [{ 
                            data: chartData.recaudacion_mes.values, 
                            backgroundColor: [colors[0], "#f59e0b"], 
                            borderWidth: 0,
                            hoverOffset: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: "75%",
                        plugins: { 
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return context.label + ': C$ ' + context.parsed.toFixed(2);
                                    }
                                }
                            }
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
