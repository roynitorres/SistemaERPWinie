/* ==========================================================================
   SISTEMA ERP WINIE — MÓDULO DE AUTENTICACIÓN (static/js/modules/auth.js)
   Validación de inicio de sesión, campos vacíos y visibilidad de contraseñas
   ========================================================================== */

(function (window, document) {
    'use strict';

    window.ERP = window.ERP || {};

    window.ERP.Auth = {
        /**
         * Inicializa la validación del formulario de Login
         */
        initLoginForm: function () {
            var form = document.getElementById('formLogin');
            if (!form) return;

            form.addEventListener('submit', function (e) {
                var uInput = document.getElementById('loginUsername');
                var pInput = document.getElementById('loginPassword');
                var errU = document.getElementById('err-login-username');
                var errP = document.getElementById('err-login-password');

                var valido = true;

                if (uInput) uInput.classList.remove('is-invalid-apex');
                if (pInput) pInput.classList.remove('is-invalid-apex');
                if (errU) errU.style.display = 'none';
                if (errP) errP.style.display = 'none';

                if (!uInput || !uInput.value.trim()) {
                    window.ERP.Validators.setError(uInput, errU);
                    valido = false;
                }

                if (!pInput || !pInput.value.trim()) {
                    window.ERP.Validators.setError(pInput, errP);
                    valido = false;
                }

                if (!valido) {
                    e.preventDefault();
                    if (uInput && !uInput.value.trim()) {
                        uInput.focus();
                    } else if (pInput && !pInput.value.trim()) {
                        pInput.focus();
                    }
                    return false;
                }

                return true;
            });
        },

        /**
         * Manejador del modal/alerta de ayuda de contraseña
         */
        initHelpTrigger: function () {
            document.querySelectorAll('[data-auth-help]').forEach(function (btn) {
                btn.addEventListener('click', function (e) {
                    e.preventDefault();
                    alert('ℹ️ Recuperación de Contraseña:\n\nSi has olvidado tus credenciales de acceso, comunícate con el Administrador Principal de tu sistema o con Soporte Técnico para restablecer tu cuenta.');
                });
            });
        },

        init: function () {
            this.initLoginForm();
            this.initHelpTrigger();
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        window.ERP.Auth.init();
    });

})(window, document);
