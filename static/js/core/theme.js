/**
 * theme.js - Manejo del Modo Claro / Oscuro (Light/Dark Theme)
 * Exclusivo para el Panel Administrativo.
 * Login y Portal del Cliente están blindados para permanecer siempre en modo Claro.
 */

(function() {
    // Si la página especifica tema fijo claro (Login o Portal del Cliente)
    const pathname = (window.location && window.location.pathname) ? window.location.pathname.toLowerCase() : '';
    const isFixedLightPage = document.documentElement.getAttribute('data-theme-fixed') === 'light' ||
                            pathname.startsWith('/login') ||
                            pathname.includes('/auth') ||
                            pathname.startsWith('/portal-cliente');

    if (isFixedLightPage) {
        document.documentElement.setAttribute('data-theme', 'light');
        return;
    }

    // 1. Obtener preferencia guardada para el dashboard
    const savedTheme = localStorage.getItem('theme');
    
    // 2. Aplicar el tema (Si no hay guardado, por defecto es 'light')
    if (savedTheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
    }
})();

// Función global para alternar el tema (se llamará desde el botón en el topbar administrativo)
function toggleTheme() {
    const pathname = (window.location && window.location.pathname) ? window.location.pathname.toLowerCase() : '';
    const isFixedLightPage = document.documentElement.getAttribute('data-theme-fixed') === 'light' ||
                            pathname.startsWith('/login') ||
                            pathname.includes('/auth') ||
                            pathname.startsWith('/portal-cliente');
    if (isFixedLightPage) return; // No permitir cambios de tema en login o portal cliente

    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    // Aplicar al HTML
    document.documentElement.setAttribute('data-theme', newTheme);
    
    // Guardar preferencia
    localStorage.setItem('theme', newTheme);
    
    // Actualizar icono del botón si existe
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        if (theme === 'light') {
            themeIcon.className = 'bi bi-moon-fill';
        } else {
            themeIcon.className = 'bi bi-sun-fill';
        }
    }
}

// Actualizar el icono al cargar la página si el DOM ya está listo
document.addEventListener('DOMContentLoaded', () => {
    const pathname = (window.location && window.location.pathname) ? window.location.pathname.toLowerCase() : '';
    const isFixedLightPage = document.documentElement.getAttribute('data-theme-fixed') === 'light' ||
                            pathname.startsWith('/login') ||
                            pathname.includes('/auth') ||
                            pathname.startsWith('/portal-cliente');
    if (isFixedLightPage) {
        document.documentElement.setAttribute('data-theme', 'light');
        return;
    }

    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    updateThemeIcon(currentTheme);
});
