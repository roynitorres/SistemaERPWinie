/* ==========================================================================
   SISTEMA ERP WINIE — MÓDULO DE VENTAS / POS (static/js/modules/ventas.js)
   Búsqueda de productos, carrito dinámico, calculador de crédito y facturación
   ========================================================================== */

(function (window, document) {
    'use strict';

    window.ERP = window.ERP || {};

    window.ERP.Ventas = {
        detalleVenta: [],
        categoriaSeleccionada: 'TODAS',
        searchDebounceTimer: null,
        productosMap: {},

        /**
         * Muestra una notificación Toast flotante
         */
        mostrarMensaje: function (tipo, mensaje) {
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
         * Control del Stepper (Paso 1: Selección Productos vs Paso 2: Datos Cliente y Crédito)
         */
        initStepper: function () {
            var self = this;
            var pillPaso1 = document.getElementById('pillPaso1');
            var pillPaso2 = document.getElementById('pillPaso2');
            var vistaPaso1 = document.getElementById('vistaPaso1');
            var vistaPaso2 = document.getElementById('vistaPaso2');
            var btnIrPaso2 = document.getElementById('btnIrPaso2');
            var btnVolverPaso1 = document.getElementById('btnVolverPaso1');
            var inputClienteNombre = document.getElementById('cliente_nombre');

            this.irAPaso = function (paso) {
                if (paso === 1) {
                    if (pillPaso1) pillPaso1.classList.add('active');
                    if (pillPaso2) pillPaso2.classList.remove('active');
                    if (vistaPaso1) vistaPaso1.style.display = 'block';
                    if (vistaPaso2) vistaPaso2.style.display = 'none';
                } else {
                    if (pillPaso1) pillPaso1.classList.remove('active');
                    if (pillPaso2) pillPaso2.classList.add('active');
                    if (vistaPaso1) vistaPaso1.style.display = 'none';
                    if (vistaPaso2) vistaPaso2.style.display = 'block';
                    if (inputClienteNombre) inputClienteNombre.focus();
                }
            };

            if (pillPaso1) pillPaso1.addEventListener('click', function () { self.irAPaso(1); });
            if (pillPaso2) pillPaso2.addEventListener('click', function () { self.irAPaso(2); });
            if (btnIrPaso2) btnIrPaso2.addEventListener('click', function () { self.irAPaso(2); });
            if (btnVolverPaso1) btnVolverPaso1.addEventListener('click', function () { self.irAPaso(1); });
        },

        /**
         * Selección de cliente mediante Datalist
         */
        initClienteDatalist: function () {
            var inputClienteNombre = document.getElementById('cliente_nombre');
            var inputClienteId = document.getElementById('cliente_id');
            var datalistClientes = document.getElementById('clientesList');

            if (!inputClienteNombre || !datalistClientes) return;

            var checkClienteSelection = function () {
                var val = inputClienteNombre.value.trim().toLowerCase();
                var options = Array.from(datalistClientes.options);
                var selectedOption = options.find(function (opt) {
                    return opt.value.trim().toLowerCase() === val;
                });

                if (selectedOption) {
                    if (inputClienteId) inputClienteId.value = selectedOption.dataset.id;
                } else {
                    if (inputClienteId) inputClienteId.value = '';
                }
            };

            inputClienteNombre.addEventListener('input', checkClienteSelection);
            inputClienteNombre.addEventListener('change', checkClienteSelection);
        },

        /**
         * Búsqueda dinámica de productos en modal
         */
        initBuscadorProductosModal: function () {
            var self = this;
            var buscarProducto = document.getElementById('buscarProducto');
            var btnAgregarProdElem = document.getElementById('btnAgregarProducto');

            if (btnAgregarProdElem) {
                btnAgregarProdElem.addEventListener('click', function () {
                    window.ERP.UI.openModal('modalProductos');
                    self.buscarProductos(buscarProducto ? buscarProducto.value.trim() : '');
                });
            }

            document.querySelectorAll('.modal-cat-pill').forEach(function (pill) {
                pill.addEventListener('click', function () {
                    document.querySelectorAll('.modal-cat-pill').forEach(function (p) {
                        p.classList.remove('state-pill--active');
                    });
                    this.classList.add('state-pill--active');
                    self.categoriaSeleccionada = this.dataset.categoriaId || 'TODAS';
                    self.buscarProductos(buscarProducto ? buscarProducto.value.trim() : '');
                });
            });

            if (buscarProducto) {
                buscarProducto.addEventListener('input', function () {
                    clearTimeout(self.searchDebounceTimer);
                    var val = this.value.trim();
                    self.searchDebounceTimer = setTimeout(function () {
                        self.buscarProductos(val);
                    }, 200);
                });
            }

            var btnAgregarMultiple = document.getElementById('btnAgregarDetalleMultiple');
            if (btnAgregarMultiple) {
                btnAgregarMultiple.addEventListener('click', function () {
                    self.agregarProductosSeleccionados();
                });
            }

            var btnLimpiarModal = document.getElementById('btnLimpiarModal');
            if (btnLimpiarModal) {
                btnLimpiarModal.addEventListener('click', function () {
                    self.limpiarModalProducto();
                });
            }
        },

        buscarProductos: async function (textoBusqueda) {
            var tbodyBusqueda = document.getElementById('tbodyBusquedaProductos');
            if (!tbodyBusqueda) return;

            tbodyBusqueda.innerHTML = `
                <tr class="data-table__row">
                    <td colspan="6" class="data-table__cell text-center py-3 text-muted">
                        <i class="bi bi-arrow-repeat spin me-2"></i> Cargando productos...
                    </td>
                </tr>
            `;

            this.productosMap = {};
            var self = this;

            try {
                var url = '/buscar-productos?busqueda=' + encodeURIComponent(textoBusqueda || '') + '&categoria_id=' + encodeURIComponent(this.categoriaSeleccionada);
                var respuesta = await fetch(url);
                var productos = await respuesta.json();

                tbodyBusqueda.innerHTML = '';

                if (productos.length === 0) {
                    tbodyBusqueda.innerHTML = `
                        <tr class="data-table__row">
                            <td colspan="6" class="data-table__cell text-center py-3" style="color: var(--color-danger);">
                                <i class="bi bi-emoji-frown me-1"></i> No se encontraron productos en esta categoría
                            </td>
                        </tr>
                    `;
                    self.updateModalSelectionSummary();
                    return;
                }

                productos.forEach(function (producto) {
                    self.productosMap[producto.id] = producto;
                    var tr = document.createElement('tr');
                    tr.className = 'data-table__row fila-prod-busqueda';
                    tr.style.cursor = 'pointer';
                    tr.dataset.prodId = producto.id;

                    tr.innerHTML = `
                        <td class="data-table__cell">
                            <div class="customer-cell-wrapper">
                                <div class="avatar-circle-apex" style="background: linear-gradient(135deg, #00e676 0%, #00b0ff 100%); color: #090a0f;">
                                    <i class="bi bi-box-seam-fill"></i>
                                </div>
                                <div>
                                    <span class="customer-title-text">${producto.nombre}</span>
                                    <span class="customer-sub-text">${producto.marca || 'Sin marca'}</span>
                                </div>
                            </div>
                        </td>
                        <td class="data-table__cell" style="font-weight: 600; color: var(--color-primary);">${producto.codigo}</td>
                        <td class="data-table__cell ">${producto.categoria}</td>
                        <td class="data-table__cell text-end" style="font-weight: 700; color: #00e676;">C$ ${producto.precio.toFixed(2)}</td>
                        <td class="data-table__cell text-center">
                            <span class="badge-pill-apex ${producto.stock > 0 ? 'badge-pill-apex--active' : 'badge-pill-apex--inactive'}">
                                ${producto.stock} en stock
                            </span>
                        </td>
                        <td class="data-table__cell text-center" onclick="event.stopPropagation();">
                            <input type="checkbox" class="producto-checkbox" value="${producto.id}">
                        </td>
                    `;

                    tr.addEventListener('dblclick', function () {
                        var pId = this.dataset.prodId;
                        var prod = self.productosMap[pId];
                        if (prod) self.agregarUnProductoAlDetalle(prod);
                    });

                    tbodyBusqueda.appendChild(tr);
                });

                document.querySelectorAll('.producto-checkbox').forEach(function (cb) {
                    cb.addEventListener('change', function () {
                        self.updateModalSelectionSummary();
                    });
                });

                self.updateModalSelectionSummary();

            } catch (error) {
                console.error(error);
                tbodyBusqueda.innerHTML = `
                    <tr class="data-table__row">
                        <td colspan="6" class="data-table__cell text-center py-3" style="color: var(--color-danger);">
                            Error al cargar los productos
                        </td>
                    </tr>
                `;
            }
        },

        updateModalSelectionSummary: function () {
            var checkboxes = document.querySelectorAll('.producto-checkbox:checked');
            var count = checkboxes.length;
            var totalEstimado = 0;
            var self = this;

            checkboxes.forEach(function (cb) {
                var pId = cb.value;
                var prod = self.productosMap[pId];
                if (prod) {
                    totalEstimado += prod.precio;
                    var row = cb.closest('tr');
                    if (row) row.style.backgroundColor = 'rgba(0, 230, 118, 0.08)';
                }
            });

            document.querySelectorAll('.producto-checkbox:not(:checked)').forEach(function (cb) {
                var row = cb.closest('tr');
                if (row) row.style.backgroundColor = '';
            });

            var selectedCountText = document.getElementById("selectedCountText");
            if (selectedCountText) {
                if (count > 0) {
                    selectedCountText.innerHTML = '<strong style="color: #00e676;">' + count + '</strong> producto' + (count > 1 ? 's' : '') + ' seleccionado' + (count > 1 ? 's' : '') + ' | Total estimado: <strong style="color: #00e676;">C$ ' + totalEstimado.toFixed(2) + '</strong>';
                } else {
                    selectedCountText.textContent = "0 productos seleccionados";
                }
            }
        },

        agregarUnProductoAlDetalle: function (producto) {
            if (producto.stock <= 0) {
                this.mostrarMensaje("danger", "El producto " + producto.nombre + " está agotado");
                return;
            }

            var existe = this.detalleVenta.find(function (p) { return p.producto_id === producto.id; });
            if (existe) {
                this.mostrarMensaje("warning", "El producto " + producto.nombre + " ya está en la factura");
                return;
            }

            this.detalleVenta.push({
                producto_id: producto.id,
                codigo: producto.codigo,
                nombre: producto.nombre,
                precio: producto.precio,
                descuento_monto: 0,
                cantidad: 1,
                stock: producto.stock,
                subtotal: producto.precio
            });

            this.renderizarTabla();
            this.mostrarMensaje("success", 'Se agregó "' + producto.nombre + '" a la factura');
            window.ERP.UI.closeModal('modalProductos');
        },

        agregarProductosSeleccionados: function () {
            var checkboxes = document.querySelectorAll('.producto-checkbox:checked');
            if (checkboxes.length === 0) {
                this.mostrarMensaje("warning", "Seleccione al menos un producto");
                return;
            }

            var agregados = 0;
            var erroresStock = 0;
            var repetidos = 0;
            var self = this;

            checkboxes.forEach(function (cb) {
                var pId = cb.value;
                var producto = self.productosMap[pId];
                if (!producto) return;

                if (producto.stock <= 0) { erroresStock++; return; }
                var existe = self.detalleVenta.find(function (p) { return p.producto_id === producto.id; });
                if (existe) { repetidos++; return; }

                self.detalleVenta.push({
                    producto_id: producto.id,
                    codigo: producto.codigo,
                    nombre: producto.nombre,
                    precio: producto.precio,
                    descuento_monto: 0,
                    cantidad: 1,
                    stock: producto.stock,
                    subtotal: producto.precio
                });
                agregados++;
            });

            if (agregados > 0) this.renderizarTabla();

            if (erroresStock > 0 || repetidos > 0) {
                var msg = [];
                if (erroresStock > 0) msg.push(erroresStock + " sin stock");
                if (repetidos > 0) msg.push(repetidos + " ya en lista");
                this.mostrarMensaje("warning", "Aviso: " + msg.join(", "));
            }

            window.ERP.UI.closeModal("modalProductos");
            this.limpiarModalProducto();
        },

        limpiarModalProducto: function () {
            var bp = document.getElementById("buscarProducto");
            if (bp) bp.value = "";
            var tb = document.getElementById("tbodyBusquedaProductos");
            if (tb) tb.innerHTML = "";
            var checkAll = document.getElementById("selectAllProducts");
            if (checkAll) checkAll.checked = false;
        },

        /**
         * Renderizado de la tabla de ítems del carrito
         */
        renderizarTabla: function () {
            var tbody = document.getElementById("detalleVentaBody");
            if (!tbody) return;
            tbody.innerHTML = "";
            var subtotalGeneral = 0;
            var self = this;

            if (this.detalleVenta.length === 0) {
                tbody.innerHTML = `
                    <tr class="data-table__row">
                        <td colspan="7" class="data-table__cell data-table__cell--center" style="padding: var(--spacing-xl); color: var(--color-text-muted);">
                            <i class="bi bi-box-seam d-block mb-2" style="font-size: 2rem;"></i>
                            Sin productos agregados en el paso 1
                        </td>
                    </tr>
                `;
                this.actualizarTotales(0);
                return;
            }

            this.detalleVenta.forEach(function (producto, index) {
                subtotalGeneral += producto.subtotal;
                var tr = document.createElement('tr');
                tr.className = 'data-table__row';
                tr.innerHTML = `
                    <td class="data-table__cell" style="font-weight: 600; color: var(--color-primary);">${producto.codigo}</td>
                    <td class="data-table__cell" style="font-weight: 600; color: #ffffff;">${producto.nombre}</td>
                    <td class="data-table__cell text-center">
                        <div class="cantidad-control">
                            <button type="button" class="cantidad-btn btn-disminuir" data-index="${index}" title="Disminuir"><i class="bi bi-dash"></i></button>
                            <span class="cantidad-num">${producto.cantidad}</span>
                            <button type="button" class="cantidad-btn btn-aumentar" data-index="${index}" title="Aumentar"><i class="bi bi-plus"></i></button>
                        </div>
                    </td>
                    <td class="data-table__cell text-end" style="color: #ffffff;">C$ ${producto.precio.toFixed(2)}</td>
                    <td class="data-table__cell text-center">
                        <input type="number" class="form-input text-end input-descuento" data-index="${index}" style="width: 85px; padding: 4px 8px; font-weight: 600; background-color: rgba(255,255,255,0.04);" 
                        value="${producto.descuento_monto}" min="0">
                    </td>
                    <td class="data-table__cell text-end" style="font-weight: 700; color: #00e676;">C$ ${producto.subtotal.toFixed(2)}</td>
                    <td class="data-table__cell text-end">
                        <button type="button" class="btn-three-dots btn-eliminar-item" data-index="${index}" title="Quitar producto" style="color: #ff5252; background: rgba(255, 82, 82, 0.1); border: 1px solid rgba(255, 82, 82, 0.2); width: 30px; height: 30px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center;">
                            <i class="bi bi-trash-fill"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });

            tbody.querySelectorAll('.btn-disminuir').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    self.disminuirCantidad(parseInt(this.dataset.index));
                });
            });

            tbody.querySelectorAll('.btn-aumentar').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    self.aumentarCantidad(parseInt(this.dataset.index));
                });
            });

            tbody.querySelectorAll('.btn-eliminar-item').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    self.eliminarProducto(parseInt(this.dataset.index));
                });
            });

            tbody.querySelectorAll('.input-descuento').forEach(function (inp) {
                inp.addEventListener('change', function () {
                    self.actualizarLinea(parseInt(this.dataset.index), 'descuento_monto', this.value);
                });
            });

            this.actualizarTotales(subtotalGeneral);
        },

        actualizarTotales: function (subtotal) {
            var ivaRate = window.empresaIVA !== undefined ? window.empresaIVA / 100 : 0.15;
            var iva = subtotal * ivaRate;
            var total = subtotal + iva;

            var stEl = document.getElementById("subtotalVenta");
            var ivaEl = document.getElementById("ivaVenta");
            var tEl = document.getElementById("totalVenta");
            var tP2 = document.getElementById("totalPaso2");

            if (stEl) stEl.textContent = "C$ " + subtotal.toFixed(2);
            if (ivaEl) ivaEl.textContent = "C$ " + iva.toFixed(2);
            if (tEl) tEl.textContent = "C$ " + total.toFixed(2);
            if (tP2) tP2.textContent = "C$ " + total.toFixed(2);

            var tipoVentaSelect = document.getElementById("tipo_venta");
            if (tipoVentaSelect && tipoVentaSelect.value === "CREDITO") {
                this.generarTablaCuotasSugeridas();
            }
        },

        actualizarLinea: function (index, campo, valor) {
            var p = this.detalleVenta[index];
            if (!p) return;
            var val = parseFloat(valor) || 0;
            if (campo === 'descuento_monto') {
                var bruto = p.cantidad * p.precio;
                var descuentoMonto = Math.min(val, bruto);
                p.descuento_monto = descuentoMonto;
                p.subtotal = bruto - descuentoMonto;
            }
            this.renderizarTabla();
        },

        recalcularItem: function (producto) {
            var bruto = producto.cantidad * producto.precio;
            var descuentoMonto = parseFloat(producto.descuento_monto) || 0;
            producto.subtotal = Math.max(bruto - descuentoMonto, 0);
        },

        eliminarProducto: function (index) {
            this.detalleVenta.splice(index, 1);
            this.renderizarTabla();
        },

        aumentarCantidad: function (index) {
            var producto = this.detalleVenta[index];
            if (!producto) return;
            if (producto.cantidad >= producto.stock) {
                this.mostrarMensaje("danger", "No hay más stock disponible");
                return;
            }
            producto.cantidad++;
            this.recalcularItem(producto);
            this.renderizarTabla();
        },

        disminuirCantidad: function (index) {
            var producto = this.detalleVenta[index];
            if (!producto) return;
            if (producto.cantidad <= 1) return;
            producto.cantidad--;
            this.recalcularItem(producto);
            this.renderizarTabla();
        },

        /**
         * Lógica de crédito y generación automática de plan de cuotas
         */
        initCredito: function () {
            var self = this;
            var tipoVentaSelect = document.getElementById("tipo_venta");
            var panelCuotasCredito = document.getElementById("panelCuotasCredito");

            var actualizarVistaCredito = function () {
                if (tipoVentaSelect && tipoVentaSelect.value === "CREDITO") {
                    if (panelCuotasCredito) panelCuotasCredito.style.display = "block";
                    self.generarTablaCuotasSugeridas();
                } else {
                    if (panelCuotasCredito) panelCuotasCredito.style.display = "none";
                }
            };

            if (tipoVentaSelect) {
                tipoVentaSelect.addEventListener("change", actualizarVistaCredito);
            }

            var inputNumCuotas = document.getElementById("num_cuotas");
            var selectFrecuenciaPago = document.getElementById("frecuencia_pago");
            var inputDiasGraciaCuota = document.getElementById("dias_gracia_cuota");
            var btnGenerarCuotas = document.getElementById("btnGenerarCuotas");

            [inputNumCuotas, selectFrecuenciaPago, inputDiasGraciaCuota].forEach(function (el) {
                if (el) {
                    el.addEventListener("change", function () { self.generarTablaCuotasSugeridas(); });
                    el.addEventListener("input", function () { self.generarTablaCuotasSugeridas(); });
                }
            });
            if (btnGenerarCuotas) {
                btnGenerarCuotas.addEventListener("click", function () { self.generarTablaCuotasSugeridas(); });
            }
        },

        generarTablaCuotasSugeridas: function () {
            var tbodyCuotasCredito = document.getElementById("tbodyCuotasCredito");
            if (!tbodyCuotasCredito) return;
            tbodyCuotasCredito.innerHTML = "";

            var inputNumCuotas = document.getElementById("num_cuotas");
            var selectFrecuenciaPago = document.getElementById("frecuencia_pago");
            var inputDiasGraciaCuota = document.getElementById("dias_gracia_cuota");
            var fechaVentaInput = document.getElementById("fecha_venta");

            var numCuotas = parseInt(inputNumCuotas ? inputNumCuotas.value : 1) || 1;
            var diasIntervalo = parseInt(selectFrecuenciaPago ? selectFrecuenciaPago.value : 30) || 30;
            var diasGracia = parseInt(inputDiasGraciaCuota ? inputDiasGraciaCuota.value : 0) || 0;
            var totalVentaVal = this.obtenerTotalCalculado();

            var lblContador = document.getElementById("lblCuotasContador");
            if (lblContador) lblContador.textContent = `0/${numCuotas}`;

            var montoBaseCuota = parseFloat((totalVentaVal / numCuotas).toFixed(2));
            var acumulado = 0;

            var fechaBaseStr = fechaVentaInput ? fechaVentaInput.value : '';
            var fechaInicio = fechaBaseStr ? new Date(fechaBaseStr + 'T00:00:00') : new Date();

            var self = this;

            for (var i = 1; i <= numCuotas; i++) {
                var montoCuota = montoBaseCuota;
                if (i === numCuotas) {
                    montoCuota = parseFloat((totalVentaVal - acumulado).toFixed(2));
                }
                acumulado += montoCuota;

                var fVenc = new Date(fechaInicio);
                fVenc.setDate(fVenc.getDate() + (i * diasIntervalo));
                var yyyy = fVenc.getFullYear();
                var mm = String(fVenc.getMonth() + 1).padStart(2, '0');
                var dd = String(fVenc.getDate()).padStart(2, '0');
                var fechaVencStr = `${yyyy}-${mm}-${dd}`;

                var fGracia = new Date(fVenc);
                fGracia.setDate(fGracia.getDate() + diasGracia);
                var yyyyG = fGracia.getFullYear();
                var mmG = String(fGracia.getMonth() + 1).padStart(2, '0');
                var ddG = String(fGracia.getDate()).padStart(2, '0');
                var fechaGraciaStr = `${ddG}/${mmG}/${yyyyG}`;

                var tr = document.createElement("tr");
                tr.className = "data-table__row";
                tr.innerHTML = `
                    <td class="data-table__cell text-center" style="font-weight: 700; color: var(--color-primary);">Cuota ${i}</td>
                    <td class="data-table__cell">
                        <input type="date" class="form-input form-input-sm fecha-cuota-input" value="${fechaVencStr}" style="padding: 4px 8px; font-weight: 600;">
                    </td>
                    <td class="data-table__cell text-end">
                        <input type="number" step="0.01" class="form-input form-input-sm monto-cuota-input text-end" value="${montoCuota.toFixed(2)}" style="width: 120px; font-weight: 800; color: #00e676;">
                    </td>
                    <td class="data-table__cell text-center celda-dias-gracia" style="font-size: 0.88rem;">
                        +${diasGracia} días
                    </td>
                    <td class="data-table__cell text-center celda-fecha-gracia" style="font-size: 0.88rem; font-weight: 700; color: #ffb74d;">
                        ${fechaGraciaStr}
                    </td>
                `;
                tbodyCuotasCredito.appendChild(tr);
            }

            tbodyCuotasCredito.querySelectorAll('.monto-cuota-input').forEach(function (inp) {
                inp.addEventListener('input', function () { self.validarSumaCuotas(); });
            });

            tbodyCuotasCredito.querySelectorAll('.fecha-cuota-input').forEach(function (inp) {
                inp.addEventListener('change', function () { self.recalcularFechaGraciaFila(this); });
            });

            this.validarSumaCuotas();
        },

        recalcularFechaGraciaFila: function (inputFecha) {
            var row = inputFecha.closest("tr");
            if (!row) return;
            var inputDiasGraciaCuota = document.getElementById("dias_gracia_cuota");
            var diasGracia = parseInt(inputDiasGraciaCuota ? inputDiasGraciaCuota.value : 0) || 0;
            var val = inputFecha.value;
            if (val) {
                var fVenc = new Date(val + 'T00:00:00');
                fVenc.setDate(fVenc.getDate() + diasGracia);
                var yyyyG = fVenc.getFullYear();
                var mmG = String(fVenc.getMonth() + 1).padStart(2, '0');
                var ddG = String(fVenc.getDate()).padStart(2, '0');

                var celdaDias = row.querySelector(".celda-dias-gracia");
                if (celdaDias) celdaDias.textContent = `+${diasGracia} días`;

                var celdaGracia = row.querySelector(".celda-fecha-gracia");
                if (celdaGracia) celdaGracia.textContent = `${ddG}/${mmG}/${yyyyG}`;
            }
        },

        validarSumaCuotas: function () {
            var suma = 0;
            document.querySelectorAll(".monto-cuota-input").forEach(function (inp) {
                suma += parseFloat(inp.value) || 0;
            });

            var totalVentaVal = this.obtenerTotalCalculado();
            var dif = Math.abs(suma - totalVentaVal);
            var resumenCuotasValidacion = document.getElementById("resumenCuotasValidacion");

            if (resumenCuotasValidacion) {
                if (dif < 0.05) {
                    resumenCuotasValidacion.style.color = "#00e676";
                    resumenCuotasValidacion.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> Suma de cuotas coincide con el Total: C$ ${suma.toFixed(2)}`;
                } else {
                    resumenCuotasValidacion.style.color = "#ff5252";
                    resumenCuotasValidacion.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-1"></i> Suma de cuotas (C$ ${suma.toFixed(2)}) no coincide con Total (C$ ${totalVentaVal.toFixed(2)})`;
                }
            }
        },

        obtenerTotalCalculado: function () {
            var subtotal = 0;
            this.detalleVenta.forEach(function (p) { subtotal += p.subtotal; });
            var ivaRate = window.empresaIVA !== undefined ? window.empresaIVA / 100 : 0.15;
            return subtotal + (subtotal * ivaRate);
        },

        /**
         * Envío y confirmación final del formulario de venta
         */
        initFormVentaSubmit: function () {
            var self = this;
            var btnLimpiarVenta = document.getElementById("btnLimpiarVenta");
            var btnGuardar = document.getElementById("btnGuardar");
            var btnConfirmarGuardar = document.getElementById("btnConfirmarGuardar");

            var formVentaElem = document.getElementById("formVenta");
            var inputClienteNombre = document.getElementById("cliente_nombre");
            var inputClienteId = document.getElementById("cliente_id");
            var inputFechaVenta = document.getElementById("fecha_venta");
            var tipoVentaSelect = document.getElementById("tipo_venta");

            if (btnLimpiarVenta) {
                btnLimpiarVenta.addEventListener("click", function () {
                    window.ERP.Validators.clearError(inputClienteNombre);
                    window.ERP.Validators.clearError(inputFechaVenta);
                    self.detalleVenta = [];
                    if (formVentaElem) formVentaElem.reset();
                    self.irAPaso(1);
                    self.renderizarTabla();
                });
            }

            if (btnGuardar) {
                btnGuardar.addEventListener("click", function () {
                    window.ERP.Validators.clearError(inputClienteNombre);
                    window.ERP.Validators.clearError(inputFechaVenta);

                    var esValido = true;
                    var primerInvalido = null;

                    var clienteId = inputClienteId ? inputClienteId.value : '';
                    var clienteNombreVal = inputClienteNombre ? inputClienteNombre.value.trim() : '';
                    var tipoVenta = tipoVentaSelect ? tipoVentaSelect.value : 'CONTADO';
                    var fechaVenta = inputFechaVenta ? inputFechaVenta.value : '';

                    if (!clienteId || !clienteNombreVal) {
                        window.ERP.Validators.setError(inputClienteNombre, null, "Por favor seleccione un cliente de la lista.");
                        esValido = false;
                        if (!primerInvalido) primerInvalido = inputClienteNombre;
                    }

                    if (!fechaVenta) {
                        window.ERP.Validators.setError(inputFechaVenta, null, "La fecha de venta es obligatoria.");
                        esValido = false;
                        if (!primerInvalido) primerInvalido = inputFechaVenta;
                    }

                    if (!esValido) {
                        if (primerInvalido) primerInvalido.focus();
                        return false;
                    }

                    if (self.detalleVenta.length === 0) {
                        self.mostrarMensaje("warning", "Debe agregar al menos un producto a la factura");
                        self.irAPaso(1);
                        window.ERP.UI.openModal('modalProductos');
                        return false;
                    }

                    var numFacturaEl = document.getElementById("numero_factura");
                    var numFactura = numFacturaEl ? numFacturaEl.value : '';
                    var totalEl = document.getElementById("totalVenta");
                    var total = totalEl ? totalEl.textContent : '';

                    var rowConfirmCuotas = document.getElementById("rowConfirmCuotas");
                    var confirmCuotas = document.getElementById("confirmCuotas");

                    if (tipoVenta === "CREDITO") {
                        var suma = 0;
                        var numC = document.querySelectorAll(".monto-cuota-input").length;
                        document.querySelectorAll(".monto-cuota-input").forEach(function (inp) {
                            suma += parseFloat(inp.value) || 0;
                        });
                        var totalVentaVal = self.obtenerTotalCalculado();
                        if (Math.abs(suma - totalVentaVal) > 0.05) {
                            self.mostrarMensaje("danger", "La suma de las cuotas no coincide con el total de la venta");
                            return false;
                        }

                        if (rowConfirmCuotas) rowConfirmCuotas.style.display = "flex";
                        if (confirmCuotas) confirmCuotas.textContent = `${numC} cuota${numC > 1 ? 's' : ''}`;
                    } else {
                        if (rowConfirmCuotas) rowConfirmCuotas.style.display = "none";
                    }

                    var cC = document.getElementById("confirmCliente");
                    var cT = document.getElementById("confirmTipoVenta");
                    var cN = document.getElementById("confirmNumFactura");
                    var cTot = document.getElementById("confirmTotal");

                    if (cC) cC.textContent = clienteNombreVal;
                    if (cT) cT.textContent = tipoVenta;
                    if (cN) cN.textContent = numFactura;
                    if (cTot) cTot.textContent = total;

                    window.ERP.UI.openModal("modalConfirmarVenta");
                });
            }

            if (btnConfirmarGuardar) {
                btnConfirmarGuardar.addEventListener("click", function () {
                    self.guardarVentaFinal();
                });
            }
        },

        guardarVentaFinal: async function () {
            var btnConfirmarGuardar = document.getElementById("btnConfirmarGuardar");
            var inputClienteId = document.getElementById("cliente_id");
            var inputFechaVenta = document.getElementById("fecha_venta");
            var tipoVentaSelect = document.getElementById("tipo_venta");

            var clienteId = inputClienteId ? inputClienteId.value : '';
            var tipoVenta = tipoVentaSelect ? tipoVentaSelect.value : 'CONTADO';
            var fechaVenta = inputFechaVenta ? inputFechaVenta.value : '';

            var cuotasPayload = [];
            var fechaLimiteCreditoCalculada = null;

            if (tipoVenta === "CREDITO") {
                var filasCuotas = document.querySelectorAll("#tbodyCuotasCredito tr");
                var inputDiasGraciaCuota = document.getElementById("dias_gracia_cuota");
                var diasGracia = parseInt(inputDiasGraciaCuota ? inputDiasGraciaCuota.value : 0) || 0;

                filasCuotas.forEach(function (row, index) {
                    var inpFecha = row.querySelector(".fecha-cuota-input");
                    var inpMonto = row.querySelector(".monto-cuota-input");

                    if (inpFecha && inpMonto) {
                        var fVenc = inpFecha.value;
                        if (index === filasCuotas.length - 1) {
                            fechaLimiteCreditoCalculada = fVenc;
                        }
                        var fVencDate = new Date(fVenc + 'T00:00:00');
                        fVencDate.setDate(fVencDate.getDate() + diasGracia);
                        var yyyyG = fVencDate.getFullYear();
                        var mmG = String(fVencDate.getMonth() + 1).padStart(2, '0');
                        var ddG = String(fVencDate.getDate()).padStart(2, '0');
                        var fGracia = `${yyyyG}-${mmG}-${ddG}`;

                        cuotasPayload.push({
                            numero_cuota: index + 1,
                            fecha_vencimiento: fVenc,
                            fecha_vencimiento_gracia: fGracia,
                            monto_cuota: parseFloat(inpMonto.value) || 0,
                            dias_gracia: diasGracia
                        });
                    }
                });
            }

            if (btnConfirmarGuardar) {
                btnConfirmarGuardar.disabled = true;
                btnConfirmarGuardar.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Procesando...`;
            }

            var datos = {
                cliente_id: clienteId,
                tipo_venta: tipoVenta,
                fecha_venta: fechaVenta,
                fecha_limite_credito: fechaLimiteCreditoCalculada,
                observaciones: "",
                productos: this.detalleVenta,
                cuotas: cuotasPayload
            };

            try {
                var respuesta = await fetch("/guardar-venta", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(datos)
                });

                var resultado = await respuesta.json();

                if (!resultado.success) {
                    this.mostrarMensaje("danger", resultado.message);
                    if (btnConfirmarGuardar) {
                        btnConfirmarGuardar.disabled = false;
                        btnConfirmarGuardar.innerHTML = `<i class="bi bi-check-lg"></i> Confirmar y Guardar`;
                    }
                    return;
                }

                window.open(`/factura/${resultado.venta_id}`, "_blank");
                location.reload();

            } catch (error) {
                console.error(error);
                this.mostrarMensaje("danger", "Error al emitir la factura");
                if (btnConfirmarGuardar) {
                    btnConfirmarGuardar.disabled = false;
                    btnConfirmarGuardar.innerHTML = `<i class="bi bi-check-lg"></i> Confirmar y Guardar`;
                }
            }
        },

        init: function () {
            this.initStepper();
            this.initClienteDatalist();
            this.initBuscadorProductosModal();
            this.initCredito();
            this.initFormVentaSubmit();
            this.renderizarTabla();
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        window.ERP.Ventas.init();
    });

})(window, document);
