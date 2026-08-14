/* ==========================================================================
   SISTEMA ERP WINIE — MÓDULO DE EMPRESA (static/js/modules/empresa.js)
   Gestión desacoplada de la Información de la Empresa y perfil tributario
   ========================================================================== */

(function (window, document) {
    'use strict';

    window.ERP = window.ERP || {};

    window.ERP.Empresa = {
        init: function () {
            var formEmpresa = document.getElementById("formEmpresa");
            if (!formEmpresa) return;

            var btnEditarEmpresa = document.getElementById("btnEditarEmpresa");
            var btnGuardarEmpresa = document.getElementById("btnGuardarEmpresa");
            var formEstadoEmpresa = document.getElementById("form_estado");
            var formRazonSocial = document.getElementById("form_razon_social");
            var formRuc = document.getElementById("form_ruc");
            var btnConfirmarEdicionModal = document.getElementById("btnConfirmarEdicionModal");

            var tieneEmpresa = formEmpresa.dataset.tieneEmpresa === "true";

            if (formEstadoEmpresa) {
                window.ERP.UI.updateSelectEstado(formEstadoEmpresa);
                formEstadoEmpresa.addEventListener("change", function () {
                    window.ERP.UI.updateSelectEstado(this);
                });
            }

            var bloquearCamposEmpresa = function () {
                formEmpresa.querySelectorAll("input, select, textarea").forEach(function (campo) {
                    if (campo.type !== "file") {
                        campo.disabled = true;
                    }
                });
            };

            var habilitarCamposEmpresa = function () {
                formEmpresa.querySelectorAll("input, select, textarea").forEach(function (campo) {
                    campo.disabled = false;
                });
            };

            if (tieneEmpresa) {
                bloquearCamposEmpresa();
                if (btnGuardarEmpresa) {
                    btnGuardarEmpresa.disabled = true;
                    btnGuardarEmpresa.style.opacity = "0.5";
                    btnGuardarEmpresa.style.cursor = "not-allowed";
                }
                if (btnEditarEmpresa) {
                    btnEditarEmpresa.disabled = false;
                }
            } else {
                habilitarCamposEmpresa();
                if (btnEditarEmpresa) {
                    btnEditarEmpresa.disabled = true;
                    btnEditarEmpresa.style.opacity = "0.5";
                }
                if (btnGuardarEmpresa) {
                    btnGuardarEmpresa.disabled = false;
                    btnGuardarEmpresa.style.opacity = "1";
                }
            }

            if (btnEditarEmpresa) {
                btnEditarEmpresa.addEventListener("click", function (e) {
                    e.preventDefault();
                    window.ERP.UI.openModal('modalConfirmarEdicion');
                });
            }

            if (btnConfirmarEdicionModal) {
                btnConfirmarEdicionModal.addEventListener("click", function () {
                    window.ERP.UI.closeModal('modalConfirmarEdicion');
                    habilitarCamposEmpresa();
                    if (btnEditarEmpresa) {
                        btnEditarEmpresa.disabled = true;
                        btnEditarEmpresa.style.opacity = "0.5";
                        btnEditarEmpresa.innerHTML = '<i class="bi bi-unlock me-1"></i> Modo Edición Activo';
                    }
                    if (btnGuardarEmpresa) {
                        btnGuardarEmpresa.disabled = false;
                        btnGuardarEmpresa.style.opacity = "1";
                        btnGuardarEmpresa.style.cursor = "pointer";
                    }
                    if (formRazonSocial) formRazonSocial.focus();
                });
            }

            // Limpieza de alertas en tiempo real
            [formRazonSocial, formRuc].forEach(function (input) {
                if (input) {
                    input.addEventListener("input", function () { window.ERP.Validators.clearError(input); });
                    input.addEventListener("change", function () { window.ERP.Validators.clearError(input); });
                }
            });

            // Submit con Validación Apex Dark
            formEmpresa.addEventListener("submit", function (e) {
                window.ERP.Validators.clearError(formRazonSocial);
                window.ERP.Validators.clearError(formRuc);

                var esValido = true;
                var primerInvalido = null;

                if (!formRazonSocial || !formRazonSocial.value.trim()) {
                    window.ERP.Validators.setError(formRazonSocial, null, "La razón social o nombre comercial es obligatoria.");
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formRazonSocial;
                }

                if (!formRuc || !formRuc.value.trim()) {
                    window.ERP.Validators.setError(formRuc, null, "El RUC de la empresa es obligatorio.");
                    esValido = false;
                    if (!primerInvalido) primerInvalido = formRuc;
                }

                if (!esValido) {
                    e.preventDefault();
                    if (primerInvalido) primerInvalido.focus();
                    return false;
                }
            });
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        window.ERP.Empresa.init();
    });

})(window, document);
