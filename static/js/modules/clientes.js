/* ==========================================================================
   SISTEMA ERP WINIE — MÓDULO DE CLIENTES (static/js/modules/clientes.js)
   Gestión de clientes, credenciales, paginación live e historial de compras
   ========================================================================== */

(function (window, document) {
    'use strict';

    window.ERP = window.ERP || {};

    window.ERP.Clientes = {
        textoCopiarCredenciales: '',
        filtroActual: 'TODOS',
        estadoFiltroActual: 'TODOS',
        currentPage: 1,
        itemsPerPage: 10,
        allRows: [],
        filteredRows: [],

        /**
         * Inicializa la paginación y búsqueda en tiempo real de la tabla de clientes
         */
        initPaginacionClientes: function () {
            var self = this;
            var tabla = document.getElementById('tablaClientes');
            if (!tabla) return;

            this.allRows = Array.from(tabla.querySelectorAll('tr'));
            this.filteredRows = Array.from(this.allRows);

            var inputBuscar = document.getElementById('buscarCliente');
            if (inputBuscar) {
                inputBuscar.addEventListener('input', function () {
                    self.aplicarFiltrosClientes();
                });
            }

            document.querySelectorAll('.state-pill[data-estado]').forEach(function (pill) {
                pill.addEventListener('click', function () {
                    document.querySelectorAll('.state-pill[data-estado]').forEach(function (p) {
                        p.classList.remove('state-pill--active');
                    });
                    this.classList.add('state-pill--active');
                    self.estadoFiltroActual = this.dataset.estado || 'TODOS';
                    self.aplicarFiltrosClientes();
                });
            });

            this.renderTable();
        },

        /**
         * Aplica los filtros a la lista de clientes (texto + estado)
         */
        aplicarFiltrosClientes: function () {
            var inputBuscar = document.getElementById('buscarCliente');
            var query = inputBuscar ? inputBuscar.value.toLowerCase().trim() : '';

            this.filteredRows = this.allRows.filter(function (row) {
                var codigo = (row.dataset.codigo || '').toLowerCase();
                var nombres = (row.dataset.nombres || '').toLowerCase();
                var telefono = (row.dataset.telefono || '').toLowerCase();
                var ciudad = (row.dataset.ciudad || '').toLowerCase();
                var estadoRow = row.dataset.estado || '';

                var cumpleTexto = !query ||
                    codigo.includes(query) ||
                    nombres.includes(query) ||
                    telefono.includes(query) ||
                    ciudad.includes(query);

                var cumpleEstado = this.estadoFiltroActual === 'TODOS' || estadoRow === this.estadoFiltroActual;

                return cumpleTexto && cumpleEstado;
            }, this);

            this.currentPage = 1;
            this.renderTable();
        },

        /**
         * Renderiza la tabla y controles de paginación
         */
        renderTable: function () {
            var totalItems = this.filteredRows.length;
            var totalPages = Math.ceil(totalItems / this.itemsPerPage) || 1;

            if (this.currentPage > totalPages) this.currentPage = totalPages;
            if (this.currentPage < 1) this.currentPage = 1;

            var startIndex = (this.currentPage - 1) * this.itemsPerPage;
            var endIndex = Math.min(startIndex + this.itemsPerPage, totalItems);

            this.allRows.forEach(function (row) {
                row.style.display = 'none';
            });

            for (var i = startIndex; i < endIndex; i++) {
                if (this.filteredRows[i]) this.filteredRows[i].style.display = '';
            }

            var summaryText = totalItems > 0
                ? 'Mostrando ' + (startIndex + 1) + ' a ' + endIndex + ' de ' + totalItems + ' registros'
                : 'Mostrando 0 a 0 de 0 registros';

            var summaryEl = document.getElementById('paginationSummary');
            if (summaryEl) summaryEl.innerText = summaryText;

            var badgeTotal = document.getElementById('badgeTotalItems');
            if (badgeTotal) badgeTotal.textContent = totalItems;

            this.renderControls(totalPages);
        },

        /**
         * Genera los botones de paginación numerados
         */
        renderControls: function (totalPages) {
            var self = this;
            var container = document.getElementById('paginationControls');
            if (!container) return;
            container.innerHTML = '';

            if (totalPages <= 1) return;

            var btnPrev = document.createElement('button');
            btnPrev.className = 'btn-apex-outline btn--small';
            btnPrev.innerHTML = '<i class="bi bi-chevron-left"></i>';
            if (this.currentPage === 1) {
                btnPrev.disabled = true;
            } else {
                btnPrev.addEventListener('click', function () {
                    self.currentPage--;
                    self.renderTable();
                });
            }
            container.appendChild(btnPrev);

            for (var i = 1; i <= totalPages; i++) {
                (function (pageIndex) {
                    var btnPage = document.createElement('button');
                    btnPage.className = 'btn--small ' + (self.currentPage === pageIndex ? 'btn-neon-primary' : 'btn-apex-outline');
                    btnPage.innerText = pageIndex;
                    btnPage.addEventListener('click', function () {
                        self.currentPage = pageIndex;
                        self.renderTable();
                    });
                    container.appendChild(btnPage);
                })(i);
            }

            var btnNext = document.createElement('button');
            btnNext.className = 'btn-apex-outline btn--small';
            btnNext.innerHTML = '<i class="bi bi-chevron-right"></i>';
            if (this.currentPage === totalPages) {
                btnNext.disabled = true;
            } else {
                btnNext.addEventListener('click', function () {
                    self.currentPage++;
                    self.renderTable();
                });
            }
            container.appendChild(btnNext);
        },

        /**
         * Formulario de alta y edición de cliente con mensajes de retroalimentación
         */
        initFormCliente: function () {
            var self = this;
            var form = document.getElementById('formClientes');
            if (!form) return;

            var formTitle = document.getElementById('formTitle');
            var formCodigo = document.getElementById('form_codigo');
            var formNombre = document.getElementById('form_nombre');
            var formTelefono = document.getElementById('form_telefono');
            var formCiudad = document.getElementById('form_ciudad');
            var formEstado = document.getElementById('form_estado');
            var clienteIdInput = document.getElementById('cliente_id');

            var btnLimpiar = document.getElementById('btnLimpiar');
            var btnIrForm = document.getElementById('btnIrForm');

            form.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' && e.target.tagName !== 'BUTTON') {
                    e.preventDefault();
                }
            });

            var resetForm = function () {
                form.querySelectorAll('.is-invalid-apex').forEach(function (el) {
                    window.ERP.Validators.clearError(el);
                });
                form.reset();
                if (clienteIdInput) clienteIdInput.value = '';
                if (formEstado) {
                    formEstado.value = 'ACTIVO';
                    window.ERP.UI.updateSelectEstado(formEstado);
                }
                if (formTitle) formTitle.innerHTML = '<i class="bi bi-person-plus-fill text-success me-1"></i> NUEVO CLIENTE';
                if (formNombre) formNombre.focus();
            };

            if (btnLimpiar) btnLimpiar.addEventListener('click', resetForm);
            if (btnIrForm) {
                btnIrForm.addEventListener('click', function () {
                    resetForm();
                    window.ERP.UI.openModal('modalFormCliente');
                });
            }

            var cargarCliente = function (row) {
                resetForm();
                if (clienteIdInput) clienteIdInput.value = row.dataset.id || '';
                if (formCodigo) formCodigo.value = row.dataset.codigo || '';
                if (formNombre) formNombre.value = row.dataset.nombres || '';
                if (formTelefono) formTelefono.value = row.dataset.telefono || '';
                if (formEstado) {
                    formEstado.value = row.dataset.estado || 'ACTIVO';
                    window.ERP.UI.updateSelectEstado(formEstado);
                }

                var ciudadData = (row.dataset.ciudad || '').trim().toUpperCase();
                if (formCiudad) {
                    var encontrada = false;
                    for (var i = 0; i < formCiudad.options.length; i++) {
                        if (formCiudad.options[i].value.toUpperCase() === ciudadData ||
                            formCiudad.options[i].text.toUpperCase() === ciudadData) {
                            formCiudad.selectedIndex = i;
                            encontrada = true;
                            break;
                        }
                    }
                    if (!encontrada) formCiudad.value = '';
                }

                if (formTitle) formTitle.innerHTML = '<i class="bi bi-pencil-fill text-primary me-1"></i> EDITAR CLIENTE';
                window.ERP.UI.openModal('modalFormCliente');
            };

            document.querySelectorAll('.btn-editar-fila').forEach(function (btn) {
                btn.addEventListener('click', function (e) {
                    e.stopPropagation();
                    var row = this.closest('tr');
                    if (row) cargarCliente(row);
                });
            });

            document.querySelectorAll('#tablaClientes tr').forEach(function (row) {
                row.addEventListener('dblclick', function () {
                    cargarCliente(this);
                });
            });

            form.addEventListener('submit', function (e) {
                form.querySelectorAll('.is-invalid-apex').forEach(function (el) {
                    window.ERP.Validators.clearError(el);
                });

                var esValido = true;
                var primerInvalido = null;

                // 1. Validar Nombre del Cliente
                var valNombre = formNombre ? formNombre.value.trim() : '';
                if (!valNombre) {
                    window.ERP.Validators.setError(formNombre, null, 'El nombre del cliente es obligatorio.');
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formNombre;
                } else if (valNombre.length < 3) {
                    window.ERP.Validators.setError(formNombre, null, 'El nombre debe tener al menos 3 caracteres.');
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formNombre;
                }

                // 2. Validar Teléfono (8 dígitos comenzando con 5, 7 u 8)
                var valTel = formTelefono ? formTelefono.value.trim() : '';
                var regexTel = /^[578][0-9]{7}$/;
                if (!valTel) {
                    window.ERP.Validators.setError(formTelefono, null, 'El número de teléfono es obligatorio.');
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formTelefono;
                } else if (!regexTel.test(valTel)) {
                    window.ERP.Validators.setError(formTelefono, null, 'El teléfono debe tener 8 dígitos y comenzar con 5, 7 u 8.');
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formTelefono;
                }

                // 3. Validar Ciudad
                if (formCiudad && !formCiudad.value) {
                    window.ERP.Validators.setError(formCiudad, null, 'Por favor seleccione una ciudad de la lista.');
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formCiudad;
                }

                if (!esValido) {
                    e.preventDefault();
                    if (primerInvalido) primerInvalido.focus();
                    return false;
                }
            });
        },

        /**
         * Filtros dinámicos en la página de Historial del Cliente (Todos, Contado, Crédito, Pendientes)
         */
        initFiltrosHistorial: function () {
            var self = this;
            var tablaHistorial = document.getElementById('tablaHistorial');
            if (!tablaHistorial) return;

            var allHistorialRows = Array.from(tablaHistorial.querySelectorAll('tr.fila-historial'));
            var inputBuscar = document.getElementById('buscarFactura');

            var aplicarFiltros = function () {
                var query = inputBuscar ? inputBuscar.value.toLowerCase().trim() : '';
                var visibles = 0;

                allHistorialRows.forEach(function (row) {
                    var numFactura = (row.dataset.factura || '').toLowerCase();
                    var tipoVenta = (row.dataset.tipo || '').toUpperCase();
                    var esPagada = row.dataset.pagada === '1';

                    var coincideTexto = !query || numFactura.includes(query);
                    var coincideFiltro = true;

                    if (self.filtroActual === 'CONTADO') {
                        coincideFiltro = (tipoVenta === 'CONTADO');
                    } else if (self.filtroActual === 'CREDITO') {
                        coincideFiltro = (tipoVenta === 'CREDITO');
                    } else if (self.filtroActual === 'PENDIENTE') {
                        coincideFiltro = !esPagada;
                    }

                    if (coincideTexto && coincideFiltro) {
                        row.style.display = '';
                        visibles++;
                    } else {
                        row.style.display = 'none';
                    }
                });

                var badgeTotal = document.getElementById('badgeTotalVentas');
                if (badgeTotal) {
                    badgeTotal.textContent = visibles;
                }
            };

            document.querySelectorAll('.state-pill[data-filtro]').forEach(function (pill) {
                pill.addEventListener('click', function () {
                    document.querySelectorAll('.state-pill[data-filtro]').forEach(function (p) {
                        p.classList.remove('state-pill--active');
                    });
                    this.classList.add('state-pill--active');
                    self.filtroActual = this.dataset.filtro || 'TODOS';
                    aplicarFiltros();
                });
            });

            if (inputBuscar) {
                inputBuscar.addEventListener('input', aplicarFiltros);
            }
        },

        /**
         * Modales de detalles de Pago Contado y Plan de Crédito en el Historial del Cliente
         */
        initModalesDetalleHistorial: function () {
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

                    window.ERP.UI.openModal('modalDetallePagoContado');
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
                                    <td class="data-table__cell text-center " style="font-size: 0.88rem;">${c.metodo_pago}</td>
                                    <td class="data-table__cell text-center " style="font-size: 0.88rem;">${c.referencia}</td>
                                    <td class="data-table__cell text-center " style="font-size: 0.88rem;">${c.banco}</td>
                                `;
                                tbody.appendChild(row);
                            });
                        }
                    }

                    window.ERP.UI.openModal('modalDetallePlanCredito');
                });
            });
        },

        /**
         * Restablecimiento de contraseña
         */
        initRestaurarPassword: function () {
            var formToSubmit = null;
            document.querySelectorAll('.btn-restaurar-trigger').forEach(function (btn) {
                btn.addEventListener('click', function (e) {
                    var debeCambiar = this.dataset.debeCambiar === '1';
                    if (debeCambiar) {
                        e.preventDefault();
                        e.stopPropagation();
                        alert('El cliente aún no ha utilizado su contraseña temporal activa. Puedes consultar y entregarle las credenciales vigentes en la opción "Ver credenciales".');
                        return false;
                    }
                    e.stopPropagation();
                    formToSubmit = this.closest('form');
                    window.ERP.UI.openModal('modalRestaurarPassword');
                });
            });

            var btnConfirmar = document.getElementById('btnConfirmarRestaurar');
            if (btnConfirmar) {
                btnConfirmar.addEventListener('click', function () {
                    if (formToSubmit) formToSubmit.submit();
                });
            }
        },

        /**
         * Manejador del Modal Ver Cliente
         */
        initModalVerCliente: function () {
            document.querySelectorAll('.btn-ver-cliente-trigger').forEach(function (btn) {
                btn.addEventListener('click', function (e) {
                    e.stopPropagation();
                    var codigo = this.dataset.codigo || '';
                    var nombres = this.dataset.nombres || '';
                    var telefono = this.dataset.telefono || '';
                    var ciudad = this.dataset.ciudad || '';
                    var estado = this.dataset.estado || '';
                    var usuario = this.dataset.usuario || '';
                    var historialUrl = this.dataset.historialUrl || '#';

                    var nEl = document.getElementById('verClienteNombre');
                    var cEl = document.getElementById('verClienteCodigo');
                    var tEl = document.getElementById('verClienteTelefono');
                    var ciEl = document.getElementById('verClienteCiudad');
                    var uEl = document.getElementById('verClienteUsuario');
                    var hEl = document.getElementById('verClienteHistorialLink');
                    var badge = document.getElementById('verClienteEstadoBadge');

                    if (nEl) nEl.textContent = nombres;
                    if (cEl) cEl.textContent = 'Código: ' + codigo;
                    if (tEl) tEl.textContent = telefono;
                    if (ciEl) ciEl.textContent = ciudad;
                    if (uEl) uEl.textContent = usuario;
                    if (hEl) hEl.href = historialUrl;

                    if (badge) {
                        if (estado === 'ACTIVO') {
                            badge.className = 'badge-pill-apex badge-pill-apex--active';
                            badge.textContent = 'ACTIVO';
                        } else {
                            badge.className = 'badge-pill-apex badge-pill-apex--inactive';
                            badge.textContent = 'INACTIVO';
                        }
                    }

                    window.ERP.UI.openModal('modalVerCliente');
                });
            });
        },

        /**
         * Manejador del Modal Ver Credenciales del Portal
         */
        initModalVerCredenciales: function () {
            var self = this;
            document.querySelectorAll('.btn-ver-credenciales-trigger').forEach(function (btn) {
                btn.addEventListener('click', function (e) {
                    e.stopPropagation();
                    var codigo = this.dataset.codigo || '';
                    var nombres = this.dataset.nombres || '';
                    var usuario = this.dataset.usuario || '';
                    var passTemp = this.dataset.passTemp || '';
                    var debeCambiar = this.dataset.debeCambiar === '1';

                    var cEl = document.getElementById('credCodigo');
                    var nEl = document.getElementById('credNombre');
                    var uEl = document.getElementById('credUsuario');

                    if (cEl) cEl.textContent = codigo;
                    if (nEl) nEl.textContent = nombres;
                    if (uEl) uEl.textContent = usuario;

                    var badgeEstado = document.getElementById('credEstadoBadge');
                    var cajaTemp = document.getElementById('cajaPassTemp');
                    var cajaPers = document.getElementById('cajaPassPersonal');
                    var passTempEl = document.getElementById('credPassTemp');

                    if (debeCambiar) {
                        if (badgeEstado) {
                            badgeEstado.textContent = 'TEMPORAL ACTIVA';
                            badgeEstado.className = 'badge-pill-apex badge-pill-apex--active';
                        }
                        if (cajaTemp) cajaTemp.style.display = 'block';
                        if (cajaPers) cajaPers.style.display = 'none';
                        if (passTempEl) passTempEl.textContent = passTemp || 'No disponible';
                        self.textoCopiarCredenciales = 'Portal de Acceso - Cliente: ' + nombres + ' (' + codigo + ')\nUsuario: ' + usuario + '\nContraseña Temporal: ' + passTemp;
                    } else {
                        if (badgeEstado) {
                            badgeEstado.textContent = 'CLAVE PERSONAL';
                            badgeEstado.className = 'badge-pill-apex badge-pill-apex--active';
                        }
                        if (cajaTemp) cajaTemp.style.display = 'none';
                        if (cajaPers) cajaPers.style.display = 'block';
                        self.textoCopiarCredenciales = 'Portal de Acceso - Cliente: ' + nombres + ' (' + codigo + ')\nUsuario: ' + usuario;
                    }

                    window.ERP.UI.openModal('modalVerCredenciales');
                });
            });

            var btnCopiar = document.getElementById('btnCopiarCredenciales');
            if (btnCopiar) {
                btnCopiar.addEventListener('click', function () {
                    if (navigator.clipboard) {
                        navigator.clipboard.writeText(self.textoCopiarCredenciales).then(function () {
                            var orig = btnCopiar.innerHTML;
                            btnCopiar.innerHTML = '<i class="bi bi-check2-all me-1"></i> ¡Copiado!';
                            setTimeout(function () { btnCopiar.innerHTML = orig; }, 2000);
                        });
                    }
                });
            }
        },

        init: function () {
            this.initPaginacionClientes();
            this.initFormCliente();
            this.initFiltrosHistorial();
            this.initModalesDetalleHistorial();
            this.initRestaurarPassword();
            this.initModalVerCliente();
            this.initModalVerCredenciales();
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        window.ERP.Clientes.init();
    });

})(window, document);
