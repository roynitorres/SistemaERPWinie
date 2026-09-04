/**
 * theme.js - Manejo del Modo Claro / Oscuro (Light/Dark Theme)
 * Se ejecuta en el <head> para evitar FOUC (Flash of Unstyled Content).
 */

(function() {
    // 1. Obtener preferencia guardada
    const savedTheme = localStorage.getItem('theme');
    
    // 2. Aplicar el tema (Si no hay guardado, por defecto es 'dark')
    if (savedTheme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
    } else {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
})();

// Función global para alternar el tema (se llamará desde el botón en el topbar)
function toggleTheme() {
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
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    updateThemeIcon(currentTheme);
});
