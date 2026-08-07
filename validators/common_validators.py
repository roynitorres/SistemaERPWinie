def validar_telefono_nicaraguense(telefono):
    """
    Valida que un número de teléfono nicaragüense sea correcto.
    Debe tener exactamente 8 dígitos y comenzar con 5, 7 u 8.
    Retorna un tuple: (es_valido: bool, mensaje_error: str)
    """
    if not telefono:
        return False, "El teléfono es obligatorio."
        
    if not telefono.isdigit() or len(telefono) != 8:
        return False, "El teléfono debe contener exactamente 8 números."
        
    if telefono[0] not in ['5', '7', '8']:
        return False, "El celular es inválido (debe iniciar con 5, 7 u 8)."
        
    return True, ""
