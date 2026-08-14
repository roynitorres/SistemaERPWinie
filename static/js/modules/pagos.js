/* ==========================================================================
   SISTEMA ERP WINIE — MÓDULO DE PAGOS Y COBROS (static/js/modules/pagos.js)
   Gestión de pagos de contado, abonos a crédito, bancos y anulación de pagos
   ========================================================================== */

(function (window, document) {
    'use strict';

    window.ERP = window.ERP || {};

    window.ERP.Pagos = {
        pagoIdToCancel: null,

        /**
         * Muestra notificaciones Toast flotantes
         */
        showToast: function (mensaje, tipo) {
            tipo = tipo || 'success';
            var toastContainer = document.getElementById("toastContainer");
            if (!toastContainer) {
                alert(mensaje);
                return;
            }

            var div = document.createElement("div");
            div.className = "alert-toast alert-toast--" + tipo;
            div.style.marginBottom = '10px';
            div.innerHTML = `
                <i class="bi ${tipo === 'success' ? 'bi-check-circle-fill' : (tipo === 'warning' ? 'bi-exclamation-triangle-fill' : 'bi-x-circle-fill')} alert-icon" style="font-size: 1.4rem; flex-shrink: 0;"></i>
                <div class="alert-content">
                    <p class="alert-title">${tipo === 'success' ? 'Éxito' : (tipo === 'warning' ? 'Advertencia' : 'Error')}</p>
                    <p class="alert-message">${mensaje}</p>
                </div>
            `;
            toastContainer.appendChild(div);

            setTimeout(function () {
                div.classList.add('is-closing');
                setTimeout(function () { div.remove(); }, 300);
            }, 3500);
        },

        /**
         * Carga la lista de bancos dinámicamente vía AJAX
         */
        cargarBancos: async function (selectElement, bancoSeleccionarId) {
            if (!selectElement) return;
            try {
                var resp = await fetch("/bancos/lista");
                var data = await resp.json();
                if (data.success && data.bancos) {
                    selectElement.innerHTML = '<option value="">-- Seleccionar Banco --</option>';
                    data.bancos.forEach(function (b) {
                        var opt = document.createElement("option");
                        opt.value = b.id;
                        opt.textContent = b.nombre;
                        if (bancoSeleccionarId && b.id == bancoSeleccionarId) {
                            opt.selected = true;
                        }
                        selectElement.appendChild(opt);
                    });
                }
            } catch (e) {
                console.error("Error cargando lista de bancos:", e);
            }
        },

        /**
         * Paginación y Filtrado por Meses de Facturas de Contado (`pagos_contado.html`)
         */
        initPaginationContado: function () {
            var filtroMesCxc = document.getElementById("filtro_mes_cxc");
            var buscarClienteCxc = document.getElementById("buscarClienteCxc");
            var tablaPagos = document.getElementById("tablaPagos");
            if (!tablaPagos) return;

            var currentPage = 1;
            var itemsPerPage = 10;
            var allRows = Array.from(tablaPagos.querySelectorAll(".fila-factura"));
            var filteredRows = Array.from(allRows);

            var updateBadge = function () {
                var totalMonto = 0;
                filteredRows.forEach(function (row) {
                    var cell3 = row.children[3];
                    if (cell3) {
                        var totalText = cell3.innerText.replace("C$", "").replace(/,/g, "").trim();
                        var monto = parseFloat(totalText) || 0;
                        totalMonto += monto;
                    }
                });

                var badgeTotalFacturas = document.getElementById("badgeTotalFacturas");
                if (badgeTotalFacturas) {
                    badgeTotalFacturas.innerHTML = filteredRows.length;
                }

                var paginationSummary = document.getElementById("paginationSummary");
                if (paginationSummary) {
                    var currentText = paginationSummary.innerText.split(' | ')[0];
                    paginationSummary.innerHTML = currentText + ` | <strong style="margin-left: 10px; color: var(--color-primary-dark);">Total página: C$ ${totalMonto.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>`;
                }
            };

            var renderControls = function (totalPages) {
                var controlsContainer = document.getElementById("paginationControls");
                if (!controlsContainer) return;
                controlsContainer.innerHTML = "";
                if (totalPages <= 1) return;

                var btnPrev = document.createElement("button");
                btnPrev.className = "btn btn--outline btn--small";
                btnPrev.innerHTML = `<i class="bi bi-chevron-left"></i>`;
                if (currentPage === 1) btnPrev.disabled = true;
                else {
                    btnPrev.addEventListener("click", function () {
                        currentPage--;
                        renderTable();
                    });
                }
                controlsContainer.appendChild(btnPrev);

                for (var i = 1; i <= totalPages; i++) {
                    var btnPage = document.createElement("button");
                    btnPage.className = `btn btn--small ${currentPage === i ? 'btn--primary' : 'btn--outline'}`;
                    btnPage.innerText = i;
                    (function (p) {
                        btnPage.addEventListener("click", function () {
                            currentPage = p;
                            renderTable();
                        });
                    })(i);
                    controlsContainer.appendChild(btnPage);
                }

                var btnNext = document.createElement("button");
                btnNext.className = "btn btn--outline btn--small";
                btnNext.innerHTML = `<i class="bi bi-chevron-right"></i>`;
                if (currentPage === totalPages) btnNext.disabled = true;
                else {
                    btnNext.addEventListener("click", function () {
                        currentPage++;
                        renderTable();
                    });
                }
                controlsContainer.appendChild(btnNext);
            };

            var renderTable = function () {
                var totalItems = filteredRows.length;
                var totalPages = Math.ceil(totalItems / itemsPerPage) || 1;

                if (currentPage > totalPages) currentPage = totalPages;
                if (currentPage < 1) currentPage = 1;

                var startIndex = (currentPage - 1) * itemsPerPage;
                var endIndex = Math.min(startIndex + itemsPerPage, totalItems);

                allRows.forEach(function (row) { row.style.display = "none"; });
                for (var i = startIndex; i < endIndex; i++) {
                    if (filteredRows[i]) filteredRows[i].style.display = "";
                }

                var summaryEl = document.getElementById("paginationSummary");
                if (summaryEl) {
                    summaryEl.innerText = totalItems > 0
                        ? `Mostrando ${startIndex + 1} a ${endIndex} de ${totalItems} registros`
                        : "Mostrando 0 a 0 de 0 registros";
                }

                renderControls(totalPages);
                updateBadge();
            };

            var filtrarCuentas = function () {
                var mes = filtroMesCxc ? filtroMesCxc.value : "TODOS";
                var query = buscarClienteCxc ? buscarClienteCxc.value.toLowerCase().trim() : "";

                filteredRows = allRows.filter(function (row) {
                    var factura = row.children[0] ? row.children[0].innerText.toLowerCase() : "";
                    var cliente = row.children[1] ? row.children[1].innerText.toLowerCase() : "";
                    var rowMes = row.dataset.mes || "";

                    var coincideTexto = factura.includes(query) || cliente.includes(query);
                    var coincideMes = (mes === "TODOS" || rowMes === mes);

                    return coincideTexto && coincideMes;
                });

                currentPage = 1;
                renderTable();
            };

            // Poblar combobox de meses
            if (filtroMesCxc) {
                var mesesSet = new Set();
                allRows.forEach(function (row) {
                    if (row.dataset.mes) mesesSet.add(row.dataset.mes);
                });

                var mesesArray = Array.from(mesesSet).sort().reverse();
                var monthNames = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];

                filtroMesCxc.innerHTML = '<option value="TODOS">Todos los meses</option>';
                mesesArray.forEach(function (mes) {
                    var option = document.createElement("option");
                    option.value = mes;
                    var parts = mes.split('-');
                    if (parts.length === 2) {
                        var y = parts[0];
                        var m = parseInt(parts[1], 10);
                        option.text = `${monthNames[m - 1]} ${y}`;
                        filtroMesCxc.appendChild(option);
                    }
                });

                filtroMesCxc.addEventListener("change", filtrarCuentas);
            }

            if (buscarClienteCxc) {
                buscarClienteCxc.addEventListener("input", filtrarCuentas);
            }

            filtrarCuentas();
        },

        /**
         * Paginación y Filtrado por Meses de Facturas de Crédito (`pagos_credito.html`)
         */
        initPaginationCredito: function () {
            var estadoSwitcherBtns = document.querySelectorAll('#estadoSwitcher .segmented-control__btn');
            var filtroMesCxc = document.getElementById("filtro_mes_cxc");
            var buscarClienteCxc = document.getElementById("buscarClienteCxc");
            var badgeCantidadRegistros = document.getElementById("badgeCantidadRegistros");
            var inputEstadoActual = document.getElementById("estado_actual");

            if (!document.getElementById("tablaContainerPendientes")) return;

            var currentPage = 1;
            var itemsPerPage = 10;
            var allRows = [];
            var filteredRows = [];

            var renderControls = function (totalPages) {
                var controlsContainer = document.getElementById("paginationControls");
                if (!controlsContainer) return;
                controlsContainer.innerHTML = "";
                if (totalPages <= 1) return;

                var btnPrev = document.createElement("button");
                btnPrev.className = "btn btn--outline btn--small";
                btnPrev.innerHTML = `<i class="bi bi-chevron-left"></i>`;
                if (currentPage === 1) btnPrev.disabled = true;
                else {
                    btnPrev.addEventListener("click", function () {
                        currentPage--;
                        renderTable();
                    });
                }
                controlsContainer.appendChild(btnPrev);

                for (var i = 1; i <= totalPages; i++) {
                    var btnPage = document.createElement("button");
                    btnPage.className = `btn btn--small ${currentPage === i ? 'btn--primary' : 'btn--outline'}`;
                    btnPage.innerText = i;
                    (function (p) {
                        btnPage.addEventListener("click", function () {
                            currentPage = p;
                            renderTable();
                        });
                    })(i);
                    controlsContainer.appendChild(btnPage);
                }

                var btnNext = document.createElement("button");
                btnNext.className = "btn btn--outline btn--small";
                btnNext.innerHTML = `<i class="bi bi-chevron-right"></i>`;
                if (currentPage === totalPages) btnNext.disabled = true;
                else {
                    btnNext.addEventListener("click", function () {
                        currentPage++;
                        renderTable();
                    });
                }
                controlsContainer.appendChild(btnNext);
            };

            var renderTable = function () {
                var totalItems = filteredRows.length;
                var totalPages = Math.ceil(totalItems / itemsPerPage) || 1;

                if (currentPage > totalPages) currentPage = totalPages;
                if (currentPage < 1) currentPage = 1;

                var startIndex = (currentPage - 1) * itemsPerPage;
                var endIndex = Math.min(startIndex + itemsPerPage, totalItems);

                var totalFacturado = 0;
                allRows.forEach(function (row) { row.style.display = "none"; });

                for (var i = startIndex; i < endIndex; i++) {
                    if (filteredRows[i]) filteredRows[i].style.display = "";
                }

                filteredRows.forEach(function (row) {
                    var cell3 = row.children[3];
                    if (cell3) {
                        var totalText = cell3.innerText.replace("C$", "").replace(/,/g, "").trim();
                        var monto = parseFloat(totalText) || 0;
                        totalFacturado += monto;
                    }
                });

                var summaryEl = document.getElementById("paginationSummary");
                if (summaryEl) {
                    summaryEl.innerHTML =
                        (totalItems > 0
                            ? `Mostrando ${startIndex + 1} a ${endIndex} de ${totalItems} registros`
                            : "Mostrando 0 a 0 de 0 registros") +
                        ` | <strong style="color: var(--color-primary-dark); font-weight: bold; margin-left: 10px;">Total página: C$ ${totalFacturado.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>`;
                }

                renderControls(totalPages);
            };

            var filtrarCuentas = function () {
                var mes = filtroMesCxc ? filtroMesCxc.value : "TODOS";
                var query = buscarClienteCxc ? buscarClienteCxc.value.toLowerCase().trim() : "";

                filteredRows = allRows.filter(function (row) {
                    var factura = row.children[0] ? row.children[0].innerText.toLowerCase() : "";
                    var cliente = row.children[1] ? row.children[1].innerText.toLowerCase() : "";
                    var fechaCell = row.children[2] ? row.children[2].innerText.trim() : "";

                    var coincideTexto = factura.includes(query) || cliente.includes(query);

                    var coincideMes = true;
                    if (mes !== "TODOS") {
                        if (fechaCell && fechaCell !== '-') {
                            var parts = fechaCell.split('/');
                            if (parts.length === 3) {
                                var mesAnio = `${parts[2]}-${parts[1].padStart(2, '0')}`;
                                coincideMes = (mesAnio === mes || `${parts[1]}/${parts[2]}` === mes);
                            } else {
                                coincideMes = false;
                            }
                        } else {
                            coincideMes = false;
                        }
                    }

                    return coincideTexto && coincideMes;
                });

                if (badgeCantidadRegistros) {
                    badgeCantidadRegistros.textContent = filteredRows.length;
                }

                currentPage = 1;
                renderTable();
            };

            var inicializarFiltroMeses = function () {
                if (!filtroMesCxc) return;
                var mesesSet = new Set();
                allRows.forEach(function (row) {
                    var fechaCell = row.children[2] ? row.children[2].innerText.trim() : "";
                    if (fechaCell && fechaCell !== '-') {
                        var parts = fechaCell.split('/');
                        if (parts.length === 3) {
                            var mesAnio = `${parts[2]}-${parts[1].padStart(2, '0')}`;
                            mesesSet.add(mesAnio);
                        }
                    }
                });

                var mesesArray = Array.from(mesesSet).sort().reverse();
                var nombreMeses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];

                filtroMesCxc.innerHTML = '<option value="TODOS">Todos los meses</option>';
                mesesArray.forEach(function (mesAnio) {
                    var parts = mesAnio.split('-');
                    if (parts.length === 2) {
                        var y = parts[0];
                        var m = parseInt(parts[1], 10);
                        var option = document.createElement("option");
                        option.value = mesAnio;
                        option.textContent = `${nombreMeses[m - 1]} ${y}`;
                        filtroMesCxc.appendChild(option);
                    }
                });
            };

            var actualizarTablaActiva = function () {
                var estadoActual = inputEstadoActual ? inputEstadoActual.value : 'PENDIENTES';
                var tablaPendientes = document.getElementById('tablaContainerPendientes');
                var tablaPagadas = document.getElementById('tablaContainerPagadas');

                if (tablaPendientes && tablaPagadas) {
                    if (estadoActual === 'PENDIENTES') {
                        tablaPendientes.classList.add('tabla-activa');
                        tablaPendientes.style.display = '';
                        tablaPagadas.classList.remove('tabla-activa');
                        tablaPagadas.style.display = 'none';
                    } else {
                        tablaPagadas.classList.add('tabla-activa');
                        tablaPagadas.style.display = '';
                        tablaPendientes.classList.remove('tabla-activa');
                        tablaPendientes.style.display = 'none';
                    }
                }

                var containerActivo = document.querySelector(".tabla-activa");
                if (containerActivo) {
                    allRows = Array.from(containerActivo.querySelectorAll(".fila-factura"));
                } else {
                    allRows = [];
                }

                inicializarFiltroMeses();
                filtrarCuentas();
            };

            if (estadoSwitcherBtns.length > 0) {
                estadoSwitcherBtns.forEach(function (btn) {
                    btn.addEventListener('click', function () {
                        estadoSwitcherBtns.forEach(function (b) { b.classList.remove('is-active'); });
                        this.classList.add('is-active');
                        if (inputEstadoActual) inputEstadoActual.value = this.dataset.value;
                        actualizarTablaActiva();
                    });
                });
            }

            if (filtroMesCxc) filtroMesCxc.addEventListener("change", filtrarCuentas);
            if (buscarClienteCxc) buscarClienteCxc.addEventListener("input", filtrarCuentas);

            actualizarTablaActiva();
        },

        /**
         * Lógica de Pagos de Contado (`pagos_contado.html`)
         */
        initPagosContado: function () {
            var self = this;
            var selectTipoPagoContado = document.getElementById("pagarTipoPago");
            var bancoSelectContado = document.getElementById("contado_banco_id");

            var actualizarCamposMetodoPagoContado = function () {
                var val = selectTipoPagoContado ? selectTipoPagoContado.value : "EFECTIVO";
                var cajaBancoRef = document.getElementById("cajaCamposBancoRefContado");
                var grupoBanco = document.getElementById("grupoBancoContado");
                var grupoReferencia = document.getElementById("grupoReferenciaContado");
                var cajaPagoMixto = document.getElementById("cajaPagoMixtoContado");

                if (val === "TRANSFERENCIA") {
                    if (cajaBancoRef) cajaBancoRef.style.display = "grid";
                    if (grupoBanco) grupoBanco.style.display = "block";
                    if (grupoReferencia) grupoReferencia.style.display = "block";
                    if (cajaPagoMixto) cajaPagoMixto.style.display = "none";
                } else if (val === "MIXTO") {
                    if (cajaBancoRef) cajaBancoRef.style.display = "grid";
                    if (grupoBanco) grupoBanco.style.display = "block";
                    if (grupoReferencia) grupoReferencia.style.display = "block";
                    if (cajaPagoMixto) cajaPagoMixto.style.display = "grid";
                } else {
                    if (cajaBancoRef) cajaBancoRef.style.display = "none";
                    if (grupoBanco) grupoBanco.style.display = "none";
                    if (grupoReferencia) grupoReferencia.style.display = "none";
                    if (cajaPagoMixto) cajaPagoMixto.style.display = "none";
                }
            };

            if (selectTipoPagoContado) {
                selectTipoPagoContado.addEventListener("change", actualizarCamposMetodoPagoContado);
            }

            // Modal Nuevo Banco Contado
            var btnAbrirNuevoBancoContadoModal = document.getElementById("btnAbrirNuevoBancoContadoModal");
            var btnGuardarNuevoBancoContado = document.getElementById("btnGuardarNuevoBancoContado");
            var inputNuevoBancoNombreContado = document.getElementById("nuevo_banco_nombre_contado");

            if (btnAbrirNuevoBancoContadoModal) {
                btnAbrirNuevoBancoContadoModal.addEventListener("click", function () {
                    if (inputNuevoBancoNombreContado) inputNuevoBancoNombreContado.value = "";
                    window.ERP.UI.openModal("modalNuevoBancoContado");
                });
            }

            if (btnGuardarNuevoBancoContado) {
                btnGuardarNuevoBancoContado.addEventListener("click", async function () {
                    var nom = inputNuevoBancoNombreContado ? inputNuevoBancoNombreContado.value.trim() : "";
                    if (!nom) {
                        if (inputNuevoBancoNombreContado) inputNuevoBancoNombreContado.focus();
                        return;
                    }

                    try {
                        var resp = await fetch("/bancos/guardar", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ nombre: nom })
                        });
                        var data = await resp.json();
                        if (data.success) {
                            window.ERP.UI.closeModal("modalNuevoBancoContado");
                            self.showToast(data.message || "Banco registrado correctamente", "success");
                            await self.cargarBancos(bancoSelectContado);
                            if (data.banco && bancoSelectContado) {
                                bancoSelectContado.value = data.banco.id;
                            }
                        } else {
                            self.showToast(data.message || "Error al registrar banco", "danger");
                        }
                    } catch (err) {
                        self.showToast("Error de conexión al guardar banco.", "danger");
                    }
                });
            }

            // Botón Abonar / Pagar Factura Contado
            document.querySelectorAll(".btn-abonar[data-saldo]").forEach(function (btn) {
                btn.addEventListener("click", function (e) {
                    e.stopPropagation();
                    var ventaId = this.dataset.ventaId;
                    var factura = this.dataset.factura;
                    var cliente = this.dataset.cliente || "N/D";
                    var saldo = this.dataset.saldo;

                    var pVId = document.getElementById("pagarVentaId");
                    var lFact = document.getElementById("lblFacturaPagar");
                    var lCli = document.getElementById("lblClientePagar");
                    var pMont = document.getElementById("pagarMonto");
                    var pFech = document.getElementById("pagarFecha");
                    var pRef = document.getElementById("pagarReferencia");
                    var pObs = document.getElementById("pagarObservaciones");

                    if (pVId) pVId.value = ventaId;
                    if (lFact) lFact.innerText = `#${factura}`;
                    if (lCli) lCli.innerText = cliente;
                    if (pMont) pMont.value = Number(saldo).toFixed(2);
                    if (pFech) pFech.value = new Date().toISOString().split("T")[0];
                    if (selectTipoPagoContado) selectTipoPagoContado.value = "EFECTIVO";
                    if (pRef) pRef.value = "";
                    if (pObs) pObs.value = "";

                    self.cargarBancos(bancoSelectContado);
                    actualizarCamposMetodoPagoContado();
                    window.ERP.UI.openModal("modalPagarFactura");
                });
            });

            var formPagarFactura = document.getElementById("formPagarFactura");
            if (formPagarFactura) {
                formPagarFactura.addEventListener("submit", async function (e) {
                    e.preventDefault();
                    var formData = new FormData(this);
                    try {
                        var respuesta = await fetch("/guardar-pago", {
                            method: "POST",
                            body: formData
                        });
                        var resultado = await respuesta.json();
                        if (resultado.success) {
                            window.ERP.UI.closeModal("modalPagarFactura");
                            self.showToast('Pago registrado exitosamente.', 'success');
                            setTimeout(function () { location.reload(); }, 1800);
                        } else {
                            self.showToast(resultado.message, 'danger');
                        }
                    } catch (err) {
                        self.showToast('Error de conexión al procesar el pago.', 'danger');
                    }
                });
            }

            // Anular Factura
            document.querySelectorAll(".btn-anular-factura").forEach(function (btn) {
                btn.addEventListener("click", function (e) {
                    e.stopPropagation();
                    var factura = this.dataset.factura;
                    var action = this.dataset.action;

                    var lAnu = document.getElementById("lblAnularFactura");
                    var fAnu = document.getElementById("formAnularFactura");

                    if (lAnu) lAnu.innerText = `#${factura}`;
                    if (fAnu) fAnu.action = action;

                    window.ERP.UI.openModal("modalAnularFactura");
                });
            });
        },

        /**
         * Lógica de Pagos de Crédito (`pagos_credito.html`)
         */
        initPagosCredito: function () {
            var self = this;
            var formAbonarFactura = document.getElementById("formAbonarFactura");

            document.querySelectorAll(".btn-abonar[data-saldo-pendiente]").forEach(function (btn) {
                btn.addEventListener("click", function (e) {
                    e.stopPropagation();
                    var ventaId = this.dataset.ventaId;
                    var factura = this.dataset.factura;
                    var cliente = this.dataset.cliente || "N/D";
                    var saldo = this.dataset.saldo;

                    var aVId = document.getElementById("abonarVentaId");
                    var aSP = document.getElementById("abonarSaldoPendiente");
                    var lFact = document.getElementById("lblFacturaAbonar");
                    var lCli = document.getElementById("lblClienteAbonar");
                    var lSaldo = document.getElementById("lblSaldoPendiente");
                    var aMont = document.getElementById("abonarMonto");
                    var aFech = document.getElementById("abonarFecha");
                    var aForm = document.getElementById("abonarForma");
                    var aRef = document.getElementById("abonarReferencia");
                    var aObs = document.getElementById("abonarObservaciones");

                    if (aVId) aVId.value = ventaId;
                    if (aSP) aSP.value = saldo;
                    if (lFact) lFact.innerText = `#${factura}`;
                    if (lCli) lCli.innerText = cliente;

                    var saldoNumerico = Number(saldo) || 0;
                    if (lSaldo) lSaldo.innerText = "C$ " + saldoNumerico.toFixed(2);
                    if (aMont) {
                        aMont.value = saldoNumerico.toFixed(2);
                        aMont.max = saldoNumerico;
                    }
                    if (aFech) aFech.value = new Date().toISOString().split("T")[0];
                    if (aForm) aForm.value = "";
                    if (aRef) aRef.value = "";
                    if (aObs) aObs.value = "";

                    window.ERP.UI.openModal("modalAbonarFactura");
                });
            });

            if (formAbonarFactura) {
                formAbonarFactura.addEventListener("submit", async function (e) {
                    e.preventDefault();

                    var saldo = Number(document.getElementById("abonarSaldoPendiente") ? document.getElementById("abonarSaldoPendiente").value : 0);
                    var monto = Number(document.getElementById("abonarMonto") ? document.getElementById("abonarMonto").value : 0);
                    var forma = document.getElementById("abonarForma") ? document.getElementById("abonarForma").value : '';
                    var fecha = document.getElementById("abonarFecha") ? document.getElementById("abonarFecha").value : '';

                    if (monto <= 0) {
                        self.showToast('Ingrese un monto de abono mayor a cero.', 'warning');
                        return;
                    }

                    if (monto > saldo) {
                        self.showToast('El abono no puede superar el saldo pendiente.', 'warning');
                        return;
                    }

                    if (!forma || !fecha) {
                        self.showToast('Verifique forma de pago y fecha.', 'warning');
                        return;
                    }

                    var formData = new FormData(this);

                    try {
                        var respuesta = await fetch("/guardar-pago", {
                            method: "POST",
                            body: formData
                        });

                        var resultado = await respuesta.json();

                        if (resultado.success) {
                            window.ERP.UI.closeModal("modalAbonarFactura");
                            self.showToast('Abono registrado exitosamente.', 'success');
                            setTimeout(function () { location.reload(); }, 1800);
                        } else {
                            self.showToast(resultado.message, 'danger');
                        }
                    } catch (err) {
                        self.showToast('Error al conectar con el servidor.', 'danger');
                    }
                });
            }

            // Historial de abonos
            document.querySelectorAll(".btn-historial-abonos").forEach(function (btn) {
                btn.addEventListener("click", function (e) {
                    e.stopPropagation();
                    var ventaId = this.dataset.ventaId;
                    var factura = this.dataset.factura;
                    var cliente = this.dataset.cliente || "N/D";

                    var lF = document.getElementById("lblFacturaHistorial");
                    var lC = document.getElementById("lblClienteHistorial");
                    var hBody = document.getElementById("historialAbonosBody");

                    if (lF) lF.innerText = `#${factura}`;
                    if (lC) lC.innerText = cliente;

                    var template = document.getElementById('historial-template-' + ventaId);
                    if (hBody) {
                        if (template) {
                            hBody.innerHTML = template.innerHTML;
                        } else {
                            hBody.innerHTML = "<div style='padding: 24px; text-align: center; color: var(--color-text-muted);'>No hay historial de abonos disponible.</div>";
                        }
                    }

                    window.ERP.UI.openModal("modalHistorialAbonos");
                });
            });

            // Anulación de pagos en vista de pagos crédito
            document.addEventListener("click", function (e) {
                var btnAnular = e.target.closest(".btn-anular-pago");
                if (btnAnular) {
                    e.stopPropagation();
                    self.pagoIdToCancel = btnAnular.dataset.id;
                    var txtMotivo = document.getElementById("motivoAnulacionPago");
                    if (txtMotivo) txtMotivo.value = "";
                    window.ERP.UI.openModal("modalAnularPago");
                }
            });

            var btnConfirmarAnularPago = document.getElementById("btnConfirmarAnularPago");
            if (btnConfirmarAnularPago) {
                btnConfirmarAnularPago.addEventListener("click", async function () {
                    if (!self.pagoIdToCancel) return;
                    var txtMotivo = document.getElementById("motivoAnulacionPago");
                    var motivo = txtMotivo ? txtMotivo.value.trim() : "";

                    if (!motivo) {
                        self.showToast("Por favor ingrese el motivo de anulación.", "warning");
                        if (txtMotivo) txtMotivo.focus();
                        return;
                    }

                    try {
                        var resp = await fetch("/pagos/anular/" + self.pagoIdToCancel, {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ motivo: motivo })
                        });
                        var res = await resp.json();

                        if (res.success) {
                            window.ERP.UI.closeModal("modalAnularPago");
                            self.showToast(res.message || "Pago anulado correctamente", "success");
                            setTimeout(function () { location.reload(); }, 1500);
                        } else {
                            self.showToast(res.message || "Error al anular el pago", "danger");
                        }
                    } catch (e) {
                        self.showToast("Error de conexión al anular el pago.", "danger");
                    }
                });
            }
        },

        /**
         * Lógica del Historial Completo de Factura (`historial_factura.html`)
         */
        initHistorialFactura: function () {
            var self = this;
            var selectBanco = document.getElementById("abono_banco_id");
            var selectTipoPago = document.getElementById("abono_tipo_pago");

            var actualizarCamposMetodoPago = function () {
                var val = selectTipoPago ? selectTipoPago.value : "EFECTIVO";
                var cajaBancoRef = document.getElementById("cajaCamposBancoRef");
                var grupoBanco = document.getElementById("grupoBanco");
                var grupoReferencia = document.getElementById("grupoReferencia");
                var cajaPagoMixto = document.getElementById("cajaPagoMixto");

                if (val === "TRANSFERENCIA") {
                    if (cajaBancoRef) cajaBancoRef.style.display = "grid";
                    if (grupoBanco) grupoBanco.style.display = "block";
                    if (grupoReferencia) grupoReferencia.style.display = "block";
                    if (cajaPagoMixto) cajaPagoMixto.style.display = "none";
                } else if (val === "MIXTO") {
                    if (cajaBancoRef) cajaBancoRef.style.display = "grid";
                    if (grupoBanco) grupoBanco.style.display = "block";
                    if (grupoReferencia) grupoReferencia.style.display = "block";
                    if (cajaPagoMixto) cajaPagoMixto.style.display = "grid";
                } else {
                    if (cajaBancoRef) cajaBancoRef.style.display = "none";
                    if (grupoBanco) grupoBanco.style.display = "none";
                    if (grupoReferencia) grupoReferencia.style.display = "none";
                    if (cajaPagoMixto) cajaPagoMixto.style.display = "none";
                }
            };

            if (selectTipoPago) {
                selectTipoPago.addEventListener("change", actualizarCamposMetodoPago);
            }

            var selectCuotaAbono = document.getElementById("abono_select_cuota");
            if (selectCuotaAbono) {
                selectCuotaAbono.addEventListener("change", function () {
                    var opt = this.options[this.selectedIndex];
                    var abonoMonto = document.getElementById("abono_monto_pago");
                    if (opt && opt.dataset.saldo && abonoMonto) {
                        abonoMonto.value = opt.dataset.saldo;
                    }
                });
            }

            var btnAbonarFacturaModal = document.getElementById("btnAbonarFacturaModal");
            if (btnAbonarFacturaModal) {
                btnAbonarFacturaModal.addEventListener("click", function () {
                    if (selectCuotaAbono) selectCuotaAbono.value = "";
                    var hiddenCuotaId = document.getElementById("abono_cuota_id");
                    if (hiddenCuotaId) hiddenCuotaId.value = "";
                    self.cargarBancos(selectBanco);
                    actualizarCamposMetodoPago();
                    window.ERP.UI.openModal("modalRegistrarAbono");
                });
            }

            document.querySelectorAll(".btn-abonar-cuota-trigger").forEach(function (btn) {
                btn.addEventListener("click", function (e) {
                    e.stopPropagation();
                    var cuotaId = this.dataset.cuotaId;
                    var saldo = this.dataset.saldo;

                    if (selectCuotaAbono) selectCuotaAbono.value = cuotaId;
                    var hiddenCuotaId = document.getElementById("abono_cuota_id");
                    if (hiddenCuotaId) hiddenCuotaId.value = cuotaId;

                    var abonoMonto = document.getElementById("abono_monto_pago");
                    if (abonoMonto) abonoMonto.value = saldo;

                    self.cargarBancos(selectBanco);
                    actualizarCamposMetodoPago();
                    window.ERP.UI.openModal("modalRegistrarAbono");
                });
            });

            var btnAbrirNuevoBancoModal = document.getElementById("btnAbrirNuevoBancoModal");
            var btnGuardarNuevoBanco = document.getElementById("btnGuardarNuevoBanco");
            var inputNuevoBancoNombre = document.getElementById("nuevo_banco_nombre");

            if (btnAbrirNuevoBancoModal) {
                btnAbrirNuevoBancoModal.addEventListener("click", function () {
                    if (inputNuevoBancoNombre) inputNuevoBancoNombre.value = "";
                    window.ERP.UI.openModal("modalNuevoBanco");
                });
            }

            if (btnGuardarNuevoBanco) {
                btnGuardarNuevoBanco.addEventListener("click", async function () {
                    var nom = inputNuevoBancoNombre ? inputNuevoBancoNombre.value.trim() : "";
                    if (!nom) {
                        if (inputNuevoBancoNombre) inputNuevoBancoNombre.focus();
                        return;
                    }

                    try {
                        var resp = await fetch("/bancos/guardar", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ nombre: nom })
                        });

                        var res = await resp.json();
                        if (res.success) {
                            window.ERP.UI.closeModal("modalNuevoBanco");
                            await self.cargarBancos(selectBanco, res.banco.id);
                        } else {
                            alert(res.message);
                        }
                    } catch (err) {
                        console.error(err);
                        alert("Error al guardar el banco");
                    }
                });
            }

            var formRegistrarAbono = document.getElementById("formRegistrarAbono");
            if (formRegistrarAbono) {
                formRegistrarAbono.addEventListener("submit", async function (e) {
                    e.preventDefault();
                    var formData = new FormData(this);
                    var btnSubmit = document.getElementById("btnGuardarAbonoSubmit");
                    if (btnSubmit) {
                        btnSubmit.disabled = true;
                        btnSubmit.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Procesando...`;
                    }

                    try {
                        var respuesta = await fetch("/guardar-pago", {
                            method: "POST",
                            body: formData
                        });

                        var resultado = await respuesta.json();

                        if (resultado.success) {
                            window.ERP.UI.closeModal("modalRegistrarAbono");
                            setTimeout(function () { location.reload(); }, 300);
                        } else {
                            alert(resultado.message);
                            if (btnSubmit) {
                                btnSubmit.disabled = false;
                                btnSubmit.innerHTML = `<i class="bi bi-check-lg me-1"></i> Confirmar Abono`;
                            }
                        }
                    } catch (error) {
                        console.error(error);
                        alert("Error procesando el abono");
                        if (btnSubmit) {
                            btnSubmit.disabled = false;
                            btnSubmit.innerHTML = `<i class="bi bi-check-lg me-1"></i> Confirmar Abono`;
                        }
                    }
                });
            }

            document.querySelectorAll(".btn-anular-pago-directo").forEach(function (btn) {
                btn.addEventListener("click", function (e) {
                    e.stopPropagation();
                    self.pagoIdToCancel = this.dataset.id;
                    var txtMotivo = document.getElementById("motivoAnulacionPago");
                    if (txtMotivo) txtMotivo.value = "";
                    window.ERP.UI.openModal("modalAnularPago");
                });
            });
        },

        /**
         * Manejo del detalle de pago simple en modal `#modalDetallePago`
         */
        initModalVerDetallePagoSimple: function () {
            document.querySelectorAll(".btn-ver-pago[data-factura]").forEach(function (btn) {
                btn.addEventListener("click", function () {
                    var factura = this.dataset.factura || "---";
                    var cliente = this.dataset.cliente || "N/D";
                    var referencia = this.dataset.referencia || "-";
                    var banco = this.dataset.banco || "-";
                    var observaciones = this.dataset.observaciones || "Sin observaciones";

                    var dF = document.getElementById("detFactura");
                    var dC = document.getElementById("detCliente");
                    var dM = document.getElementById("detMonto");
                    var dFe = document.getElementById("detFecha");
                    var dFo = document.getElementById("detForma");
                    var dB = document.getElementById("detBanco");
                    var dR = document.getElementById("detReferencia");
                    var dO = document.getElementById("detObservaciones");

                    if (dF) dF.innerText = `#${factura}`;
                    if (dC) dC.innerText = cliente;
                    if (dM) dM.innerText = this.dataset.monto || '0.00';
                    if (dFe) dFe.innerText = this.dataset.fecha || "--/--/----";
                    if (dFo) dFo.innerText = this.dataset.forma || "EFECTIVO";
                    if (dB) dB.innerText = banco !== "" ? banco : "-";
                    if (dR) dR.innerText = referencia !== "" ? referencia : "-";
                    if (dO) dO.innerText = observaciones !== "" ? observaciones : "Sin observaciones";

                    window.ERP.UI.openModal("modalDetallePago");
                });
            });
        },

        init: function () {
            this.initPaginationContado();
            this.initPaginationCredito();
            this.initPagosContado();
            this.initPagosCredito();
            this.initHistorialFactura();
            this.initModalVerDetallePagoSimple();
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        window.ERP.Pagos.init();
    });

})(window, document);
