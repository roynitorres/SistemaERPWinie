/* ==========================================================================
   SISTEMA ERP WINIE — VALIDADOR CENTRALIZADO (static/js/core/validators.js)
   Validación con bordes rojos (.is-invalid-apex) y mensajes de retroalimentación
   ========================================================================== */

(function (window, document) {
    'use strict';

    window.ERP = window.ERP || {};

    window.ERP.Validators = {
        /**
         * Marca un campo de entrada con borde rojo y genera/muestra el mensaje de error
         */
        setError: function (inputEl, errorEl, message) {
            if (inputEl) {
                inputEl.classList.add('is-invalid-apex');
                var parent = inputEl.closest('.form-group') || inputEl.parentElement;
                if (parent && message) {
                    var feedback = parent.querySelector('.invalid-feedback-apex');
                    if (!feedback) {
                        feedback = document.createElement('div');
                        feedback.className = 'invalid-feedback-apex';
                        feedback.style.color = '#ff5252';
                        feedback.style.fontSize = '0.75rem';
                        feedback.style.marginTop = '4px';
                        parent.appendChild(feedback);
                    }
                    feedback.innerHTML = '<i class="bi bi-exclamation-circle-fill me-1"></i> ' + message;
                    feedback.style.display = 'block';
                }
            }
            if (errorEl) {
                if (message) {
                    errorEl.innerHTML = '<i class="bi bi-exclamation-circle-fill me-1"></i> ' + message;
                }
                errorEl.style.display = 'block';
            }
        },

        /**
         * Limpia el borde rojo y oculta el mensaje de error
         */
        clearError: function (inputEl, errorEl) {
            if (inputEl) {
                inputEl.classList.remove('is-invalid-apex');
                var parent = inputEl.closest('.form-group') || inputEl.parentElement;
                if (parent) {
                    var feedback = parent.querySelector('.invalid-feedback-apex');
                    if (feedback) feedback.style.display = 'none';
                }
            }
            if (errorEl) {
                errorEl.style.display = 'none';
            }
        },

        /**
         * Asigna limpieza dinámica de error al tipear en cualquier campo
         */
        bindAutoClear: function () {
            var self = this;
            document.querySelectorAll('input, select, textarea').forEach(function (input) {
                if (input.dataset.valClearInit) return;
                input.dataset.valClearInit = "true";

                var handler = function () {
                    if (input.value.trim().length > 0) {
                        self.clearError(input);
                        var errorId = input.dataset.errorId;
                        if (errorId) {
                            var errEl = document.getElementById(errorId);
                            if (errEl) self.clearError(null, errEl);
                        }
                    }
                };

                input.addEventListener('input', handler);
                input.addEventListener('change', handler);
            });
        },

        /**
         * Valida cambio de contraseña (actual, nueva >= 6 caracteres, confirmación)
         */
        validatePasswordForm: function (pActEl, pNueEl, pConEl, errActEl, errNueEl, errConEl) {
            var valido = true;

            [pActEl, pNueEl, pConEl].forEach(function (el) {
                if (el) el.classList.remove('is-invalid-apex');
            });
            [errActEl, errNueEl, errConEl].forEach(function (el) {
                if (el) el.style.display = 'none';
            });

            if (!pActEl || !pActEl.value.trim()) {
                this.setError(pActEl, errActEl, 'Por favor ingresa tu contraseña actual.');
                valido = false;
            }

            if (!pNueEl || !pNueEl.value.trim() || pNueEl.value.length < 6) {
                this.setError(pNueEl, errNueEl, 'Mínimo 6 caracteres requeridos.');
                valido = false;
            }

            if (!pConEl || !pConEl.value.trim() || (pNueEl && pNueEl.value !== pConEl.value)) {
                this.setError(pConEl, errConEl, 'Las contraseñas no coinciden o está vacía.');
                valido = false;
            }

            return valido;
        },

        init: function () {
            this.bindAutoClear();
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        window.ERP.Validators.init();
    });

})(window, document);
