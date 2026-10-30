/* ==========================================================================
   SISTEMA ERP WINIE — BUSCADOR DE NAVEGACIÓN RÁPIDA (NAV SEARCH)
   static/js/core/nav_search.js
   Permite buscar y saltar rápidamente a cualquier vista o módulo del sistema
   ========================================================================== */

(function (window, document) {
    'use strict';

    function initNavSearch() {
        const input = document.getElementById('topbarSearchInput');
        const container = document.getElementById('topbarSearchContainer');
        const resultsDiv = document.getElementById('topbarSearchResults');
        const clearBtn = document.getElementById('topbarSearchClearBtn');
        const dataScript = document.getElementById('navSearchData');

        if (!input || !resultsDiv || !dataScript) return;

        let items = [];
        try {
            items = JSON.parse(dataScript.textContent || '[]');
        } catch (e) {
            console.error('Error al cargar datos del buscador de menú:', e);
            return;
        }

        let currentFiltered = [];
        let selectedIndex = -1;

        // Normaliza texto eliminando acentos y espacios
        function normalizeText(text) {
            return (text || '')
                .toLowerCase()
                .normalize('NFD')
                .replace(/[\u0300-\u036f]/g, '')
                .trim();
        }

        // Resalta coincidencias en el título
        function highlightMatch(text, query) {
            if (!query) return escapeHtml(text);
            const normText = normalizeText(text);
            const normQuery = normalizeText(query);
            const idx = normText.indexOf(normQuery);

            if (idx === -1) return escapeHtml(text);

            const before = text.substring(0, idx);
            const match = text.substring(idx, idx + query.length);
            const after = text.substring(idx + query.length);

            return `${escapeHtml(before)}<span class="topbar-search-match">${escapeHtml(match)}</span>${escapeHtml(after)}`;
        }

        function escapeHtml(str) {
            return (str || '')
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }

        // Muestra u oculta la caja de resultados
        function showResults() {
            resultsDiv.style.display = 'flex';
        }

        function hideResults() {
            resultsDiv.style.display = 'none';
            selectedIndex = -1;
        }

        // Actualiza el elemento seleccionado visualmente
        function updateSelection(newIndex) {
            const itemEls = resultsDiv.querySelectorAll('.topbar-search-item');
            if (!itemEls.length) return;

            itemEls.forEach((el, idx) => {
                if (idx === newIndex) {
                    el.classList.add('is-selected');
                    el.scrollIntoView({ block: 'nearest' });
                } else {
                    el.classList.remove('is-selected');
                }
            });
            selectedIndex = newIndex;
        }

        // Renderiza las opciones filtradas
        function render(query) {
            const q = normalizeText(query);

            if (!q) {
                // Si está vacío, mostrar todas las vistas disponibles
                currentFiltered = items;
            } else {
                currentFiltered = items.filter(item => {
                    const normTitle = normalizeText(item.title);
                    const normCat = normalizeText(item.category);
                    const normDesc = normalizeText(item.description);
                    const normKey = normalizeText(item.keywords);

                    return normTitle.includes(q) ||
                           normCat.includes(q) ||
                           normDesc.includes(q) ||
                           normKey.includes(q);
                });
            }

            resultsDiv.innerHTML = '';
            selectedIndex = -1;

            if (currentFiltered.length === 0) {
                resultsDiv.innerHTML = `
                    <div class="topbar-search-empty">
                        <i class="bi bi-search"></i>
                        <div>No se encontraron opciones para "<strong>${escapeHtml(query)}</strong>"</div>
                    </div>
                `;
                showResults();
                return;
            }

            // Agrupar o listar las opciones
            currentFiltered.forEach((item, index) => {
                const link = document.createElement('a');
                link.className = 'topbar-search-item';
                link.href = item.url;
                link.dataset.index = index;

                link.innerHTML = `
                    <div class="topbar-search-item-icon">
                        <i class="bi ${item.icon || 'bi-circle'}"></i>
                    </div>
                    <div class="topbar-search-item-content">
                        <span class="topbar-search-item-title">${highlightMatch(item.title, query)}</span>
                        <span class="topbar-search-item-desc">${escapeHtml(item.description || '')}</span>
                    </div>
                    <span class="topbar-search-item-badge">${escapeHtml(item.category || 'Módulo')}</span>
                `;

                link.addEventListener('mouseenter', () => {
                    updateSelection(index);
                });

                resultsDiv.appendChild(link);
            });

            showResults();
        }

        // Eventos en el input
        input.addEventListener('input', function () {
            const val = this.value;
            if (clearBtn) {
                clearBtn.style.display = val.length > 0 ? 'flex' : 'none';
            }
            render(val);
        });

        input.addEventListener('focus', function () {
            render(this.value);
        });

        // Navegación por teclado (Flechas, Enter, Esc)
        input.addEventListener('keydown', function (e) {
            if (resultsDiv.style.display === 'none') {
                if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                    showResults();
                    render(this.value);
                    return;
                }
            }

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (currentFiltered.length > 0) {
                    const next = selectedIndex < currentFiltered.length - 1 ? selectedIndex + 1 : 0;
                    updateSelection(next);
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (currentFiltered.length > 0) {
                    const prev = selectedIndex > 0 ? selectedIndex - 1 : currentFiltered.length - 1;
                    updateSelection(prev);
                }
            } else if (e.key === 'Enter') {
                e.preventDefault();
                let targetItem = null;
                if (selectedIndex >= 0 && selectedIndex < currentFiltered.length) {
                    targetItem = currentFiltered[selectedIndex];
                } else if (currentFiltered.length > 0) {
                    targetItem = currentFiltered[0]; // Selecciona el primero por defecto si presionó Enter
                }

                if (targetItem && targetItem.url) {
                    window.location.href = targetItem.url;
                }
            } else if (e.key === 'Escape') {
                hideResults();
                input.blur();
            }
        });

        // Botón de limpiar
        if (clearBtn) {
            clearBtn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                input.value = '';
                clearBtn.style.display = 'none';
                render('');
                input.focus();
            });
        }

        // Cerrar al hacer clic fuera del contenedor
        document.addEventListener('click', function (e) {
            if (container && !container.contains(e.target)) {
                hideResults();
            }
        });

        // Atajo global Ctrl+K o Cmd+K para enfocar el buscador
        document.addEventListener('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                input.focus();
                input.select();
                render(input.value);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNavSearch);
    } else {
        initNavSearch();
    }

})(window, document);
