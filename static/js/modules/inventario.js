/* ==========================================================================
   SISTEMA ERP WINIE — MÓDULO DE INVENTARIO (static/js/modules/inventario.js)
   Gestión desacoplada de Productos y Categorías: CRUD, autocompletado y filtros
   ========================================================================== */

(function (window, document) {
    'use strict';

    window.ERP = window.ERP || {};

    window.ERP.Inventario = {

        /**
         * Inicializa la lógica de Productos (Tabla de catálogo o Formulario de página dedicada)
         */
        initProductos: function () {
            this.initProductosTabla();
            this.initProductosForm();
        },

        /**
         * Inicializa la Tabla de Productos (`productos.html`)
         */
        initProductosTabla: function () {
            var tabla = document.getElementById("tablaProductos");
            if (!tabla) return;

            var buscarProducto = document.getElementById("buscarProducto");

            // Doble clic en fila para editar en página dedicada
            document.querySelectorAll("#tablaProductos tr").forEach(function (row) {
                row.addEventListener("dblclick", function () {
                    if (this.dataset.urlEditar) {
                        window.location.href = this.dataset.urlEditar;
                    }
                });
            });

            // Paginación y Filtrado del lado del cliente
            var currentPage = 1;
            var itemsPerPage = 10;
            var allRows = Array.from(document.querySelectorAll("#tablaProductos tr"));
            var filteredRows = [...allRows];
            var estadoFiltroActual = "TODOS";

            var renderControls = function (totalPages) {
                var controlsContainer = document.getElementById("paginationControls");
                if (!controlsContainer) return;
                controlsContainer.innerHTML = "";
                if (totalPages <= 1) return;

                var btnPrev = document.createElement("button");
                btnPrev.className = "btn-apex-outline btn--small";
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
                    btnPage.className = `btn--small ${currentPage === i ? 'btn-neon-primary' : 'btn-apex-outline'}`;
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
                btnNext.className = "btn-apex-outline btn--small";
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

                var totalPrecioCompra = 0;
                for (var i = startIndex; i < endIndex; i++) {
                    if (filteredRows[i]) {
                        filteredRows[i].style.display = "";
                        var pCompra = parseFloat(filteredRows[i].dataset.precioCompra) || 0;
                        totalPrecioCompra += pCompra;
                    }
                }

                var paginationText = totalItems > 0
                    ? `Mostrando ${startIndex + 1} a ${endIndex} de ${totalItems} registros`
                    : "Mostrando 0 a 0 de 0 registros";

                var paginationSummary = document.getElementById("paginationSummary");
                if (paginationSummary) {
                    paginationSummary.innerHTML = `${paginationText} | <strong style="margin-left: 10px; color: var(--color-primary-dark);">Total P. Costo de página: C$ ${totalPrecioCompra.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>`;
                }

                var badgeTotal = document.getElementById("badgeTotalItems");
                if (badgeTotal) {
                    badgeTotal.textContent = totalItems;
                }

                renderControls(totalPages);
            };

            var filterTable = function () {
                var query = buscarProducto ? buscarProducto.value.toLowerCase().trim() : "";

                filteredRows = allRows.filter(function (row) {
                    var codigo = row.dataset.codigo ? row.dataset.codigo.toLowerCase() : "";
                    var nombre = row.dataset.nombre ? row.dataset.nombre.toLowerCase() : "";
                    var marca = row.dataset.marca ? row.dataset.marca.toLowerCase() : "";
                    var estadoRow = row.dataset.estado;

                    var matchesSearch = query === "" || codigo.includes(query) || nombre.includes(query) || marca.includes(query);
                    var matchesEstado = estadoFiltroActual === "TODOS" || estadoRow === estadoFiltroActual;

                    return matchesSearch && matchesEstado;
                });

                currentPage = 1;
                renderTable();
            };

            document.querySelectorAll(".state-pill").forEach(function (pill) {
                pill.addEventListener("click", function () {
                    document.querySelectorAll(".state-pill").forEach(function (p) { p.classList.remove("state-pill--active"); });
                    this.classList.add("state-pill--active");
                    estadoFiltroActual = this.dataset.estado;
                    filterTable();
                });
            });

            if (buscarProducto) {
                buscarProducto.addEventListener("input", filterTable);
            }

            renderTable();
        },

        /**
         * Inicializa el Formulario de Producto en Página Dedicada (`form_producto.html`)
         */
        initProductosForm: function () {
            var formulario = document.getElementById("formProductos");
            if (!formulario) return;

            var formCodigo = document.getElementById("form_codigo");
            var formNombre = document.getElementById("form_nombre");
            var formMarca = document.getElementById("form_marca");
            var formCategoria = document.getElementById("form_categoria");
            var formProveedor = document.getElementById("form_proveedor");
            var formFechaCompra = document.getElementById("form_fecha_compra");
            var formCantidad = document.getElementById("form_cantidad_comprada");
            var formStockMin = document.getElementById("form_stock_minimo");
            var formPrecioCompra = document.getElementById("form_precio_compra");
            var formMargen = document.getElementById("form_margen");
            var formPrecioVenta = document.getElementById("form_precio_venta");
            var formEstadoProd = document.getElementById("form_estado");
            var productoId = document.getElementById("producto_id");

            formulario.addEventListener("keydown", function (e) {
                if (e.key === "Enter" && e.target.tagName !== "TEXTAREA" && e.target.tagName !== "BUTTON") {
                    e.preventDefault();
                }
            });

            // Autocompletado por Código de Barras / SKU al desenfocar
            if (formCodigo) {
                formCodigo.addEventListener("blur", async function () {
                    var codigo = this.value.trim();
                    if (codigo && productoId && !productoId.value) {
                        try {
                            var response = await fetch(`/buscar/${codigo}`);
                            var data = await response.json();

                            if (data.encontrado) {
                                if (formNombre && !formNombre.value) formNombre.value = data.nombre;
                                if (formMarca && !formMarca.value) formMarca.value = data.marca;
                                if (formCategoria && !formCategoria.value) formCategoria.value = data.categoria_id;
                                if (formProveedor && !formProveedor.value) formProveedor.value = data.proveedor_id;
                                if (formPrecioCompra && !formPrecioCompra.value) formPrecioCompra.value = parseFloat(data.precio_compra).toFixed(2);
                                if (formPrecioVenta && !formPrecioVenta.value) formPrecioVenta.value = parseFloat(data.precio_venta).toFixed(2);
                                if (formStockMin && data.stock_minimo) formStockMin.value = data.stock_minimo;

                                if (formCantidad) formCantidad.focus();
                            }
                        } catch (error) {
                            console.error("Error autocompletando:", error);
                        }
                    }
                });
            }

            // Sync visual del Select Estado (Verde / Rojo)
            if (formEstadoProd && window.ERP.UI) {
                window.ERP.UI.updateSelectEstado(formEstadoProd);
                formEstadoProd.addEventListener("change", function () {
                    window.ERP.UI.updateSelectEstado(this);
                });
            }

            // Limpieza de feedback de error en tiempo real al escribir
            var inputsAValidar = [
                formCodigo, formFechaCompra, formNombre, formMarca, 
                formCantidad, formStockMin, formCategoria, formProveedor, 
                formPrecioCompra, formPrecioVenta
            ];

            inputsAValidar.forEach(function (input) {
                if (input && window.ERP.Validators) {
                    input.addEventListener("input", function () { window.ERP.Validators.clearError(input); });
                    input.addEventListener("change", function () { window.ERP.Validators.clearError(input); });
                }
            });

            // Submit con Validación Estricta
            formulario.addEventListener("submit", function (e) {
                inputsAValidar.forEach(function (i) {
                    if (i && window.ERP.Validators) window.ERP.Validators.clearError(i);
                });

                var esValido = true;
                var primerInvalido = null;

                function marcarError(input, mensaje) {
                    if (!input) return;
                    if (window.ERP.Validators) {
                        window.ERP.Validators.setError(input, null, mensaje);
                    }
                    esValido = false;
                    if (!primerInvalido) primerInvalido = input;
                }

                if (!formCodigo || !formCodigo.value.trim()) {
                    marcarError(formCodigo, "El código del producto es obligatorio.");
                }

                if (!formFechaCompra || !formFechaCompra.value) {
                    marcarError(formFechaCompra, "La fecha de compra es obligatoria.");
                }

                if (!formNombre || !formNombre.value.trim() || formNombre.value.trim().length < 3) {
                    marcarError(formNombre, "El nombre del producto debe tener al menos 3 caracteres.");
                }

                if (!formMarca || !formMarca.value.trim()) {
                    marcarError(formMarca, "La marca es obligatoria.");
                }

                var cantVal = parseInt(formCantidad ? formCantidad.value : 0);
                if (isNaN(cantVal) || cantVal <= 0) {
                    marcarError(formCantidad, "Ingrese una cantidad válida mayor a 0.");
                }

                var stockMinVal = parseInt(formStockMin ? formStockMin.value : 0);
                if (isNaN(stockMinVal) || stockMinVal < 0) {
                    marcarError(formStockMin, "El stock mínimo no puede ser negativo.");
                }

                if (!formCategoria || !formCategoria.value) {
                    marcarError(formCategoria, "Seleccione una categoría.");
                }

                if (!formProveedor || !formProveedor.value) {
                    marcarError(formProveedor, "Seleccione un proveedor.");
                }

                var costVal = parseFloat(formPrecioCompra ? formPrecioCompra.value : 0);
                if (isNaN(costVal) || costVal <= 0) {
                    marcarError(formPrecioCompra, "Ingrese un precio costo mayor a 0.");
                }

                var ventVal = parseFloat(formPrecioVenta ? formPrecioVenta.value : 0);
                if (isNaN(ventVal) || ventVal <= 0) {
                    marcarError(formPrecioVenta, "Ingrese un precio venta mayor a 0.");
                }

                if (!esValido) {
                    e.preventDefault();
                    if (primerInvalido) primerInvalido.focus();
                    return false;
                }
            });
        },

        /**
         * Módulo de Categorías (`categorias.html`)
         */
        initCategorias: function () {
            var formulario = document.getElementById("formCategorias");
            if (!formulario) return;

            var formTitle = document.getElementById("formTitle");
            var categoriaId = document.getElementById("categoria_id");
            var formCodigo = document.getElementById("form_codigo");
            var formNombre = document.getElementById("form_nombre");
            var formDescripcion = document.getElementById("form_descripcion");
            var formEstado = document.getElementById("form_estado");

            var btnLimpiar = document.getElementById("btnLimpiar");
            var btnIrForm = document.getElementById("btnIrForm");
            var buscarCategoria = document.getElementById("buscarCategoria");

            formulario.addEventListener("keydown", function (e) {
                if (e.key === "Enter" && e.target.tagName !== "TEXTAREA" && e.target.tagName !== "BUTTON") {
                    e.preventDefault();
                }
            });

            if (formEstado) {
                window.ERP.UI.updateSelectEstado(formEstado);
                formEstado.addEventListener("change", function () {
                    window.ERP.UI.updateSelectEstado(this);
                });
            }

            // Limpieza de feedback en tiempo real
            if (formNombre) {
                formNombre.addEventListener("input", function () {
                    window.ERP.Validators.clearError(formNombre);
                });
            }

            // Validación al enviar el formulario
            formulario.addEventListener("submit", function (e) {
                window.ERP.Validators.clearError(formNombre);

                var esValido = true;
                var primerInvalido = null;

                if (!formNombre || !formNombre.value.trim()) {
                    window.ERP.Validators.setError(formNombre, null, "El nombre de la categoría es obligatorio.");
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formNombre;
                } else if (formNombre.value.trim().length < 3) {
                    window.ERP.Validators.setError(formNombre, null, "El nombre debe contener al menos 3 caracteres.");
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formNombre;
                }

                if (!esValido) {
                    e.preventDefault();
                    if (primerInvalido) primerInvalido.focus();
                    return false;
                }
            });

            var resetForm = function () {
                if (formNombre) window.ERP.Validators.clearError(formNombre);
                formulario.reset();
                if (categoriaId) categoriaId.value = "";
                if (formCodigo && window.siguienteCodigo) formCodigo.value = window.siguienteCodigo;
                if (formEstado) {
                    formEstado.value = "ACTIVO";
                    window.ERP.UI.updateSelectEstado(formEstado);
                }
                if (formTitle) formTitle.innerHTML = `<i class="bi bi-tag"></i> NUEVA CATEGORÍA`;
                if (formNombre) formNombre.focus();
            };

            var cargarCategoria = function (row) {
                if (formNombre) window.ERP.Validators.clearError(formNombre);
                if (categoriaId) categoriaId.value = row.dataset.id;
                if (formCodigo) formCodigo.value = row.dataset.codigo;
                if (formNombre) formNombre.value = row.dataset.nombre;
                if (formDescripcion) formDescripcion.value = row.dataset.descripcion;
                if (formEstado) {
                    formEstado.value = row.dataset.estado;
                    window.ERP.UI.updateSelectEstado(formEstado);
                }

                if (formTitle) formTitle.innerHTML = `<i class="bi bi-pencil"></i> EDITAR CATEGORÍA`;
                window.ERP.UI.openModal('modalFormCategoria');
            };

            if (btnLimpiar) btnLimpiar.addEventListener("click", resetForm);
            if (btnIrForm) {
                btnIrForm.addEventListener("click", function () {
                    resetForm();
                    window.ERP.UI.openModal('modalFormCategoria');
                });
            }

            document.querySelectorAll(".btn-editar-fila").forEach(function (btn) {
                btn.addEventListener("click", function (e) {
                    e.stopPropagation();
                    cargarCategoria(this.closest("tr"));
                });
            });

            document.querySelectorAll("#tablaCategorias tr").forEach(function (row) {
                row.addEventListener("dblclick", function () {
                    cargarCategoria(this);
                });
            });

            // Paginación y Filtro de Categorías
            var currentPage = 1;
            var itemsPerPage = 10;
            var allRows = Array.from(document.querySelectorAll("#tablaCategorias tr"));
            var filteredRows = [...allRows];
            var estadoFiltroActual = "TODOS";

            var renderControls = function (totalPages) {
                var controlsContainer = document.getElementById("paginationControls");
                if (!controlsContainer) return;
                controlsContainer.innerHTML = "";
                if (totalPages <= 1) return;

                var btnPrev = document.createElement("button");
                btnPrev.className = "btn-apex-outline btn--small";
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
                    btnPage.className = `btn--small ${currentPage === i ? 'btn-neon-primary' : 'btn-apex-outline'}`;
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
                btnNext.className = "btn-apex-outline btn--small";
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

                var summaryText = totalItems > 0
                    ? `Mostrando ${startIndex + 1} a ${endIndex} de ${totalItems} registros`
                    : "Mostrando 0 a 0 de 0 registros";

                var summaryEl = document.getElementById("paginationSummary");
                if (summaryEl) summaryEl.innerText = summaryText;

                var badgeTotal = document.getElementById("badgeTotalItems");
                if (badgeTotal) badgeTotal.textContent = totalItems;

                renderControls(totalPages);
            };

            var aplicarFiltros = function () {
                var query = buscarCategoria ? buscarCategoria.value.toLowerCase().trim() : "";

                filteredRows = allRows.filter(function (row) {
                    var codigo = row.dataset.codigo ? row.dataset.codigo.toLowerCase() : "";
                    var nombre = row.dataset.nombre ? row.dataset.nombre.toLowerCase() : "";
                    var descripcion = row.dataset.descripcion ? row.dataset.descripcion.toLowerCase() : "";
                    var estadoRow = row.dataset.estado;

                    var coincideTexto = query === "" || codigo.includes(query) || nombre.includes(query) || descripcion.includes(query);
                    var coincideEstado = estadoFiltroActual === "TODOS" || estadoRow === estadoFiltroActual;

                    return coincideTexto && coincideEstado;
                });

                currentPage = 1;
                renderTable();
            };

            document.querySelectorAll(".state-pill").forEach(function (pill) {
                pill.addEventListener("click", function () {
                    document.querySelectorAll(".state-pill").forEach(function (p) { p.classList.remove("state-pill--active"); });
                    this.classList.add("state-pill--active");
                    estadoFiltroActual = this.dataset.estado;
                    aplicarFiltros();
                });
            });

            if (buscarCategoria) {
                buscarCategoria.addEventListener("input", aplicarFiltros);
            }

            renderTable();
        },

        init: function () {
            this.initProductos();
            this.initCategorias();
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        window.ERP.Inventario.init();
    });

})(window, document);
