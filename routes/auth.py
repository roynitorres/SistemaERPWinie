# ==================================================
# IMPORTACIONES
# ==================================================

# Blueprint para modularizar rutas
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user
from models.usuario import Usuario
# ==================================================
# CREACIÓN BLUEPRINT
# ==================================================

# Blueprint autenticación
auth_bp = Blueprint(

    # Nombre interno blueprint
    "auth",

    # Nombre archivo actual
    __name__,

    # Carpeta templates asociada
    template_folder="../templates"
)

# ==================================================
# RUTA LOGIN
# ==================================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    # ==============================================
    # SI EL FORMULARIO FUE ENVIADO
    # ==============================================

    if request.method == "POST":

        # ==========================================
        # OBTENER DATOS FORMULARIO
        # ==========================================

        username = request.form.get("username")

        password = request.form.get("password")

        # ==========================================
        # BUSCAR USUARIO
        # ==========================================

        usuario = Usuario.query.filter_by(
            username=username
        ).first()

        # ==========================================
        # VALIDAR USUARIO Y PASSWORD
        # ==========================================

        if usuario and usuario.check_password(password):
            rol_nombre = usuario.rol.nombre.upper() if usuario.rol else ""

            # ======================================
            # CREAR SESIÓN
            # ======================================

            login_user(usuario)

            # ======================================
            # REDIRECCIONAR
            # ======================================

            if rol_nombre == "CLIENTE":
                if usuario.debe_cambiar_password:
                    return redirect(url_for("portal_cliente.cambiar_password_cliente"))
            
                return redirect(url_for("portal_cliente.portal"))
            
            return redirect(url_for("dashboard"))

        # ==========================================
        # VALIDAR SI ES SUPER ADMINISTRADOR SAAS
        # ==========================================
        from models.saas.super_usuario import SuperUsuario
        super_user = SuperUsuario.query.filter_by(username=username).first()
        if super_user and super_user.check_password(password) and super_user.is_active:
            session["superadmin_id"] = super_user.id
            session["superadmin_user"] = super_user.username
            session["superadmin_name"] = super_user.nombre_completo or super_user.username
            return redirect(url_for("saas_admin.dashboard"))

        # ==========================================
        # LOGIN INCORRECTO
        # ==========================================
        
        return render_template(
            "auth/login.html",
            error_login="Usuario o contraseña incorrectos"
        )

    # ==============================================
    # MOSTRAR LOGIN
    # ==============================================

    return render_template(
        "auth/login.html"
    )


# ==================================================
# LOGOUT
# ==================================================

from flask_login import logout_user


@auth_bp.route("/logout")
def logout():

    # ==============================================
    # CERRAR SESIÓN
    # ==============================================

    logout_user()

    # ==============================================
    # REDIRECCIONAR LOGIN
    # ==============================================

    return redirect(
        url_for("auth.login")
    )