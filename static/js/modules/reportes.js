/* ==========================================================================
   SISTEMA ERP WINIE — MÓDULO DE REPORTES FINANCIEROS (static/js/modules/reportes.js)
   Gestión desacoplada del informe financiero, gráficos, tablas y filtros
   ========================================================================== */

(function (window, document) {
    'use strict';

    window.ERP = window.ERP || {};

    window.ERP.Reportes = {
        datosGlobales: {},

        fmt: function (n) {
            return "C$ " + parseFloat(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        },

        fmtNum: function (n) {
            return parseFloat(n || 0).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
        },

        empty: function (cols, msg) {
            msg = msg || "Sin registros";
            return `<tr><td colspan="${cols}"><div class="rpt-empty"><i class="bi bi-inbox"></i><p>${msg}</p></div></td></tr>`;
        },

        mostrarSeccion: function (id, btn) {
            document.querySelectorAll('.seccion-reporte').forEach(function (s) { s.classList.add('oculto'); });
            document.querySelectorAll('#botones-secciones .btn').forEach(function (b) {
                b.classList.remove('active');
                b.classList.add('btn--outline');
            });
            var sec = document.getElementById('seccion-' + id);
            if (sec) sec.classList.remove('oculto');

            var targetBtn = btn || document.getElementById('btn-nav-' + id);
            if (targetBtn) {
                targetBtn.classList.remove('btn--outline');
                targetBtn.classList.add('active');
            }
        },

        filtrarVentas: function (tipo) {
            var self = this;
            ['btn-v-todas', 'btn-v-contado', 'btn-v-credito'].forEach(function (id) {
                var b = document.getElementById(id);
                if (b) {
                    b.classList.remove('active');
                    b.classList.add('btn--outline');
                }
            });
            var activo = tipo === 'TODAS' ? 'btn-v-todas' : tipo === 'CONTADO' ? 'btn-v-contado' : 'btn-v-credito';
            var ba = document.getElementById(activo);
            if (ba) { ba.classList.remove('btn--outline'); ba.classList.add('active'); }

            if (!self.datosGlobales.ventas) return;
            var lista = tipo === 'TODAS' ? self.datosGlobales.ventas.lista
                : tipo === 'CONTADO' ? self.datosGlobales.ventas.lista_contado
                    : self.datosGlobales.ventas.lista_credito;

            var tbody = document.getElementById('tabla-ventas-body');
            var total = 0;
            var cantTotal = 0;
            if (!tbody) return;

            if (!lista || lista.length === 0) {
                tbody.innerHTML = self.empty(6);
            } else {
                tbody.innerHTML = lista.map(function (v) {
                    total += v.total;
                    cantTotal += (v.cantidad || 0);
                    var badgeCls = v.tipo === 'CONTADO' ? 'badge-pill-apex--active' : 'badge-pill-apex';
                    return `<tr class="data-table__row">
                        <td class="data-table__cell" style="font-weight:600; color:var(--color-primary);">${v.factura}</td>
                        <td class="data-table__cell" style="color:#ffffff;">${v.cliente}</td>
                        <td class="data-table__cell" style="font-weight:600; color:#cbd5e1;">${v.fecha}</td>
                        <td class="data-table__cell text-center"><span class="badge-pill-apex ${badgeCls}">${v.tipo}</span></td>
                        <td class="data-table__cell text-center" style="font-weight:700; color:#ffffff;">${self.fmtNum(v.cantidad || 0)}</td>
                        <td class="data-table__cell text-end" style="font-weight:700; color:#00e676;">${self.fmt(v.total)}</td>
                    </tr>`;
                }).join('');
            }
            if (document.getElementById('subtotal-ventas-cant')) {
                document.getElementById('subtotal-ventas-cant').textContent = self.fmtNum(cantTotal);
            }
            if (document.getElementById('subtotal-ventas')) document.getElementById('subtotal-ventas').textContent = self.fmt(total);
            if (document.getElementById('subtotal-ventas-contado')) document.getElementById('subtotal-ventas-contado').textContent = self.fmt(self.datosGlobales.ventas.contado);
            if (document.getElementById('subtotal-ventas-credito')) document.getElementById('subtotal-ventas-credito').textContent = self.fmt(self.datosGlobales.ventas.credito);
        },

        renderizarDatos: function (data) {
            var self = this;
            self.datosGlobales = data;

            // KPIs Resumen General
            if (document.getElementById('kpi-inversion')) document.getElementById('kpi-inversion').textContent = self.fmt(data.resumen.inversion);
            if (document.getElementById('kpi-inversion-proy')) {
                document.getElementById('kpi-inversion-proy').textContent = "Proyección Venta: " + self.fmt(data.compras ? data.compras.proyeccion_venta : 0);
            }
            if (document.getElementById('kpi-ventas')) document.getElementById('kpi-ventas').textContent = self.fmt(data.resumen.total_ventas);
            if (document.getElementById('kpi-cobrado')) document.getElementById('kpi-cobrado').textContent = self.fmt(data.resumen.total_cobrado);
            if (document.getElementById('kpi-por-cobrar')) document.getElementById('kpi-por-cobrar').textContent = self.fmt(data.resumen.pendiente);
            if (document.getElementById('kpi-ganancia-real')) document.getElementById('kpi-ganancia-real').textContent = self.fmt(data.resumen.ganancia_real);
            if (document.getElementById('kpi-ganancia-proy')) document.getElementById('kpi-ganancia-proy').textContent = self.fmt(data.resumen.ganancia_proyectada);

            // Ventas completas
            self.filtrarVentas('TODAS');

            // Mejores clientes
            var mejores = data.mejores_clientes || [];
            if (document.getElementById('badge-mejores-clientes')) {
                document.getElementById('badge-mejores-clientes').textContent = mejores.length;
            }
            if (document.getElementById('subtotal-mejores-clientes')) {
                document.getElementById('subtotal-mejores-clientes').textContent = self.fmt(data.total_ventas_clientes);
            }
            var tbodyMej = document.getElementById('tabla-mejores-clientes-body');
            if (tbodyMej) {
                if (mejores.length === 0) {
                    tbodyMej.innerHTML = self.empty(5, 'Sin ventas este mes');
                } else {
                    tbodyMej.innerHTML = mejores.map(function (c, i) {
                        var trClass = i === 0 ? 'data-table__row top-buyer' : 'data-table__row';
                        var tag = i === 0 ? `<span class="top-buyer-tag"><i class="bi bi-trophy-fill me-1"></i> Top Comprador</span>` : '';
                        return `<tr class="${trClass}">
                            <td class="data-table__cell" style="font-weight:700; color:#94a3b8;">#${i + 1}</td>
                            <td class="data-table__cell" style="font-weight:600; color:#ffffff;">${c.nombre}${tag}</td>
                            <td class="data-table__cell" style="color:#cbd5e1;">${c.telefono}</td>
                            <td class="data-table__cell text-center" style="font-weight:700; color:#ffffff;">${c.cantidad_compras}</td>
                            <td class="data-table__cell text-end" style="font-weight:700; color:#00e676;">${self.fmt(c.total)}</td>
                        </tr>`;
                    }).join('');
                }
            }

            // Clientes nuevos
            var nuevos = data.lista_clientes_nuevos || [];
            if (document.getElementById('badge-clientes-nuevos')) {
                document.getElementById('badge-clientes-nuevos').textContent = nuevos.length;
            }
            if (document.getElementById('subtotal-clientes-nuevos')) {
                document.getElementById('subtotal-clientes-nuevos').textContent = nuevos.length;
            }
            var tbodyNuevos = document.getElementById('tabla-clientes-nuevos-body');
            if (tbodyNuevos) {
                if (nuevos.length === 0) {
                    tbodyNuevos.innerHTML = self.empty(4, 'Sin clientes nuevos este mes');
                } else {
                    tbodyNuevos.innerHTML = nuevos.map(function (c, i) {
                        return `<tr class="data-table__row">
                            <td class="data-table__cell" style="font-weight:700; color:#94a3b8;">#${i + 1}</td>
                            <td class="data-table__cell" style="font-weight:600; color:#ffffff;">${c.nombre}</td>
                            <td class="data-table__cell" style="color:#cbd5e1;">${c.telefono}</td>
                            <td class="data-table__cell text-end" style="font-weight:600; color:#cbd5e1;">${c.fecha}</td>
                        </tr>`;
                    }).join('');
                }
            }

            // Productos comprados del mes
            var comprasList = (data.compras && data.compras.lista) ? data.compras.lista : [];
            if (document.getElementById('badge-cant-items-compras')) {
                document.getElementById('badge-cant-items-compras').textContent = `${comprasList.length} item${comprasList.length !== 1 ? 's' : ''}`;
            }
            if (document.getElementById('subtotal-unidades-compradas')) {
                document.getElementById('subtotal-unidades-compradas').textContent = self.fmtNum(data.compras ? data.compras.unidades_compradas : 0);
            }
            if (document.getElementById('subtotal-inversion-compras')) {
                document.getElementById('subtotal-inversion-compras').textContent = self.fmt(data.compras ? data.compras.inversion : 0);
            }
            if (document.getElementById('subtotal-proyeccion-ventas')) {
                document.getElementById('subtotal-proyeccion-ventas').textContent = self.fmt(data.compras ? data.compras.proyeccion_venta : 0);
            }
            if (document.getElementById('foot-total-cant')) {
                document.getElementById('foot-total-cant').textContent = self.fmtNum(data.compras ? data.compras.unidades_compradas : 0);
            }
            if (document.getElementById('foot-total-inversion')) {
                document.getElementById('foot-total-inversion').textContent = self.fmt(data.compras ? data.compras.inversion : 0);
            }
            if (document.getElementById('foot-total-proyeccion')) {
                document.getElementById('foot-total-proyeccion').textContent = self.fmt(data.compras ? data.compras.proyeccion_venta : 0);
            }
            var tbodyProds = document.getElementById('tabla-productos-comprados-body');
            if (tbodyProds) {
                if (comprasList.length === 0) {
                    tbodyProds.innerHTML = self.empty(8, 'Sin productos comprados este mes');
                } else {
                    tbodyProds.innerHTML = comprasList.map(function (p, i) {
                        return `<tr class="data-table__row">
                            <td class="data-table__cell" style="font-weight:700; color:#94a3b8;">#${i + 1}</td>
                            <td class="data-table__cell" style="font-weight:600; color:#ffffff;">
                                ${p.nombre}
                                <div style="font-size:0.75rem; color:#94a3b8;">${p.codigo}</div>
                            </td>
                            <td class="data-table__cell text-info" style="font-weight:600;"><i class="bi bi-truck me-1"></i>${p.proveedor || '-'}</td>
                            <td class="data-table__cell text-center" style="font-weight:700; color:#ffffff;">${self.fmtNum(p.cantidad)}</td>
                            <td class="data-table__cell text-end" style="font-weight:700; color:#ffb74d;">${self.fmt(p.precio_compra)}</td>
                            <td class="data-table__cell text-end" style="font-weight:700; color:#cbd5e1;">${self.fmt(p.precio_venta)}</td>
                            <td class="data-table__cell text-end" style="font-weight:700; color:#00e676;">${self.fmt(p.inversion)}</td>
                            <td class="data-table__cell text-end" style="font-weight:700; color:#00b0ff;">${self.fmt(p.proyeccion)}</td>
                        </tr>`;
                    }).join('');
                }
            }

            // Pagos
            var renderPagos = function (lista, tbodyId, badgeId, totalId) {
                var tbody = document.getElementById(tbodyId);
                if (!tbody) return;
                var n = lista ? lista.length : 0;
                if (document.getElementById(badgeId)) document.getElementById(badgeId).textContent = n;
                var total = lista ? lista.reduce(function (a, p) { return a + p.monto; }, 0) : 0;
                if (!lista || lista.length === 0) {
                    tbody.innerHTML = self.empty(4);
                } else {
                    tbody.innerHTML = lista.map(function (p) {
                        return `<tr class="data-table__row">
                            <td class="data-table__cell" style="font-weight:600; color:var(--color-primary);">${p.factura}</td>
                            <td class="data-table__cell cell-truncate" style="color:#ffffff;">${p.cliente}</td>
                            <td class="data-table__cell" style="font-weight:600; color:#cbd5e1;">${p.fecha}</td>
                            <td class="data-table__cell text-end" style="font-weight:700; color:#00e676;">${self.fmt(p.monto)}</td>
                        </tr>`;
                    }).join('');
                }
                if (document.getElementById(totalId)) document.getElementById(totalId).textContent = self.fmt(total);
            };
            renderPagos(data.pagos ? data.pagos.lista_pagos_contado : [], 'tabla-pagos-contado-body', 'badge-pagos-contado', 'subtotal-pagos-contado');
            renderPagos(data.pagos ? data.pagos.lista_pagos_credito : [], 'tabla-pagos-credito-body', 'badge-pagos-credito', 'subtotal-pagos-credito');

            // Estancados
            var estanc = (data.inventario_estancado && data.inventario_estancado.lista) ? data.inventario_estancado.lista : [];
            if (document.getElementById('badge-estancados')) {
                document.getElementById('badge-estancados').textContent = estanc.length;
            }
            if (document.getElementById('subtotal-estancados-cant')) {
                document.getElementById('subtotal-estancados-cant').textContent = self.fmtNum(data.inventario_estancado ? data.inventario_estancado.totales.cantidad : 0);
            }
            if (document.getElementById('subtotal-estancados')) {
                document.getElementById('subtotal-estancados').textContent = self.fmt(data.inventario_estancado ? data.inventario_estancado.totales.valor : 0);
            }
            var tbodyEstanc = document.getElementById('tabla-estancados-body');
            if (tbodyEstanc) {
                if (estanc.length === 0) {
                    tbodyEstanc.innerHTML = self.empty(6, 'Inventario sano ✓');
                } else {
                    tbodyEstanc.innerHTML = estanc.map(function (p) {
                        var badgeCls = p.dias > 90 ? 'badge-pill-apex--inactive' : 'badge-pill-apex';
                        return `<tr class="data-table__row">
                            <td class="data-table__cell" style="font-weight:600; color:#ffffff;">${p.nombre}</td>
                            <td class="data-table__cell text-center" style="font-weight:600; color:#cbd5e1;">${p.fecha_compra}</td>
                            <td class="data-table__cell text-center"><span class="badge-pill-apex ${badgeCls}">${p.dias} días</span></td>
                            <td class="data-table__cell text-end" style="font-weight:600; color:#ffffff;">${p.cantidad}</td>
                            <td class="data-table__cell text-end" style="font-weight:700; color:#ffb74d;">${self.fmt(p.precio)}</td>
                            <td class="data-table__cell text-end" style="font-weight:700; color:#ff5252;">${self.fmt(p.cantidad * p.precio)}</td>
                        </tr>`;
                    }).join('');
                }
            }
        },

        cargarDatos: function (mesStr) {
            var self = this;
            fetch(`/reportes/api/datos?mes=${mesStr}`)
                .then(function (res) { return res.json(); })
                .then(function (data) { self.renderizarDatos(data); })
                .catch(function (err) {
                    console.error("Error cargando datos:", err);
                    alert("Ocurrió un error al cargar los datos del reporte.");
                });
        },

        init: function () {
            var self = this;
            var filtroMes = document.getElementById("filtroMes");

            // Exponer funciones globales para botones onclick en el HTML si es necesario
            window.mostrarSeccion = function (id, btn) { self.mostrarSeccion(id, btn); };
            window.filtrarVentas = function (tipo) { self.filtrarVentas(tipo); };

            if (filtroMes) {
                if (filtroMes.value) self.cargarDatos(filtroMes.value);
                filtroMes.addEventListener("change", function () {
                    self.cargarDatos(this.value);
                });
            }
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        window.ERP.Reportes.init();
    });

})(window, document);
