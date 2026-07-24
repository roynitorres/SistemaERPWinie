document.addEventListener('input', function (e) {
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
