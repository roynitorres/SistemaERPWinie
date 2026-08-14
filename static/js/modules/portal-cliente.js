/* ==========================================================================
   SISTEMA ERP WINIE — MÓDULO PORTAL DEL CLIENTE (static/js/modules/portal-cliente.js)
   Lógica de filtrado, modales de desgloses y cambio de contraseña
   ========================================================================== */

(function (window, document) {
    'use strict';

    window.ERP = window.ERP || {};

    window.ERP.PortalCliente = {
        filtroActual: 'TODOS',

        /**
         * Inicializa la búsqueda en tiempo real e interacciones con las pills de estado
         */
        initFiltrosTabla: function () {
            var self = this;
            var inputBuscar = document.getElementById('buscarVenta');
            var pills = document.querySelectorAll('.state-pill');

            pills.forEach(function (pill) {
                pill.addEventListener('click', function () {
                    pills.forEach(function (p) {
                        p.classList.remove('state-pill--active');
                    });
                    this.classList.add('state-pill--active');

                    self.filtroActual = this.dataset.filtro || 'TODOS';
                    self.aplicarFiltros();
                });
            });

            if (inputBuscar) {
                inputBuscar.addEventListener('input', function () {
                    self.aplicarFiltros();
                });
            }
        },

        /**
         * Aplica los filtros de búsqueda por texto y por pill activo a las filas de la tabla
         */
        aplicarFiltros: function () {
            var inputBuscar = document.getElementById('buscarVenta');
            var query = inputBuscar ? inputBuscar.value.toLowerCase().trim() : '';
            var filas = document.querySelectorAll('#tablaVentasPortal tr.fila-venta');
            var visibles = 0;

            filas.forEach(function (row) {
                var numFactura = (row.dataset.factura || '').toLowerCase();
                var tipoVenta = (row.dataset.tipo || '').toUpperCase();
                var esPagada = row.dataset.pagada === '1';

                var cumpleBusqueda = !query || numFactura.includes(query);
                var cumpleFiltro = true;

                if (this.filtroActual === 'CONTADO') {
                    cumpleFiltro = (tipoVenta === 'CONTADO');
                } else if (this.filtroActual === 'CREDITO') {
                    cumpleFiltro = (tipoVenta === 'CREDITO');
                } else if (this.filtroActual === 'PENDIENTE') {
                    cumpleFiltro = !esPagada;
                }

                if (cumpleBusqueda && cumpleFiltro) {
                    row.style.display = '';
                    visibles++;
                } else {
                    row.style.display = 'none';
                }
            }, this);

            var badgeTotal = document.getElementById('badgeTotalVentas');
            if (badgeTotal) {
                badgeTotal.textContent = visibles;
            }
        },

        /**
         * Modales de detalles de Pago Contado y Plan de Cuotas Crédito
         */
        initModalesDetalle: function () {
            document.querySelectorAll('.btn-ver-pago-contado-trigger').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    var ventaId = this.dataset.ventaId;
                    var scriptTag = document.getElementById('venta-json-' + ventaId);
                    if (!scriptTag) return;
                    var data = JSON.parse(scriptTag.textContent);

                    var fEl = document.getElementById('detContadoFactura');
                    var cEl = document.getElementById('detContadoCliente');
                    var tEl = document.getElementById('detContadoTotal');

                    if (fEl) fEl.textContent = data.factura;
                    if (cEl) cEl.textContent = data.cliente;
                    if (tEl) tEl.textContent = data.total;

                    var p = (data.pagos && data.pagos.length > 0) ? data.pagos[0] : null;
                    var feEl = document.getElementById('detContadoFecha');
                    var mEl = document.getElementById('detContadoMetodo');
                    var bEl = document.getElementById('detContadoBanco');
                    var rEl = document.getElementById('detContadoReferencia');
                    var oEl = document.getElementById('detContadoObs');

                    if (feEl) feEl.textContent = p ? p.fecha : data.fecha_venta;
                    if (mEl) mEl.textContent = p ? p.metodo : 'EFECTIVO';
                    if (bEl) bEl.textContent = p ? p.banco : '-';
                    if (rEl) rEl.textContent = p ? p.referencia : '-';
                    if (oEl) oEl.textContent = p ? p.observaciones : '-';

                    var modalEl = document.getElementById('modalDetallePagoContado');
                    if (modalEl && window.bootstrap) {
                        var modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                        modal.show();
                    }
                });
            });

            document.querySelectorAll('.btn-ver-plan-credito-trigger').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    var ventaId = this.dataset.ventaId;
                    var scriptTag = document.getElementById('venta-json-' + ventaId);
                    if (!scriptTag) return;
                    var data = JSON.parse(scriptTag.textContent);

                    var tEl = document.getElementById('creditoTitleFactura');
                    var pBtn = document.getElementById('btnImprimirPlanPdf');
                    var mTEl = document.getElementById('creditoMontoTotal');
                    var mAEl = document.getElementById('creditoMontoAbonado');
                    var sPEl = document.getElementById('creditoSaldoPendiente');

                    if (tEl) tEl.textContent = data.factura;
                    if (pBtn) pBtn.href = data.imprimir_url;
                    if (mTEl) mTEl.textContent = data.total;
                    if (mAEl) mAEl.textContent = data.abonado;
                    if (sPEl) sPEl.textContent = data.saldo;

                    var tbody = document.getElementById('tablaCuotasCreditoBody');
                    if (tbody) {
                        tbody.innerHTML = '';
                        if (!data.cuotas || data.cuotas.length === 0) {
                            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-3 text-muted">No hay cuotas registradas para este crédito.</td></tr>';
                        } else {
                            data.cuotas.forEach(function (c) {
                                var badgeEstado = '';
                                if (c.estado === 'PAGADA') {
                                    badgeEstado = '<span class="badge-pill-apex badge-pill-apex--active">PAGADA</span>';
                                } else if (c.estado === 'VENCIDA') {
                                    badgeEstado = '<span class="badge-pill-apex badge-pill-apex--inactive" style="background: rgba(255,82,82,0.15); color: #ff5252;">VENCIDA</span>';
                                } else if (c.estado === 'EN GRACIA') {
                                    badgeEstado = '<span class="badge-pill-apex" style="background: rgba(255,183,77,0.15); color: #ffb74d; border: 1px solid rgba(255,183,77,0.3);">EN GRACIA</span>';
                                } else {
                                    badgeEstado = '<span class="badge-pill-apex" style="background: rgba(0,176,255,0.12); color: #00b0ff; border: 1px solid rgba(0,176,255,0.2);">PENDIENTE</span>';
                                }

                                var row = document.createElement('tr');
                                row.className = 'data-table__row';
                                row.innerHTML = `
                                    <td class="data-table__cell text-center" style="font-weight: 800; color: var(--color-primary);">Cuota ${c.numero}</td>
                                    <td class="data-table__cell">
                                        <span style="color: #ffffff; font-weight: 600;">${c.vencimiento}</span>
                                    </td>
                                    <td class="data-table__cell text-end" style="font-weight: 700; color: #ffffff;">${c.monto}</td>
                                    <td class="data-table__cell text-center">${badgeEstado}</td>
                                    <td class="data-table__cell text-center text-muted" style="font-size: 0.88rem;">${c.metodo_pago}</td>
                                    <td class="data-table__cell text-center text-muted" style="font-size: 0.88rem;">${c.referencia}</td>
                                    <td class="data-table__cell text-center text-muted" style="font-size: 0.88rem;">${c.banco}</td>
                                `;
                                tbody.appendChild(row);
                            });
                        }
                    }

                    var modalEl = document.getElementById('modalDetallePlanCredito');
                    if (modalEl && window.bootstrap) {
                        var modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                        modal.show();
                    }
                });
            });
        },

        /**
         * Manejo del formulario de cambio de contraseña obligatoria
         */
        initFormCambioPassword: function () {
            var form = document.getElementById('formCambiarPasswordPortal');
            if (!form) return;

            form.addEventListener('submit', function (e) {
                var pAct = document.getElementById('inputPassActual');
                var pNue = document.getElementById('inputPassNueva');
                var pCon = document.getElementById('inputPassConfirm');

                var errAct = document.getElementById('err-pass-actual');
                var errNue = document.getElementById('err-pass-nueva');
                var errCon = document.getElementById('err-pass-confirm');

                var valido = window.ERP.Validators.validatePasswordForm(pAct, pNue, pCon, errAct, errNue, errCon);

                if (!valido) {
                    e.preventDefault();
                    return false;
                }
                return true;
            });
        },

        init: function () {
            this.initFiltrosTabla();
            this.initModalesDetalle();
            this.initFormCambioPassword();
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        window.ERP.PortalCliente.init();
    });

})(window, document);
