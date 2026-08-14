/* ==========================================================================
   SISTEMA ERP WINIE — MÓDULO DE PROVEEDORES (static/js/modules/proveedores.js)
   Gestión desacoplada de Proveedores: CRUD, departamentos/municipios y filtros
   ========================================================================== */

(function (window, document) {
    'use strict';

    window.ERP = window.ERP || {};

    window.ERP.Proveedores = {
        departamentos_municipios: {
            "BOACO": ["BOACO", "CAMOAPA", "SAN JOSÉ DE LOS REMATES", "SAN LORENZO", "SANTA LUCÍA", "TEUSTEPE"],
            "CARAZO": ["DIRIAMBA", "DOLORES", "EL ROSARIO", "JINOTEPE", "LA CONQUISTA", "LA PAZ DE CARAZO", "SAN MARCOS", "SANTA TERESA"],
            "CHINANDEGA": ["CHICHIGALPA", "CHINANDEGA", "CINCO PINOS", "CORINTO", "EL REALEJO", "EL VIEJO", "POSOLTEGA", "PUERTO MORAZÁN", "SAN FRANCISCO DEL NORTE", "SAN PEDRO DEL NORTE", "SANTO TOMÁS DEL NORTE", "SOMOTILLO", "VILLANUEVA"],
            "CHONTALES": ["ACOYAPA", "COMALAPA", "EL CORAL", "JUIGALPA", "LA LIBERTAD", "MOYOGALPA", "SAN FRANCISCO DE CUAPA", "SAN PEDRO DE LÓVAGO", "SANTO DOMINGO", "SANTO TOMÁS", "VILLA SANDINO"],
            "ESTELÍ": ["CONDEGA", "ESTELÍ", "LA TRINIDAD", "PUEBLO NUEVO", "SAN JUAN DE LIMAY", "SAN NICOLÁS"],
            "GRANADA": ["DIRIÁ", "DIRIOMO", "GRANADA", "NANDAIME"],
            "JINOTEGA": ["EL CUÁ", "JINOTEGA", "LA CONCORDIA", "SAN JOSÉ DE BOCAY", "SAN RAFAEL DEL NORTE", "SAN SEBASTIÁN DE YALÍ", "SANTA MARÍA DE PANTASMA", "WIWILÍ DE JINOTEGA"],
            "LEÓN": ["ACHUAPA", "EL JICARAL", "EL SAUCE", "LA PAZ CENTRO", "LARREYNAGA", "LEÓN", "NAGAROTE", "QUEZALGUAQUE", "SANTA ROSA DEL PEÑÓN", "TELICA"],
            "MADRIZ": ["LAS SABANAS", "PALACAGÜINA", "SAN JOSÉ DE CUSMAPA", "SAN JUAN DE RÍO COCO", "SAN LUCAS", "SOMOTO", "TELPANECA", "TOTOGALPA", "YALAGÜINA"],
            "MANAGUA": ["CIUDAD SANDINO", "EL CRUCERO", "MANAGUA", "MATEARE", "SAN FRANCISCO LIBRE", "SAN RAFAEL DEL SUR", "TICUANTEPE", "TIPITAPA"],
            "MASAYA": ["CATARINA", "LA CONCEPCIÓN", "MASAYA", "MASATEPE", "NANDASMO", "NINDIRÍ", "NIQUINOMO", "SAN JUAN DE ORIENTE", "TISMA"],
            "MATAGALPA": ["CIUDAD DARÍO", "EL TUMA - LA DALIA", "ESQUIPULAS", "MATAGALPA", "MATIGUÁS", "MUY MUY", "RANCHO GRANDE", "RÍO BLANCO", "SAN DIONISIO", "SAN ISIDRO", "SAN RAMÓN", "SÉBACO", "TERRABONA"],
            "NUEVA SEGOVIA": ["CIUDAD ANTIGUA", "DIPILTO", "EL JÍCARO", "JALAPA", "MACUELIZO", "MOZONTE", "MURRA", "QUILALÍ", "SAN FERNANDO", "SANTA MARÍA", "TECOTECUMAN", "TOTOGALPA", "WANI", "OCOTAL"],
            "RÍO SAN JUAN": ["EL ALMENDRO", "EL CASTILLO", "MORRITO", "SAN CARLOS", "SAN JUAN DEL NORTE", "SAN MIGUELITO"],
            "RIVAS": ["ALTAGRACIA", "BELÉN", "BUENOS AIRES", "CÁRDENAS", "MOYOGALPA", "POTOSÍ", "RIVAS", "SAN JORGE", "SAN JUAN DEL SUR"],
            "COSTA CARIBE NORTE": ["BONANZA", "MULUKUKÚ", "PRINZAPOLKA", "PUERTO CABEZAS (BILWI)", "ROSITA", "SIUNA", "WASLALA", "WASPAM"],
            "COSTA CARIBE SUR": ["BLUEFIELDS", "CORN ISLAND", "DESEMBOCADURA DE LA CRUZ DE RÍO GRANDE", "EL TORTUGUERO", "EL RAMA", "KUKRA HILL", "LA DESEMBOCADURA DE RÍO MAÍZ", "LA CRUZ DE RÍO GRANDE", "LAGUNA DE PERLAS", "MUELLE DE LOS BUEYES", "NUEVA GUINEA", "PAIWAS", "SAN JUAN DE NICARAGUA"]
        },

        cargarMunicipios: function (departamento, municipioSeleccionado) {
            var formMunicipio = document.getElementById("form_municipio");
            if (!formMunicipio) return;

            if (window.ERP && window.ERP.Validators) {
                window.ERP.Validators.clearError(formMunicipio);
            }

            formMunicipio.innerHTML = '<option value="">Seleccione un municipio...</option>';
            if (departamento && this.departamentos_municipios[departamento]) {
                this.departamentos_municipios[departamento].forEach(function (m) {
                    var option = document.createElement("option");
                    option.value = m;
                    option.textContent = m;
                    if (m === municipioSeleccionado) {
                        option.selected = true;
                    }
                    formMunicipio.appendChild(option);
                });
            }
        },

        init: function () {
            var self = this;
            var form = document.getElementById("formProveedores");
            if (!form) return;

            var formTitle = document.getElementById("formTitle");
            var formCodigo = document.getElementById("form_codigo");
            var formNombreProveedor = document.getElementById("form_nombre_proveedor");
            var formNombreContacto = document.getElementById("form_nombre_contacto");
            var formTelefono = document.getElementById("form_telefono");
            var formDepartamento = document.getElementById("form_departamento");
            var formMunicipio = document.getElementById("form_municipio");
            var formRuc = document.getElementById("form_ruc");
            var formDireccion = document.getElementById("form_direccion");
            var formEstado = document.getElementById("form_estado");
            var proveedorIdInput = document.getElementById("proveedor_id");

            var btnLimpiar = document.getElementById("btnLimpiar");
            var btnIrForm = document.getElementById("btnIrForm");

            form.addEventListener("keydown", function (e) {
                if (e.key === "Enter" && e.target.tagName !== "TEXTAREA" && e.target.tagName !== 'BUTTON') {
                    e.preventDefault();
                }
            });

            if (formDepartamento) {
                formDepartamento.addEventListener("change", function () {
                    self.cargarMunicipios(this.value);
                });
            }

            if (formEstado) {
                window.ERP.UI.updateSelectEstado(formEstado);
                formEstado.addEventListener("change", function () {
                    window.ERP.UI.updateSelectEstado(this);
                });
            }

            [formNombreProveedor, formNombreContacto, formTelefono, formDepartamento, formMunicipio].forEach(function (input) {
                if (input) {
                    input.addEventListener("input", function () { window.ERP.Validators.clearError(input); });
                    input.addEventListener("change", function () { window.ERP.Validators.clearError(input); });
                }
            });

            form.addEventListener("submit", function (e) {
                window.ERP.Validators.clearError(formNombreProveedor);
                window.ERP.Validators.clearError(formNombreContacto);
                window.ERP.Validators.clearError(formTelefono);
                window.ERP.Validators.clearError(formDepartamento);
                window.ERP.Validators.clearError(formMunicipio);

                var esValido = true;
                var primerInvalido = null;

                var valNombreP = formNombreProveedor ? formNombreProveedor.value.trim() : "";
                if (!valNombreP) {
                    window.ERP.Validators.setError(formNombreProveedor, null, "El nombre del proveedor es obligatorio.");
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formNombreProveedor;
                } else if (valNombreP.length < 3) {
                    window.ERP.Validators.setError(formNombreProveedor, null, "Debe tener al menos 3 caracteres.");
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formNombreProveedor;
                }

                var valNombreC = formNombreContacto ? formNombreContacto.value.trim() : "";
                if (!valNombreC) {
                    window.ERP.Validators.setError(formNombreContacto, null, "El nombre del contacto es obligatorio.");
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formNombreContacto;
                }

                var valTel = formTelefono ? formTelefono.value.trim() : "";
                var regexTel = /^[578][0-9]{7}$/;
                if (!valTel) {
                    window.ERP.Validators.setError(formTelefono, null, "El número de teléfono es obligatorio.");
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formTelefono;
                } else if (!regexTel.test(valTel)) {
                    window.ERP.Validators.setError(formTelefono, null, "Debe tener 8 dígitos y comenzar con 5, 7 u 8.");
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formTelefono;
                }

                if (!formDepartamento || !formDepartamento.value) {
                    window.ERP.Validators.setError(formDepartamento, null, "Por favor seleccione un departamento.");
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formDepartamento;
                }

                if (!formMunicipio || !formMunicipio.value) {
                    window.ERP.Validators.setError(formMunicipio, null, "Por favor seleccione un municipio.");
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formMunicipio;
                }

                if (!esValido) {
                    e.preventDefault();
                    if (primerInvalido) primerInvalido.focus();
                    return false;
                }
            });

            var resetForm = function () {
                window.ERP.Validators.clearError(formNombreProveedor);
                window.ERP.Validators.clearError(formNombreContacto);
                window.ERP.Validators.clearError(formTelefono);
                window.ERP.Validators.clearError(formDepartamento);
                window.ERP.Validators.clearError(formMunicipio);

                form.reset();
                if (proveedorIdInput) proveedorIdInput.value = "";
                if (formCodigo && window.siguienteCodigo) formCodigo.value = window.siguienteCodigo;
                if (formEstado) window.ERP.UI.updateSelectEstado(formEstado);
                self.cargarMunicipios("");
                if (formTitle) formTitle.innerHTML = `<i class="bi bi-truck"></i> NUEVO PROVEEDOR`;
                if (formNombreProveedor) formNombreProveedor.focus();
            };

            var cargarProveedor = function (row) {
                window.ERP.Validators.clearError(formNombreProveedor);
                window.ERP.Validators.clearError(formNombreContacto);
                window.ERP.Validators.clearError(formTelefono);
                window.ERP.Validators.clearError(formDepartamento);
                window.ERP.Validators.clearError(formMunicipio);

                if (proveedorIdInput) proveedorIdInput.value = row.dataset.id;
                if (formCodigo) formCodigo.value = row.dataset.codigo;
                if (formNombreProveedor) formNombreProveedor.value = row.dataset.nombre_proveedor;
                if (formNombreContacto) formNombreContacto.value = row.dataset.nombre_contacto;
                if (formTelefono) formTelefono.value = row.dataset.telefono;

                var deptoData = (row.dataset.departamento || "").trim().toUpperCase();
                var deptoEncontrado = false;
                if (formDepartamento) {
                    for (var i = 0; i < formDepartamento.options.length; i++) {
                        if (formDepartamento.options[i].value.toUpperCase() === deptoData) {
                            formDepartamento.selectedIndex = i;
                            deptoEncontrado = true;
                            break;
                        }
                    }
                    if (!deptoEncontrado) formDepartamento.value = "";

                    var muniData = (row.dataset.municipio || "").trim().toUpperCase();
                    self.cargarMunicipios(formDepartamento.value);

                    if (formMunicipio) {
                        var muniEncontrado = false;
                        for (var j = 0; j < formMunicipio.options.length; j++) {
                            if (formMunicipio.options[j].value.toUpperCase() === muniData) {
                                formMunicipio.selectedIndex = j;
                                muniEncontrado = true;
                                break;
                            }
                        }
                        if (!muniEncontrado) formMunicipio.value = "";
                    }
                }

                if (formRuc) formRuc.value = row.dataset.ruc;
                if (formDireccion) formDireccion.value = row.dataset.direccion;
                if (formEstado && row.dataset.estado) {
                    formEstado.value = row.dataset.estado;
                    window.ERP.UI.updateSelectEstado(formEstado);
                }

                if (formTitle) formTitle.innerHTML = `<i class="bi bi-pencil"></i> EDITAR PROVEEDOR`;
                window.ERP.UI.openModal('modalFormProveedor');
            };

            if (btnLimpiar) btnLimpiar.addEventListener("click", resetForm);
            if (btnIrForm) {
                btnIrForm.addEventListener("click", function () {
                    resetForm();
                    window.ERP.UI.openModal('modalFormProveedor');
                });
            }

            document.querySelectorAll(".btn-editar-fila").forEach(function (btn) {
                btn.addEventListener("click", function (e) {
                    e.stopPropagation();
                    cargarProveedor(this.closest("tr"));
                });
            });

            document.querySelectorAll("#tablaProveedores tr").forEach(function (row) {
                row.addEventListener("dblclick", function () {
                    cargarProveedor(this);
                });
            });

            // Paginación y Filtrado
            var currentPage = 1;
            var itemsPerPage = 10;
            var allRows = Array.from(document.querySelectorAll("#tablaProveedores tr"));
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
                var buscarProveedor = document.getElementById("buscarProveedor");
                var query = buscarProveedor ? buscarProveedor.value.toLowerCase().trim() : "";

                filteredRows = allRows.filter(function (row) {
                    var codigo = row.dataset.codigo ? row.dataset.codigo.toLowerCase() : "";
                    var nombre_proveedor = row.dataset.nombre_proveedor ? row.dataset.nombre_proveedor.toLowerCase() : "";
                    var nombre_contacto = row.dataset.nombre_contacto ? row.dataset.nombre_contacto.toLowerCase() : "";
                    var telefono = row.dataset.telefono ? row.dataset.telefono.toLowerCase() : "";
                    var departamento = row.dataset.departamento ? row.dataset.departamento.toLowerCase() : "";
                    var municipio = row.dataset.municipio ? row.dataset.municipio.toLowerCase() : "";
                    var ruc = row.dataset.ruc ? row.dataset.ruc.toLowerCase() : "";
                    var estadoRow = row.dataset.estado;

                    var coincideTexto = query === "" ||
                        codigo.includes(query) ||
                        nombre_proveedor.includes(query) ||
                        nombre_contacto.includes(query) ||
                        telefono.includes(query) ||
                        departamento.includes(query) ||
                        municipio.includes(query) ||
                        ruc.includes(query);

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

            var buscarProveedorInput = document.getElementById("buscarProveedor");
            if (buscarProveedorInput) {
                buscarProveedorInput.addEventListener("input", aplicarFiltros);
            }

            renderTable();
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        window.ERP.Proveedores.init();
    });

})(window, document);
