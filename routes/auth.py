# ==================================================
# IMPORTACIONES
# ==================================================

# Blueprint para modularizar rutas
from datetime import datetime, UTC
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, current_user
from database import db
from models.usuario import Usuario
from models.saas.super_usuario import SuperUsuario
from services.security_service import (
    ip_limiter,
    MAX_INTENTOS_LOGIN,
    MINUTOS_BLOQUEO_CUENTA
)

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
# RUTA LOGIN CON PROTECCIÓN FUERZA BRUTA
# ==================================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    # ==============================================
    # SI EL USUARIO YA ESTÁ LOGUEADO
    # ==============================================
    if current_user and current_user.is_authenticated:
        rol_nombre = current_user.rol.nombre.upper() if current_user.rol else ""
        if rol_nombre == "CLIENTE":
            return redirect(url_for("portal_cliente.portal"))
        return redirect(url_for("dashboard"))

    if session.get("superadmin_id"):
        return redirect(url_for("saas_admin.dashboard"))

    # ==============================================
    # MANEJO DE AVISO DE INACTIVIDAD (GET)
    # ==============================================
    if request.method == "GET" and request.args.get("motivo") == "inactividad":
        flash("Tu sesión ha finalizado automáticamente por inactividad. Por favor, ingresa de nuevo.", "warning")

    # ==============================================
    # SI EL FORMULARIO FUE ENVIADO (POST)
    # ==============================================
    if request.method == "POST":

        # Dirección IP del cliente para Rate Limiting
        ip_cliente = request.remote_addr or request.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0].strip()

        # 1. VERIFICAR RATE LIMIT POR IP
        if ip_limiter.esta_bloqueada(ip_cliente):
            return render_template(
                "auth/login.html",
                error_login="Has alcanzado el límite de intentos permitidos desde tu red. Por favor, espera un minuto antes de reintentar."
            )

        # Registrar intento de IP
        ip_limiter.registrar_intento(ip_cliente)

        # OBTENER DATOS FORMULARIO
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        # ==========================================
        # BUSCAR USUARIO DEL NEGOCIO / TENANT
        # ==========================================
        usuario = Usuario.query.filter_by(
            username=username
        ).first()

        if usuario:
            # 2. VERIFICAR SI LA CUENTA ESTÁ BLOQUEADA TEMPORALMENTE
            if usuario.esta_bloqueado:
                minutos = usuario.minutos_restantes_bloqueo()
                return render_template(
                    "auth/login.html",
                    error_login=f"Tu cuenta ha sido bloqueada temporalmente por seguridad. Intenta nuevamente en {minutos} minuto{'s' if minutos > 1 else ''}."
                )

            # 3. VERIFICAR CONTRASEÑA
            if usuario.check_password(password):
                # Verificar si la cuenta fue desactivada por el administrador
                if not usuario.estado:
                    return render_template(
                        "auth/login.html",
                        error_login="Esta cuenta de usuario ha sido desactivada. Comunícate con el administrador."
                    )

                # ÉXITO: Limpiar fallos previos y desbloquear
                usuario.limpiar_intentos_fallidos()
                db.session.commit()
                ip_limiter.limpiar_ip(ip_cliente)

                # ==================================
                # CREAR SESIÓN Y MARCA DE TIEMPO
                # ==================================
                login_user(usuario)
                session["ultimo_acceso"] = datetime.now(UTC).timestamp()

                # ==================================
                # REDIRECCIONAR SEGÚN ROL
                # ==================================
                rol_nombre = usuario.rol.nombre.upper() if usuario.rol else ""

                if rol_nombre == "CLIENTE":
                    if usuario.debe_cambiar_password:
                        return redirect(url_for("portal_cliente.cambiar_password_cliente"))
                    return redirect(url_for("portal_cliente.portal"))

                return redirect(url_for("dashboard"))

            else:
                # CONTRASEÑA INCORRECTA: Registrar fallo
                fue_bloqueado = usuario.registrar_fallo_login(
                    max_intentos=MAX_INTENTOS_LOGIN,
                    bloqueo_minutos=MINUTOS_BLOQUEO_CUENTA
                )
                db.session.commit()

                if fue_bloqueado:
                    return render_template(
                        "auth/login.html",
                        error_login=f"Has alcanzado el límite de {MAX_INTENTOS_LOGIN} intentos consecutivos. Tu cuenta ha sido bloqueada temporalmente durante {MINUTOS_BLOQUEO_CUENTA} minutos por seguridad."
                    )

                intentos_restantes = MAX_INTENTOS_LOGIN - (usuario.intentos_fallidos or 0)
                if intentos_restantes <= 2:
                    return render_template(
                        "auth/login.html",
                        error_login=f"Usuario o contraseña incorrectos. Advertencia: Te quedan {intentos_restantes} intento{'s' if intentos_restantes > 1 else ''} antes de que tu cuenta sea bloqueada temporalmente."
                    )

                return render_template(
                    "auth/login.html",
                    error_login="Usuario o contraseña incorrectos"
                )

        # ==========================================
        # VALIDAR SI ES SUPER ADMINISTRADOR SAAS
        # ==========================================
        super_user = SuperUsuario.query.filter_by(username=username).first()
        if super_user and super_user.check_password(password) and super_user.is_active:
            ip_limiter.limpiar_ip(ip_cliente)
            session["superadmin_id"] = super_user.id
            session["superadmin_user"] = super_user.username
            session["superadmin_name"] = super_user.nombre_completo or super_user.username
            session["ultimo_acceso"] = datetime.now(UTC).timestamp()
            return redirect(url_for("saas_admin.dashboard"))

        # ==========================================
        # LOGIN INCORRECTO (USUARIO NO ENCONTRADO)
        # ==========================================
        return render_template(
            "auth/login.html",
            error_login="Usuario o contraseña incorrectos"
        )

    # ==============================================
    # MOSTRAR LOGIN (GET)
    # ==============================================
    return render_template(
        "auth/login.html"
    )


# ==================================================
# LOGOUT
# ==================================================

@auth_bp.route("/logout")
def logout():

    # Motivo de salida (por ejemplo 'inactividad')
    motivo = request.args.get("motivo")

    # ==============================================
    # CERRAR SESIÓN Y LIMPIAR
    # ==============================================
    logout_user()
    session.clear()

    if motivo == "inactividad":
        flash("Tu sesión ha sido cerrada por inactividad por tu seguridad.", "warning")

    # ==============================================
    # REDIRECCIONAR LOGIN
    # ==============================================
    return redirect(
        url_for("auth.login")
    )


# ==================================================
# PING DE SESIÓN (RENOVACIÓN POR INACTIVIDAD)
# ==================================================

@auth_bp.route("/ping-session", methods=["POST", "GET"])
def ping_session():
    """
    Endpoint ligero para renovar la sesión activa desde el frontend
    cuando el usuario interactúa o hace clic en 'Seguir conectado'.
    """
    if (current_user and current_user.is_authenticated) or session.get("superadmin_id"):
        session["ultimo_acceso"] = datetime.now(UTC).timestamp()
        return jsonify({
            "status": "active",
            "authenticated": True,
            "timestamp": session["ultimo_acceso"]
        })

    return jsonify({
        "status": "expired",
        "authenticated": False
    }), 401
