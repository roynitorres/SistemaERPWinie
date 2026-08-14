import re

def validar_telefono_nicaraguense(telefono):
    """
    Valida que un número de teléfono nicaragüense sea correcto.
    Debe tener exactamente 8 dígitos (pudiendo tener guiones/espacios) y comenzar con 5, 7 u 8.
    Retorna un tuple: (es_valido: bool, mensaje_error: str)
    """
    if not telefono:
        return False, "El teléfono es obligatorio."
        
    telefono_clean = str(telefono).replace("-", "").replace(" ", "").strip()
    if not telefono_clean.isdigit() or len(telefono_clean) != 8:
        return False, "El teléfono debe contener exactamente 8 números."
        
    if telefono_clean[0] not in ['5', '7', '8']:
        return False, "El celular es inválido (debe iniciar con 5, 7 u 8)."
        
    return True, ""


def validar_email(email):
    """
    Valida que una dirección de correo electrónico tenga un formato estructural válido.
    Retorna un tuple: (es_valido: bool, mensaje_error: str)
    """
    if not email:
        return False, "El correo electrónico es obligatorio."
        
    email_clean = str(email).strip().lower()
    patron_email = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    
    if not re.match(patron_email, email_clean):
        return False, "El formato del correo electrónico no es válido (ej. usuario@dominio.com)."
        
    return True, ""
