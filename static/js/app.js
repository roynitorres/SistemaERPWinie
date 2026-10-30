document.addEventListener('input', function (e) {
    // Omitir inputs que tengan clase 'no-uppercase' o data-no-uppercase (como el buscador de navegación)
    if (e.target.id === 'topbarSearchInput') return;
    if (e.target.classList && e.target.classList.contains('no-uppercase')) return;
    if (e.target.dataset && e.target.dataset.noUppercase === 'true') return;

    // Verificar si el elemento es un input de texto o un textarea
    if (e.target.tagName.toLowerCase() === 'textarea' || 
       (e.target.tagName.toLowerCase() === 'input' && e.target.type === 'text')) {
        
        // Guardar la posición del cursor para evitar que salte al final
        let start = e.target.selectionStart;
        let end = e.target.selectionEnd;
        
        // Convertir a mayúsculas
        e.target.value = e.target.value.toUpperCase();
        
        // Restaurar la posición del cursor
        e.target.setSelectionRange(start, end);
    }
});
