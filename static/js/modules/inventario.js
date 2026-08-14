/* ==========================================================================
   SISTEMA ERP WINIE — MÓDULO DE INVENTARIO (static/js/modules/inventario.js)
   Gestión desacoplada de Productos y Categorías: CRUD, autocompletado y filtros
   ========================================================================== */

(function (window, document) {
    'use strict';

    window.ERP = window.ERP || {};

    window.ERP.Inventario = {

        /**
         * Módulo de Productos (`productos.html`)
         */
        initProductos: function () {
            var formulario = document.getElementById("formProductos");
            if (!formulario) return;

            var formTitle = document.getElementById("formTitle");
            var productoId = document.getElementById("producto_id");
            var formCodigo = document.getElementById("form_codigo");
            var formNombre = document.getElementById("form_nombre");
            var formCategoria = document.getElementById("form_categoria");
            var formProveedor = document.getElementById("form_proveedor");
            var formPrecioCompra = document.getElementById("form_precio_compra");
            var formPrecioVenta = document.getElementById("form_precio_venta");
            var formFechaCompra = document.getElementById("form_fecha_compra");
            var formCantidad = document.getElementById("form_cantidad_comprada");
            var formMarca = document.getElementById("form_marca");
            var formEstadoProd = document.getElementById("form_estado");

            var btnLimpiar = document.getElementById("btnLimpiar");
            var btnIrForm = document.getElementById("btnIrForm");
            var buscarProducto = document.getElementById("buscarProducto");

            formulario.addEventListener("keydown", function (e) {
                if (e.key === "Enter" && e.target.tagName !== "TEXTAREA" && e.target.tagName !== "BUTTON") {
                    e.preventDefault();
                }
            });

            // Autocompletado por Código de Barras / SKU
            if (formCodigo) {
                formCodigo.addEventListener("blur", async function () {
                    var codigo = this.value.trim();
                    if (codigo && productoId && !productoId.value) {
                        try {
                            var response = await fetch(`/buscar/${codigo}`);
                            var data = await response.json();

                            if (data.encontrado) {
                                if (formNombre) formNombre.value = data.nombre;
                                if (formMarca) formMarca.value = data.marca;
                                if (formCategoria) formCategoria.value = data.categoria_id;
                                if (formProveedor) formProveedor.value = data.proveedor_id;
                                if (formPrecioCompra) formPrecioCompra.value = data.precio_compra;
                                if (formPrecioVenta) formPrecioVenta.value = data.precio_venta;

                                var btnGuardar = document.getElementById("btnGuardar");
                                if (btnGuardar) {
                                    var iconHtml = btnGuardar.innerHTML;
                                    btnGuardar.innerHTML = `<i class="bi bi-magic"></i> ¡Autocompletado!`;
                                    btnGuardar.classList.remove("btn--primary");
                                    btnGuardar.classList.add("btn--success");
                                    btnGuardar.style.backgroundColor = "var(--color-success)";
                                    btnGuardar.style.color = "white";

                                    setTimeout(function () {
                                        btnGuardar.innerHTML = iconHtml;
                                        btnGuardar.classList.remove("btn--success");
                                        btnGuardar.classList.add("btn--primary");
                                        btnGuardar.style.backgroundColor = "";
                                        btnGuardar.style.color = "";
                                    }, 2500);
                                }

                                if (formCantidad) formCantidad.focus();
                            }
                        } catch (error) {
                            console.error("Error autocompletando:", error);
                        }
                    }
                });
            }

            // Sync visual del Select Estado (Verde / Rojo)
            if (formEstadoProd) {
                window.ERP.UI.updateSelectEstado(formEstadoProd);
                formEstadoProd.addEventListener("change", function () {
                    window.ERP.UI.updateSelectEstado(this);
                });
            }

            // Limpieza de feedback en tiempo real al escribir
            [formCodigo, formFechaCompra, formNombre, formMarca, formCantidad, formCategoria, formProveedor, formPrecioCompra, formPrecioVenta].forEach(function (input) {
                if (input) {
                    input.addEventListener("input", function () { window.ERP.Validators.clearError(input); });
                    input.addEventListener("change", function () { window.ERP.Validators.clearError(input); });
                }
            });

            // Submit con Validación
            formulario.addEventListener("submit", function (e) {
                window.ERP.Validators.clearError(formCodigo);
                window.ERP.Validators.clearError(formFechaCompra);
                window.ERP.Validators.clearError(formNombre);
                window.ERP.Validators.clearError(formMarca);
                window.ERP.Validators.clearError(formCantidad);
                window.ERP.Validators.clearError(formCategoria);
                window.ERP.Validators.clearError(formProveedor);
                window.ERP.Validators.clearError(formPrecioCompra);
                window.ERP.Validators.clearError(formPrecioVenta);

                var esValido = true;
                var primerInvalido = null;

                if (!formCodigo.value.trim()) {
                    window.ERP.Validators.setError(formCodigo, null, "El código del producto es obligatorio.");
                    esValido = false; if (!primerInvalido) primerInvalido = formCodigo;
                }

                if (!formFechaCompra.value) {
                    window.ERP.Validators.setError(formFechaCompra, null, "La fecha de compra es obligatoria.");
                    esValido = false; if (!primerInvalido) primerInvalido = formFechaCompra;
                }

                if (!formNombre.value.trim()) {
                    window.ERP.Validators.setError(formNombre, null, "El nombre del producto es obligatorio.");
                    esValido = false; if (!primerInvalido) primerInvalido = formNombre;
                }

                if (!formMarca.value.trim()) {
                    window.ERP.Validators.setError(formMarca, null, "La marca es obligatoria.");
                    esValido = false; if (!primerInvalido) primerInvalido = formMarca;
                }

                var cantVal = parseInt(formCantidad.value);
                if (isNaN(cantVal) || cantVal <= 0) {
                    window.ERP.Validators.setError(formCantidad, null, "Ingrese una cantidad válida mayor a 0.");
                    esValido = false; if (!primerInvalido) primerInvalido = formCantidad;
                }

                if (!formCategoria.value) {
                    window.ERP.Validators.setError(formCategoria, null, "Seleccione una categoría.");
                    esValido = false; if (!primerInvalido) primerInvalido = formCategoria;
                }

                if (!formProveedor.value) {
                    window.ERP.Validators.setError(formProveedor, null, "Seleccione un proveedor.");
                    esValido = false; if (!primerInvalido) primerInvalido = formProveedor;
                }

                var costVal = parseFloat(formPrecioCompra.value);
                if (isNaN(costVal) || costVal <= 0) {
                    window.ERP.Validators.setError(formPrecioCompra, null, "Ingrese un precio costo mayor a 0.");
                    esValido = false; if (!primerInvalido) primerInvalido = formPrecioCompra;
                }

                var ventVal = parseFloat(formPrecioVenta.value);
                if (isNaN(ventVal) || ventVal <= 0) {
                    window.ERP.Validators.setError(formPrecioVenta, null, "Ingrese un precio venta mayor a 0.");
                    esValido = false; if (!primerInvalido) primerInvalido = formPrecioVenta;
                }

                if (!esValido) {
                    e.preventDefault();
                    if (primerInvalido) primerInvalido.focus();
                    return false;
                }
            });

            var resetForm = function () {
                formulario.reset();
                if (productoId) productoId.value = "";
                if (formCodigo) formCodigo.value = "";
                if (formEstadoProd) window.ERP.UI.updateSelectEstado(formEstadoProd);
                if (formTitle) formTitle.innerHTML = `<i class="bi bi-box-seam"></i> NUEVO PRODUCTO`;
                if (formNombre) formNombre.focus();
            };

            var cargarProducto = function (row) {
                if (productoId) productoId.value = row.dataset.id;
                if (formCodigo) formCodigo.value = row.dataset.codigo;
                if (formNombre) formNombre.value = row.dataset.nombre;
                if (formCategoria) formCategoria.value = row.dataset.categoria;
                if (formProveedor) formProveedor.value = row.dataset.proveedor;

                if (formPrecioCompra) formPrecioCompra.value = row.dataset.precioCompra;
                if (formPrecioVenta) formPrecioVenta.value = row.dataset.precioVenta;
                if (formFechaCompra) formFechaCompra.value = row.dataset.fechaCompra;
                if (formCantidad) formCantidad.value = row.dataset.cantidadComprada;
                if (formMarca) formMarca.value = row.dataset.marca;

                if (formEstadoProd && row.dataset.estado) {
                    formEstadoProd.value = row.dataset.estado;
                    window.ERP.UI.updateSelectEstado(formEstadoProd);
                }

                if (formTitle) formTitle.innerHTML = `<i class="bi bi-pencil-fill text-success me-1"></i> EDITAR PRODUCTO`;
                window.ERP.UI.openModal('modalFormProducto');
            };

            if (btnLimpiar) btnLimpiar.addEventListener("click", resetForm);
            if (btnIrForm) {
                btnIrForm.addEventListener("click", function () {
                    resetForm();
                    window.ERP.UI.openModal('modalFormProducto');
                });
            }

            document.querySelectorAll(".btn-editar-fila").forEach(function (btn) {
                btn.addEventListener("click", function (e) {
                    e.stopPropagation();
                    cargarProducto(this.closest("tr"));
                });
            });

            document.querySelectorAll("#tablaProductos tr").forEach(function (row) {
                row.addEventListener("dblclick", function () {
                    cargarProducto(this);
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
