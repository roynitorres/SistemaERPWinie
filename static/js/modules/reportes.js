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
                        <td class="data-table__cell" style=" font-weight:700; color:var(--color-text-main);">${v.factura}</td>
                        <td class="data-table__cell" style="color:var(--color-text-main);">${v.cliente}</td>
                        <td class="data-table__cell" style=" color:var(--color-text-main);">${v.fecha}</td>
                        <td class="data-table__cell text-center"><span class="badge-pill-apex ${badgeCls}">${v.tipo}</span></td>
                        <td class="data-table__cell text-center" style=" color:var(--color-text-main);">${self.fmtNum(v.cantidad || 0)}</td>
                        <td class="data-table__cell text-end" style="font-weight:700; color:var(--color-text-main);">${self.fmt(v.total)}</td>
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

        filtrarPagos: function (tipo) {
            var self = this;
            ['btn-p-todas', 'btn-p-contado', 'btn-p-credito'].forEach(function (id) {
                var b = document.getElementById(id);
                if (b) {
                    b.classList.remove('active');
                    b.classList.add('btn--outline');
                }
            });
            var activo = tipo === 'TODAS' ? 'btn-p-todas' : tipo === 'CONTADO' ? 'btn-p-contado' : 'btn-p-credito';
            var ba = document.getElementById(activo);
            if (ba) { ba.classList.remove('btn--outline'); ba.classList.add('active'); }

            if (!self.datosGlobales.pagos) return;

            var listaContado = (self.datosGlobales.pagos.lista_pagos_contado || []).map(p => ({ ...p, tipo: 'CONTADO' }));
            var listaCredito = (self.datosGlobales.pagos.lista_pagos_credito || []).map(p => ({ ...p, tipo: 'CREDITO' }));
            var listaTodas = listaContado.concat(listaCredito).sort((a, b) => new Date(b.fecha) - new Date(a.fecha));

            var lista = tipo === 'TODAS' ? listaTodas
                : tipo === 'CONTADO' ? listaContado
                    : listaCredito;

            var tbody = document.getElementById('tabla-pagos-body');
            var total = 0;
            if (!tbody) return;

            if (!lista || lista.length === 0) {
                tbody.innerHTML = self.empty(5);
            } else {
                tbody.innerHTML = lista.map(function (p) {
                    total += p.monto;
                    var badgeCls = p.tipo === 'CONTADO' ? 'badge-pill-apex--active' : 'badge-pill-apex';
                    return `<tr class="data-table__row">
                        <td class="data-table__cell" style="font-weight:700; color:var(--color-text-main);">${p.factura}</td>
                        <td class="data-table__cell" style="color:var(--color-text-main);">${p.cliente}</td>
                        <td class="data-table__cell" style=" color:var(--color-text-main);">${p.fecha}</td>
                        <td class="data-table__cell text-center"><span class="badge-pill-apex ${badgeCls}">${p.tipo}</span></td>
                        <td class="data-table__cell text-end" style="font-weight:700; color:var(--color-text-main);">${self.fmt(p.monto)}</td>
                    </tr>`;
                }).join('');
            }
            if (document.getElementById('subtotal-pagos-unificado')) {
                document.getElementById('subtotal-pagos-unificado').textContent = self.fmt(total);
            }
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

            // Clientes unificados
            var mejores = data.mejores_clientes || [];
            var nuevos = data.lista_clientes_nuevos || [];
            
            // Unir ambas listas
            var mapaClientes = {};
            mejores.forEach(function(c) {
                mapaClientes[c.nombre] = {
                    nombre: c.nombre,
                    telefono: c.telefono,
                    cantidad_compras: c.cantidad_compras,
                    total: c.total,
                    esNuevo: false
                };
            });
            nuevos.forEach(function(c) {
                if (mapaClientes[c.nombre]) {
                    mapaClientes[c.nombre].esNuevo = true;
                } else {
                    mapaClientes[c.nombre] = {
                        nombre: c.nombre,
                        telefono: c.telefono,
                        cantidad_compras: 0,
                        total: 0,
                        esNuevo: true
                    };
                }
            });
            
            var clientesUnificados = Object.values(mapaClientes);
            clientesUnificados.sort(function(a, b) {
                return b.total - a.total;
            });
            
            if (document.getElementById('badge-clientes-unificado')) {
                document.getElementById('badge-clientes-unificado').textContent = clientesUnificados.length;
            }
            if (document.getElementById('subtotal-clientes-compras')) {
                document.getElementById('subtotal-clientes-compras').textContent = self.fmtNum(clientesUnificados.reduce((acc, c) => acc + (c.cantidad_compras || 0), 0));
            }
            if (document.getElementById('subtotal-clientes-unificado')) {
                document.getElementById('subtotal-clientes-unificado').textContent = self.fmt(clientesUnificados.reduce((acc, c) => acc + c.total, 0));
            }
            
            var tbodyClientes = document.getElementById('tabla-clientes-unificado-body');
            if (tbodyClientes) {
                if (clientesUnificados.length === 0) {
                    tbodyClientes.innerHTML = self.empty(6, 'Sin datos de clientes este mes');
                } else {
                    tbodyClientes.innerHTML = clientesUnificados.map(function (c, i) {
                        var trClass = i === 0 && c.total > 0 ? 'data-table__row top-buyer' : 'data-table__row';
                        var tag = i === 0 && c.total > 0 ? `<span class="top-buyer-tag"><i class="bi bi-trophy-fill me-1"></i> Top Comprador</span>` : '';
                        var badgeNuevo = c.esNuevo ? `<div style="margin-top:4px;"><span class="badge-pill-apex badge-pill-apex--active" style="background:var(--color-success); color:#fff; padding:2px 6px; font-size:0.65rem; font-weight: 800; letter-spacing: 0.5px;">NUEVO CLIENTE</span></div>` : '';
                        
                        return `<tr class="${trClass}">
                            <td class="data-table__cell" style="font-weight:700; color:var(--color-text-main);">${i + 1}</td>
                            <td class="data-table__cell" style=" color:var(--color-text-main);">
                                ${c.nombre}${tag}
                                ${badgeNuevo}
                            </td>
                            <td class="data-table__cell" style="color:var(--color-text-main);">${c.telefono}</td>
                            <td class="data-table__cell text-center" style=" color:var(--color-text-main);">${c.cantidad_compras}</td>
                            <td class="data-table__cell text-end" style=" font-weight:700; color:var(--color-text-main);">${self.fmt(c.total)}</td>
                        </tr>`;
                    }).join('');
                }
            }

            // Productos comprados del mes
            var comprasList = (data.compras && data.compras.lista) ? data.compras.lista : [];
            if (document.getElementById('badge-cant-items-compras')) {
                document.getElementById('badge-cant-items-compras').textContent = `${comprasList.length} item${comprasList.length !== 1 ? 's' : ''}`;
            }
            var totalPrecioCompra = comprasList.reduce((acc, p) => acc + (parseFloat(p.precio_compra) || 0), 0);
            var totalPrecioVenta = comprasList.reduce((acc, p) => acc + (parseFloat(p.precio_venta) || 0), 0);

            if (document.getElementById('subtotal-unidades-compradas')) {
                document.getElementById('subtotal-unidades-compradas').textContent = self.fmtNum(data.compras ? data.compras.unidades_compradas : 0);
            }
            if (document.getElementById('subtotal-precio-compra')) {
                document.getElementById('subtotal-precio-compra').textContent = self.fmt(totalPrecioCompra);
            }
            if (document.getElementById('subtotal-precio-venta')) {
                document.getElementById('subtotal-precio-venta').textContent = self.fmt(totalPrecioVenta);
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
                            <td class="data-table__cell" style="font-weight:700; color:var(--color-text-main);">${i + 1}</td>
                            <td class="data-table__cell" style="font-weight:600; color:var(--color-text-main);">
                                ${p.nombre}
                                <div style="font-size:0.75rem; color:var(--color-text-muted);">${p.codigo}</div>
                            </td>
                            <td class="data-table__cell " style="color:var(--color-text-main);"><i class="bi bi-truck me-1"></i>${p.proveedor || '-'}</td>
                            <td class="data-table__cell text-center" style="font-weight:700; color:var(--color-text-main);">${self.fmtNum(p.cantidad)}</td>
                            <td class="data-table__cell text-end" style=" color:var(--color-text-main);">${self.fmt(p.precio_compra)}</td>
                            <td class="data-table__cell text-end" style=" color:var(--color-text-main);">${self.fmt(p.precio_venta)}</td>
                            <td class="data-table__cell text-end" style=" color:var(--color-text-main);">${self.fmt(p.inversion)}</td>
                            <td class="data-table__cell text-end" style=" color:var(--color-text-main);">${self.fmt(p.proyeccion)}
                        </tr>`;
                    }).join('');
                }
            }

            // Pagos unificados
            self.filtrarPagos('TODAS');

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
            window.filtrarPagos = function (tipo) { self.filtrarPagos(tipo); };

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
