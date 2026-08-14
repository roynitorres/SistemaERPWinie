/* ==========================================================================
   SISTEMA ERP WINIE — NÚCLEO UI (static/js/core/ui.js)
   Manejo desacoplado de componentes interactivos: Contraseñas, Tabs, Selects de Estado y Modales
   ========================================================================== */

(function (window, document) {
    'use strict';

    window.ERP = window.ERP || {};

    window.ERP.UI = {
        /**
         * Abre un modal por ID (soporta modales custom .modal-overlay y Bootstrap 5)
         */
        openModal: function (id) {
            var modal = document.getElementById(id);
            if (!modal) return;

            if (modal.classList.contains('modal-overlay')) {
                modal.classList.add('is-open');
                modal.classList.add('active');
            } else if (window.bootstrap) {
                var bsModal = bootstrap.Modal.getInstance(modal) || new bootstrap.Modal(modal);
                bsModal.show();
            }
        },

        /**
         * Cierra un modal por ID
         */
        closeModal: function (id) {
            var modal = document.getElementById(id);
            if (!modal) return;

            if (modal.classList.contains('modal-overlay')) {
                modal.classList.remove('is-open');
                modal.classList.remove('active');
            } else if (window.bootstrap) {
                var bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            }
        },

        /**
         * Actualiza el atributo data-estado del select de estado para activar estilos CSS (Verde ACTIVO / Rojo INACTIVO)
         */
        updateSelectEstado: function (select) {
            if (select) {
                select.setAttribute('data-estado', select.value);
            }
        },

        /**
         * Inicializa escuchadores para actualizar automáticamente el color de los select.select-estado-apex
         */
        initSelectEstadoColoring: function () {
            var self = this;
            document.querySelectorAll('.select-estado-apex').forEach(function (select) {
                self.updateSelectEstado(select);
                if (!select.dataset.colorInit) {
                    select.dataset.colorInit = "true";
                    select.addEventListener('change', function () {
                        self.updateSelectEstado(this);
                    });
                }
            });
        },

        /**
         * Inicializa escuchadores globales para alternar visibilidad de contraseña (👁️)
         */
        initPasswordToggles: function () {
            document.querySelectorAll('[data-toggle-password]').forEach(function (btn) {
                if (btn.dataset.pwdInit) return;
                btn.dataset.pwdInit = "true";

                btn.addEventListener('click', function () {
                    var container = this.closest('.position-relative') || this.parentElement;
                    var input = container ? container.querySelector('input[type="password"], input[type="text"]') : null;
                    var icon = this.querySelector('i');

                    if (!input || !icon) return;

                    var esPassword = input.type === 'password';
                    input.type = esPassword ? 'text' : 'password';

                    if (esPassword) {
                        icon.classList.remove('bi-eye-fill');
                        icon.classList.add('bi-eye-slash-fill');
                        icon.style.color = '#ffb74d';
                    } else {
                        icon.classList.remove('bi-eye-slash-fill');
                        icon.classList.add('bi-eye-fill');
                        icon.style.color = 'var(--color-text-muted)';
                    }
                });
            });
        },

        /**
         * Conmutación de pestañas (Tabs) dinámicas
         */
        switchTab: function (tabBarId, targetPanelId, activeClass) {
            activeClass = activeClass || 'active';
            var tabBar = document.getElementById(tabBarId);
            if (!tabBar) return;

            var buttons = tabBar.querySelectorAll('button[data-tab-target]');
            buttons.forEach(function (btn) {
                var panelId = btn.dataset.tabTarget;
                var panel = document.getElementById(panelId);

                if (panelId === targetPanelId) {
                    btn.classList.add(activeClass);
                    if (panel) panel.classList.remove('d-none');
                } else {
                    btn.classList.remove(activeClass);
                    if (panel) panel.classList.add('d-none');
                }
            });
        },

        /**
         * Inicializador del sistema UI
         */
        init: function () {
            this.initPasswordToggles();
            this.initSelectEstadoColoring();
        }
    };

    // Exponer abrirModal y cerrarModal globales para compatibilidad
    window.abrirModal = function (id) {
        window.ERP.UI.openModal(id);
    };

    window.cerrarModal = function (id) {
        window.ERP.UI.closeModal(id);
    };

    document.addEventListener('DOMContentLoaded', function () {
        window.ERP.UI.init();
    });

})(window, document);
