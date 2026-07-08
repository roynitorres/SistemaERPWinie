from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def roles_required(*roles_permitidos):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))

            rol_actual = current_user.rol.nombre.upper() if current_user.rol else ""

            if rol_actual not in roles_permitidos:
                flash("No tiene permisos para acceder a esta opción", "danger")
                return redirect(url_for("dashboard"))

            return func(*args, **kwargs)

        return wrapper

    return decorator