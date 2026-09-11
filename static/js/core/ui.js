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
            this.initPremiumCombobox();
        },

        /**
         * Crea un Combobox Premium personalizado a partir de selects nativos
         * para permitir styling completo del hover (ya que Windows lo bloquea).
         */
        initPremiumCombobox: function() {
            var selects = document.querySelectorAll('select.form-input, select.toolbar-input');
            selects.forEach(function(select) {
                // Si ya fue inicializado, omitir
                if (select.nextElementSibling && select.nextElementSibling.classList.contains('premium-select-container')) return;
                
                // Ocultar el select original
                select.style.display = 'none';
                
                // Contenedor principal
                var container = document.createElement('div');
                container.className = 'premium-select-container';
                if (select.disabled) container.classList.add('premium-disabled');
                
                // Copiar anchos en línea si existen (para toolbar-inputs o estilos custom)
                if (select.style.width) container.style.width = select.style.width;
                if (select.style.maxWidth) container.style.maxWidth = select.style.maxWidth;
                if (select.style.minWidth) container.style.minWidth = select.style.minWidth;
                
                // Área seleccionada (el "input" visible)
                var selectedDiv = document.createElement('div');
                selectedDiv.className = 'premium-select-selected';
                if (select.disabled) {
                    container.classList.add('premium-disabled');
                }
                
                // Buscar la opción seleccionada actual
                var activeOption = select.options[select.selectedIndex];
                selectedDiv.innerHTML = activeOption ? activeOption.innerHTML : 'Seleccione...';
                
                // Contenedor de la lista desplegable
                var optionsContainer = document.createElement('div');
                optionsContainer.className = 'premium-select-items premium-select-hide';
                
                // Función para construir/reconstruir opciones
                function buildOptions() {
                    optionsContainer.innerHTML = '';
                    var currActive = select.options[select.selectedIndex];
                    selectedDiv.innerHTML = currActive ? currActive.innerHTML : 'Seleccione...';
                    
                    for (var i = 0; i < select.length; i++) {
                        var optionDiv = document.createElement('div');
                        optionDiv.className = 'premium-select-item';
                        optionDiv.innerHTML = select.options[i].innerHTML;
                        
                        if (i === select.selectedIndex) {
                            optionDiv.classList.add('same-as-selected');
                        }
                        
                        // Evento al seleccionar opción
                        optionDiv.addEventListener('click', function(e) {
                            var clickedText = this.innerHTML;
                            var originalSelect = optionsContainer.originalSelectRef;
                            var selDiv = optionsContainer.selectedDivRef;
                            
                            // Actualizar original
                            for (var j = 0; j < originalSelect.length; j++) {
                                if (originalSelect.options[j].innerHTML === clickedText) {
                                    originalSelect.selectedIndex = j;
                                    selDiv.innerHTML = clickedText;
                                    
                                    // Quitar la clase a hermanos
                                    var siblings = this.parentNode.querySelectorAll('.premium-select-item');
                                    siblings.forEach(s => s.classList.remove('same-as-selected'));
                                    this.classList.add('same-as-selected');
                                    
                                    // Disparar eventos change
                                    originalSelect.dispatchEvent(new Event('change', { bubbles: true }));
                                    break;
                                }
                            }
                            optionsContainer.classList.add('premium-select-hide');
                            selDiv.classList.remove('premium-select-arrow-active');
                        });
                        
                        optionsContainer.appendChild(optionDiv);
                    }
                }
                
                // Construcción inicial
                buildOptions();
                
                // Escuchar cambios en los hijos del <select> (por si se agregan opciones por AJAX)
                var observer = new MutationObserver(function() {
                    buildOptions();
                });
                observer.observe(select, { childList: true });
                
                // Guardar referencias para el click
                optionsContainer.originalSelectRef = select;
                optionsContainer.selectedDivRef = selectedDiv;
                
                // Agregar al DOM: El selected va en el form, el dropdown va al body!
                container.appendChild(selectedDiv);
                select.parentNode.insertBefore(container, select.nextSibling);
                document.body.appendChild(optionsContainer);
                
                // Abrir/Cerrar
                selectedDiv.addEventListener('click', function(e) {
                    e.stopPropagation();
                    if (container.classList.contains('premium-disabled')) return;
                    
                    // Cerrar todos los demás primero
                    closeAllPremiumSelects(this);
                    
                    var isHidden = optionsContainer.classList.contains('premium-select-hide');
                    if (isHidden) {
                        // Mostrar temporalmente para medir su altura real
                        optionsContainer.style.top = '-9999px';
                        optionsContainer.style.maxHeight = 'none';
                        optionsContainer.classList.remove('premium-select-hide');
                        
                        var contentHeight = optionsContainer.offsetHeight;
                        var rect = this.getBoundingClientRect();
                        var spaceBelow = window.innerHeight - rect.bottom;
                        var spaceAbove = rect.top;
                        var maxH = 380; // Aumentado para mostrar más ítems (~10)
                        
                        // Si hay menos espacio abajo que la altura real y hay más espacio arriba, abrir hacia arriba
                        if (spaceBelow < Math.min(contentHeight, maxH) && spaceAbove > spaceBelow) {
                            var availableH = Math.min(spaceAbove - 15, maxH);
                            var finalHeight = Math.min(contentHeight, availableH);
                            optionsContainer.style.maxHeight = finalHeight + 'px';
                            optionsContainer.style.top = (rect.top + window.scrollY - finalHeight - 4) + 'px';
                        } else {
                            var availableH = Math.min(spaceBelow - 15, maxH);
                            var finalHeight = Math.min(contentHeight, availableH);
                            optionsContainer.style.maxHeight = finalHeight + 'px';
                            optionsContainer.style.top = (rect.bottom + window.scrollY + 4) + 'px';
                        }
                        
                        optionsContainer.style.left = (rect.left + window.scrollX) + 'px';
                        optionsContainer.style.width = rect.width + 'px';
                        optionsContainer.style.zIndex = "2147483647"; 
                        
                        this.classList.add('premium-select-arrow-active');
                    } else {
                        optionsContainer.classList.add('premium-select-hide');
                        this.classList.remove('premium-select-arrow-active');
                    }
                });
            });
            
            function closeAllPremiumSelects(elmnt) {
                var items = document.getElementsByClassName('premium-select-items');
                var selecteds = document.getElementsByClassName('premium-select-selected');
                
                for (var i = 0; i < selecteds.length; i++) {
                    if (elmnt !== selecteds[i]) {
                        selecteds[i].classList.remove('premium-select-arrow-active');
                    }
                }
                for (var i = 0; i < items.length; i++) {
                    if (items[i].selectedDivRef !== elmnt) {
                        items[i].classList.add('premium-select-hide');
                    }
                }
            }
            
            document.addEventListener('click', function(e) {
                if (e.target && e.target.closest && e.target.closest('.premium-select-items')) {
                    return;
                }
                closeAllPremiumSelects();
            });
            window.addEventListener('scroll', function(e) {
                if (e.target && e.target.classList && e.target.classList.contains('premium-select-items')) {
                    return;
                }
                closeAllPremiumSelects();
            }, true);
            window.addEventListener('resize', function() {
                closeAllPremiumSelects();
            });
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

    // Observer para re-inicializar el combobox premium si el DOM cambia dinámicamente
    // (Ej. al limpiar formularios o cargar datos asíncronos)
    document.addEventListener('change', function(e) {
        if (e.target.tagName === 'SELECT' && e.target.classList.contains('form-input')) {
            var container = e.target.nextElementSibling;
            if (container && container.classList.contains('premium-select-container')) {
                var selectedDiv = container.querySelector('.premium-select-selected');
                var activeOption = e.target.options[e.target.selectedIndex];
                if (selectedDiv && activeOption) {
                    selectedDiv.innerHTML = activeOption.innerHTML;
                    
                    // Marcar selected en la lista custom
                    var items = container.querySelectorAll('.premium-select-item');
                    items.forEach(function(item) {
                        if (item.innerHTML === activeOption.innerHTML) {
                            item.classList.add('same-as-selected');
                        } else {
                            item.classList.remove('same-as-selected');
                        }
                    });
                }
            }
        }
    });

})(window, document);
