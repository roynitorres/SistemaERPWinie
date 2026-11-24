/* ==========================================================================
   SISTEMA ERP WINIE — MÓDULO DE VENTAS / POS (static/js/modules/ventas.js)
   Punto de Venta en Vista Única, Carrito Dinámico, Escáner y Facturación
   ========================================================================== */

(function (window, document) {
    'use strict';

    window.ERP = window.ERP || {};

    window.ERP.Ventas = {
        detalleVenta: [],
        categoriaSeleccionada: 'TODAS',
        searchDebounceTimer: null,
        productosMap: {},
        formaPagoSeleccionada: 'efectivo',

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
         * Inicialización del selector de clientes mediante Datalist
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
         * Buscador rápido por código de barras / texto con escaneo directo
         */
        initBuscadorRapido: function () {
            var self = this;
            var inputRapido = document.getElementById('buscarProductoRapido');
            if (!inputRapido) return;

            inputRapido.addEventListener('keydown', async function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    var val = this.value.trim();
                    if (!val) return;

                    try {
                        var url = '/buscar-productos?busqueda=' + encodeURIComponent(val) + '&categoria_id=TODAS';
                        var resp = await fetch(url);
                        var productos = await resp.json();

                        if (!productos || productos.length === 0) {
                            self.mostrarMensaje("warning", `No se encontró producto con: "${val}"`);
                            return;
                        }

                        // Coincidencia exacta o único resultado
                        var match = productos.find(function (p) {
                            return (p.codigo && p.codigo.toLowerCase() === val.toLowerCase());
                        }) || (productos.length === 1 ? productos[0] : null);

                        if (match) {
                            self.agregarOIncrementarProducto(match);
                            inputRapido.value = '';
                        } else {
                            // Múltiples coincidencias: abrir modal para selección visual
                            var buscarModal = document.getElementById('buscarProducto');
                            if (buscarModal) buscarModal.value = val;
                            window.ERP.UI.openModal('modalProductos');
                            self.buscarProductos(val);
                        }
                    } catch (err) {
                        console.error(err);
                        self.mostrarMensaje("danger", "Error al buscar el producto");
                    }
                }
            });
        },

        /**
         * Agregar producto al carrito o incrementar si ya existe
         */
        agregarOIncrementarProducto: function (producto) {
            if (producto.stock <= 0) {
                this.mostrarMensaje("danger", `El producto "${producto.nombre}" está agotado`);
                return;
            }

            var existeIndex = this.detalleVenta.findIndex(function (p) {
                return p.producto_id === producto.id;
            });

            if (existeIndex !== -1) {
                var item = this.detalleVenta[existeIndex];
                if (item.cantidad + 1 > producto.stock) {
                    this.mostrarMensaje("warning", `Stock máximo alcanzado (${producto.stock} unid.)`);
                    return;
                }
                item.cantidad++;
                this.recalcularItem(item);
                this.renderizarTabla();
                this.mostrarMensaje("success", `Cantidad incrementada: "${producto.nombre}" (${item.cantidad})`);
            } else {
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
                this.mostrarMensaje("success", `Se agregó "${producto.nombre}"`);
            }
        },

        /**
         * Búsqueda dinámica de productos en modal catálogo
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
                                <i class="bi bi-emoji-frown me-1"></i> No se encontraron productos
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
                                <div class="avatar-circle-apex" style="background: linear-gradient(135deg, #0047AB 0%, #00b0ff 100%); color: #ffffff;">
                                    <i class="bi bi-box-seam-fill"></i>
                                </div>
                                <div>
                                    <span class="customer-title-text">${producto.nombre}</span>
                                    <span class="customer-sub-text">${producto.marca || 'Sin marca'}</span>
                                </div>
                            </div>
                        </td>
                        <td class="data-table__cell" style="font-weight: 600; color: var(--color-text-main); font-family: monospace;">${producto.codigo}</td>
                        <td class="data-table__cell">${producto.categoria}</td>
                        <td class="data-table__cell text-end" style="font-weight: 700; color: var(--color-text-main);">C$ ${producto.precio.toFixed(2)}</td>
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
                        if (prod) {
                            self.agregarOIncrementarProducto(prod);
                            window.ERP.UI.closeModal('modalProductos');
                        }
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
                    if (row) row.style.backgroundColor = 'rgba(0, 71, 171, 0.08)';
                }
            });

            document.querySelectorAll('.producto-checkbox:not(:checked)').forEach(function (cb) {
                var row = cb.closest('tr');
                if (row) row.style.backgroundColor = '';
            });

            var selectedCountText = document.getElementById("selectedCountText");
            if (selectedCountText) {
                if (count > 0) {
                    selectedCountText.innerHTML = '<strong style="color: var(--color-text-main);">' + count + '</strong> seleccionado' + (count > 1 ? 's' : '') + ' | Total: <strong style="color: var(--color-primary);">C$ ' + totalEstimado.toFixed(2) + '</strong>';
                } else {
                    selectedCountText.textContent = "0 productos seleccionados";
                }
            }
        },

        agregarProductosSeleccionados: function () {
            var checkboxes = document.querySelectorAll('.producto-checkbox:checked');
            if (checkboxes.length === 0) {
                this.mostrarMensaje("warning", "Seleccione al menos un producto");
                return;
            }

            var agregados = 0;
            var erroresStock = 0;
            var self = this;

            checkboxes.forEach(function (cb) {
                var pId = cb.value;
                var producto = self.productosMap[pId];
                if (!producto) return;

                if (producto.stock <= 0) { erroresStock++; return; }

                var existe = self.detalleVenta.find(function (p) { return p.producto_id === producto.id; });
                if (existe) {
                    if (existe.cantidad + 1 <= producto.stock) {
                        existe.cantidad++;
                        self.recalcularItem(existe);
                        agregados++;
                    }
                    return;
                }

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
         * Renderizado de la tabla de items del carrito
         */
        renderizarTabla: function () {
            var tbody = document.getElementById("detalleVentaBody");
            if (!tbody) return;
            tbody.innerHTML = "";
            var subtotalGeneral = 0;
            var totalUnidades = 0;
            var self = this;

            if (this.detalleVenta.length === 0) {
                tbody.innerHTML = `
                    <tr class="data-table__row">
                        <td colspan="6" class="data-table__cell text-center" style="padding: 40px 16px; color: var(--color-text-muted);">
                            <i class="bi bi-cart-x d-block mb-2" style="font-size: 2.2rem; opacity: 0.5;"></i>
                            El carrito está vacío. Escanee un código de barras o use "Agregar Producto".
                        </td>
                    </tr>
                `;
                var lblContador = document.getElementById('lblTotalItemsCarrito');
                if (lblContador) lblContador.textContent = '0 productos';
                this.actualizarTotales(0);
                return;
            }

            this.detalleVenta.forEach(function (producto, index) {
                subtotalGeneral += producto.subtotal;
                totalUnidades += producto.cantidad;

                var tr = document.createElement('tr');
                tr.className = 'data-table__row';
                tr.innerHTML = `
                    <td class="data-table__cell" style="font-weight: 700; color: var(--color-text-muted); font-family: monospace;">${producto.codigo}</td>
                    <td class="data-table__cell" style="font-weight: 600; color: var(--color-text-main);">${producto.nombre}</td>
                    <td class="data-table__cell text-center">
                        <div class="pos-qty-stepper">
                            <button type="button" class="pos-qty-btn btn-disminuir" data-index="${index}" title="Disminuir"><i class="bi bi-dash"></i></button>
                            <input type="text" class="pos-qty-val input-cantidad" data-index="${index}" value="${producto.cantidad}" readonly>
                            <button type="button" class="pos-qty-btn btn-aumentar" data-index="${index}" title="Aumentar"><i class="bi bi-plus"></i></button>
                        </div>
                    </td>
                    <td class="data-table__cell text-end" style="color: var(--color-text-main);">C$ ${producto.precio.toFixed(2)}</td>
                    <td class="data-table__cell text-end" style="font-weight: 800; color: var(--color-primary);">C$ ${producto.subtotal.toFixed(2)}</td>
                    <td class="data-table__cell text-center">
                        <button type="button" class="btn-trash-item btn-eliminar-item" data-index="${index}" title="Quitar fila">
                            <i class="bi bi-trash3-fill"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });

            // Actualizar badge contador
            var lblContadorCarrito = document.getElementById('lblTotalItemsCarrito');
            if (lblContadorCarrito) {
                lblContadorCarrito.textContent = `${this.detalleVenta.length} producto${this.detalleVenta.length > 1 ? 's' : ''} (${totalUnidades} unid.)`;
            }

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

            this.actualizarTotales(subtotalGeneral);
        },

        actualizarTotales: function (subtotal) {
            var ivaRate = window.empresaIVA !== undefined ? window.empresaIVA / 100 : 0.15;
            var iva = subtotal * ivaRate;
            var total = subtotal + iva;

            var stEl = document.getElementById("subtotalVenta");
            var ivaEl = document.getElementById("ivaVenta");
            var tEl = document.getElementById("totalVenta");

            if (stEl) stEl.textContent = "C$ " + subtotal.toFixed(2);
            if (ivaEl) ivaEl.textContent = "C$ " + iva.toFixed(2);
            if (tEl) tEl.textContent = "C$ " + total.toFixed(2);

            this.calcularCambio();

            var tipoVentaSelect = document.getElementById("tipo_venta");
            if (tipoVentaSelect && tipoVentaSelect.value === "CREDITO") {
                this.generarTablaCuotasSugeridas();
            }
        },

        recalcularItem: function (p) {
            p.subtotal = p.precio * p.cantidad;
        },

        aumentarCantidad: function (index) {
            var producto = this.detalleVenta[index];
            if (!producto) return;
            if (producto.cantidad + 1 > producto.stock) {
                this.mostrarMensaje("warning", `Stock máximo alcanzado (${producto.stock} unid.)`);
                return;
            }
            producto.cantidad++;
            this.recalcularItem(producto);
            this.renderizarTabla();
        },

        disminuirCantidad: function (index) {
            var producto = this.detalleVenta[index];
            if (!producto) return;
            if (producto.cantidad <= 1) {
                this.eliminarProducto(index);
                return;
            }
            producto.cantidad--;
            this.recalcularItem(producto);
            this.renderizarTabla();
        },

        eliminarProducto: function (index) {
            var prod = this.detalleVenta[index];
            this.detalleVenta.splice(index, 1);
            this.renderizarTabla();
            if (prod) this.mostrarMensaje("warning", `Se eliminó "${prod.nombre}" del carrito`);
        },

        /**
         * Inicialización de Forma de Pago y Calculadora de Vuelto
         */
        initFormaPagoYCalculadora: function () {
            var self = this;
            var payBtns = document.querySelectorAll('.pos-pay-btn');
            var cashBox = document.getElementById('posCashBox');
            var inputRecibido = document.getElementById('inputMontoRecibido');

            payBtns.forEach(function (btn) {
                btn.addEventListener('click', function () {
                    payBtns.forEach(function (b) { b.classList.remove('active'); });
                    this.classList.add('active');
                    self.formaPagoSeleccionada = this.dataset.metodo || 'efectivo';

                    if (self.formaPagoSeleccionada !== 'efectivo') {
                        if (cashBox) {
                            cashBox.style.opacity = '0.35';
                            cashBox.style.pointerEvents = 'none';
                        }
                        var total = self.obtenerTotalCalculado();
                        if (inputRecibido) {
                            inputRecibido.value = total > 0 ? total.toFixed(2) : '';
                            inputRecibido.classList.remove("pos-field-input--error");
                        }
                        var badge = document.getElementById('badgeCambio');
                        if (badge) badge.textContent = 'C$ 0.00';
                    } else {
                        if (cashBox) {
                            cashBox.style.opacity = '1';
                            cashBox.style.pointerEvents = 'auto';
                        }
                        self.calcularCambio();
                    }
                });
            });

            // Botones de billetes directos y exacto
            var btnPagoExacto = document.getElementById("btnPagoExacto");
            if (btnPagoExacto) {
                btnPagoExacto.addEventListener("click", function () {
                    var total = self.obtenerTotalCalculado();
                    if (inputRecibido) {
                        inputRecibido.value = total.toFixed(2);
                        inputRecibido.classList.remove("pos-field-input--error");
                    }
                    self.calcularCambio();
                });
            }

            document.querySelectorAll(".btn-quick-bill[data-billete]").forEach(function (btn) {
                btn.addEventListener("click", function () {
                    var valorBillete = parseFloat(this.dataset.billete) || 0;
                    if (inputRecibido) {
                        inputRecibido.value = valorBillete.toFixed(2);
                        inputRecibido.classList.remove("pos-field-input--error");
                    }
                    self.calcularCambio();
                });
            });

            if (inputRecibido) {
                inputRecibido.addEventListener('input', function () {
                    this.classList.remove("pos-field-input--error");
                    self.calcularCambio();
                });
                inputRecibido.addEventListener('keyup', function () {
                    self.calcularCambio();
                });
            }
        },

        calcularCambio: function () {
            if (this.formaPagoSeleccionada !== 'efectivo') return;

            var inputRecibido = document.getElementById('inputMontoRecibido');
            var badgeCambio = document.getElementById('badgeCambio');
            if (!inputRecibido || !badgeCambio) return;

            var recibido = parseFloat(inputRecibido.value.replace(/,/g, '')) || 0;
            var total = this.obtenerTotalCalculado();
            var cambio = Math.max(0, recibido - total);

            badgeCambio.textContent = 'C$ ' + cambio.toFixed(2);
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
                    if (panelCuotasCredito) panelCuotasCredito.style.display = "flex";
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
            if (lblContador) lblContador.textContent = `${numCuotas} cuotas`;

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

                var tr = document.createElement("tr");
                tr.style.borderBottom = "1px solid var(--color-border)";
                tr.innerHTML = `
                    <td style="padding: 3px 6px; font-weight: 700; color: var(--color-text-main);">#${i}</td>
                    <td style="padding: 3px 6px;">
                        <input type="date" class="pos-field-input fecha-cuota-input" value="${fechaVencStr}" style="height: 24px; padding: 0 4px; font-size: 0.7rem;">
                    </td>
                    <td style="padding: 3px 6px; text-align: right;">
                        <input type="number" step="0.01" class="pos-field-input monto-cuota-input" value="${montoCuota.toFixed(2)}" style="width: 75px; height: 24px; padding: 0 4px; font-weight: 800; text-align: right; font-size: 0.72rem;">
                    </td>
                `;
                tbodyCuotasCredito.appendChild(tr);
            }

            tbodyCuotasCredito.querySelectorAll('.monto-cuota-input').forEach(function (inp) {
                inp.addEventListener('input', function () { self.validarSumaCuotas(); });
            });

            this.validarSumaCuotas();
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
                    resumenCuotasValidacion.style.color = "var(--color-primary)";
                    resumenCuotasValidacion.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> Cuotas coinciden con el Total (C$ ${suma.toFixed(2)})`;
                } else {
                    resumenCuotasValidacion.style.color = "var(--color-danger, #ef4444)";
                    resumenCuotasValidacion.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-1"></i> Suma (C$ ${suma.toFixed(2)}) ≠ Total (C$ ${totalVentaVal.toFixed(2)})`;
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
                    var inputMontoRecibido = document.getElementById("inputMontoRecibido");
                    if (inputMontoRecibido) inputMontoRecibido.value = "";
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
                        var rapido = document.getElementById("buscarProductoRapido");
                        if (rapido) rapido.focus();
                        return false;
                    }

                    var numFacturaEl = document.getElementById("numero_factura");
                    var numFactura = numFacturaEl ? numFacturaEl.value : '';
                    var totalEl = document.getElementById("totalVenta");
                    var total = totalEl ? totalEl.textContent : '';
                    var totalVentaVal = self.obtenerTotalCalculado();

                    // VALIDACIÓN OBLIGATORIA: VENTA AL CONTADO
                    if (tipoVenta === "CONTADO") {
                        var inputRecibido = document.getElementById("inputMontoRecibido");
                        var rawRecibido = inputRecibido ? inputRecibido.value.trim() : '';

                        // 1. ¿Tiene algún valor ingresado por el usuario?
                        if (!rawRecibido) {
                            self.mostrarMensaje("warning", "Debe ingresar el monto recibido del cliente para procesar la factura.");
                            if (inputRecibido) {
                                inputRecibido.focus();
                                inputRecibido.classList.add("pos-field-input--error");
                            }
                            return false;
                        }

                        // 2. Si hay un valor, debe validarse que sea numérico válido y cubra el total
                        var montoRecibidoNum = parseFloat(rawRecibido.replace(/,/g, ''));

                        if (isNaN(montoRecibidoNum) || montoRecibidoNum <= 0) {
                            self.mostrarMensaje("warning", "El monto recibido debe ser un valor mayor a cero.");
                            if (inputRecibido) {
                                inputRecibido.focus();
                                inputRecibido.classList.add("pos-field-input--error");
                            }
                            return false;
                        }

                        if (montoRecibidoNum < totalVentaVal - 0.05) {
                            self.mostrarMensaje("danger", `El monto recibido (C$ ${montoRecibidoNum.toFixed(2)}) no cubre el total de la factura (C$ ${totalVentaVal.toFixed(2)}).`);
                            if (inputRecibido) {
                                inputRecibido.focus();
                                inputRecibido.classList.add("pos-field-input--error");
                            }
                            return false;
                        }

                        if (inputRecibido) {
                            inputRecibido.classList.remove("pos-field-input--error");
                        }
                    }

                    var rowConfirmCuotas = document.getElementById("rowConfirmCuotas");
                    var confirmCuotas = document.getElementById("confirmCuotas");

                    if (tipoVenta === "CREDITO") {
                        var suma = 0;
                        var numC = document.querySelectorAll(".monto-cuota-input").length;
                        document.querySelectorAll(".monto-cuota-input").forEach(function (inp) {
                            suma += parseFloat(inp.value) || 0;
                        });
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
                    var cMetodo = document.getElementById("confirmMetodoPago");
                    var rowConfirmRecibido = document.getElementById("rowConfirmRecibido");
                    var cRecibido = document.getElementById("confirmMontoRecibido");
                    var rowConfirmCambio = document.getElementById("rowConfirmCambio");
                    var cCambio = document.getElementById("confirmCambio");

                    var metodoTexto = self.formaPagoSeleccionada === 'efectivo' ? 'Efectivo' :
                                     (self.formaPagoSeleccionada === 'tarjeta' ? 'Tarjeta' : 'Transferencia');
                    if (cMetodo) cMetodo.textContent = metodoTexto;

                    if (tipoVenta === "CONTADO" && self.formaPagoSeleccionada === "efectivo") {
                        var inputRecibidoEl = document.getElementById("inputMontoRecibido");
                        var mRecibido = parseFloat(inputRecibidoEl ? inputRecibidoEl.value : 0) || 0;
                        var mCambio = Math.max(0, mRecibido - totalVentaVal);

                        if (rowConfirmRecibido) rowConfirmRecibido.style.display = "flex";
                        if (cRecibido) cRecibido.textContent = "C$ " + mRecibido.toFixed(2);
                        if (rowConfirmCambio) rowConfirmCambio.style.display = "flex";
                        if (cCambio) cCambio.textContent = "C$ " + mCambio.toFixed(2);
                    } else {
                        if (rowConfirmRecibido) rowConfirmRecibido.style.display = "none";
                        if (rowConfirmCambio) rowConfirmCambio.style.display = "none";
                    }

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

            var totalVentaVal = this.obtenerTotalCalculado();
            var inputRecibido = document.getElementById("inputMontoRecibido");
            var rawRecibido = inputRecibido ? inputRecibido.value.trim() : '';
            var montoRecibidoNum = parseFloat(rawRecibido.replace(/,/g, ''));

            if (tipoVenta === "CONTADO") {
                if (!rawRecibido || isNaN(montoRecibidoNum) || montoRecibidoNum < totalVentaVal - 0.05) {
                    this.mostrarMensaje("danger", "El monto recibido es obligatorio y debe cubrir el total de la venta.");
                    if (inputRecibido) {
                        inputRecibido.focus();
                        inputRecibido.classList.add("pos-field-input--error");
                    }
                    if (btnConfirmarGuardar) {
                        btnConfirmarGuardar.disabled = false;
                        btnConfirmarGuardar.innerHTML = `<i class="bi bi-printer-fill me-1"></i> Confirmar y Emitir`;
                    }
                    window.ERP.UI.closeModal("modalConfirmarVenta");
                    return false;
                }
            }

            var montoRecibidoVal = (tipoVenta === 'CONTADO') ? montoRecibidoNum : totalVentaVal;

            var datos = {
                cliente_id: clienteId,
                tipo_venta: tipoVenta,
                fecha_venta: fechaVenta,
                fecha_limite_credito: fechaLimiteCreditoCalculada,
                observaciones: "",
                productos: this.detalleVenta,
                cuotas: cuotasPayload,
                metodo_pago: this.formaPagoSeleccionada,
                monto_recibido: montoRecibidoVal
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
                        btnConfirmarGuardar.innerHTML = `<i class="bi bi-printer-fill me-1"></i> Confirmar y Emitir`;
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
                    btnConfirmarGuardar.innerHTML = `<i class="bi bi-printer-fill me-1"></i> Confirmar y Emitir`;
                }
            }
        },

        /**
         * Atajos de Teclado Globales (F2 para buscar, F9 para facturar)
         */
        initShortcuts: function () {
            var self = this;
            window.addEventListener('keydown', function (e) {
                if (e.key === 'F2') {
                    e.preventDefault();
                    var rapido = document.getElementById("buscarProductoRapido");
                    if (rapido) {
                        rapido.focus();
                        rapido.select();
                    }
                }
                if (e.key === 'F9') {
                    e.preventDefault();
                    var btnGuardar = document.getElementById("btnGuardar");
                    if (btnGuardar) btnGuardar.click();
                }
            });
        },

        init: function () {
            this.initClienteDatalist();
            this.initBuscadorRapido();
            this.initBuscadorProductosModal();
            this.initFormaPagoYCalculadora();
            this.initCredito();
            this.initFormVentaSubmit();
            this.initShortcuts();
            this.renderizarTabla();
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        window.ERP.Ventas.init();
    });

})(window, document);
