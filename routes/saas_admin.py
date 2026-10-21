import os
from functools import wraps
from datetime import date, timedelta
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, jsonify, send_file, current_app
)
from sqlalchemy import func

from database import db
from models.saas.super_usuario import SuperUsuario
from models.saas.tenant import Tenant
from models.saas.enums import EstadoTenant, PlanSaaS
from services.saas.tenant_provisioner import aprovisionar_nuevo_tenant, sanitize_slug
from services.saas.tenant_engine import get_tenant_db_path, dispose_tenant_engine


saas_admin_bp = Blueprint(
    "saas_admin",
    __name__,
    url_prefix="/saas-master",
    template_folder="../templates"
)


def superadmin_required(f):
    """Decorador de seguridad para proteger rutas exclusivas del Super Administrador."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("superadmin_id"):
            return redirect(url_for("saas_admin.login"))
        return f(*args, **kwargs)
    return decorated_function


# ==================================================
# AUTENTICACIÓN SUPER ADMINISTRADOR
# ==================================================

@saas_admin_bp.route("/login", methods=["GET", "POST"])
def login():
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json

    if session.get("superadmin_id"):
        if is_ajax:
            return jsonify({"success": True, "redirect_url": url_for("saas_admin.dashboard")})
        return redirect(url_for("saas_admin.dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = SuperUsuario.query.filter_by(username=username).first()
        if admin and admin.check_password(password) and admin.is_active:
            session["superadmin_id"] = admin.id
            session["superadmin_user"] = admin.username
            session["superadmin_name"] = admin.nombre_completo or admin.username

            if is_ajax:
                return jsonify({"success": True, "redirect_url": url_for("saas_admin.dashboard")})

            return redirect(url_for("saas_admin.dashboard"))

        error = "Credenciales maestras inválidas o cuenta inactiva."
        if is_ajax:
            return jsonify({"success": False, "error": error}), 401

    return render_template("saas/superadmin_login.html", error=error)


@saas_admin_bp.route("/logout")
def logout():
    session.pop("superadmin_id", None)
    session.pop("superadmin_user", None)
    session.pop("superadmin_name", None)
    return redirect(url_for("saas_admin.login"))


# ==================================================
# DASHBOARD PRINCIPAL DEL SUPER ADMIN
# ==================================================

@saas_admin_bp.route("/dashboard")
@superadmin_required
def dashboard():
    hoy = date.today()
    proximos_7_dias = hoy + timedelta(days=7)

    # 1. Métricas KPI
    total_activas = Tenant.query.filter_by(estado=EstadoTenant.ACTIVO.value).count()
    total_suspendidas = Tenant.query.filter_by(estado=EstadoTenant.SUSPENDIDO.value).count()
    
    ingresos_raw = db.session.query(func.coalesce(func.sum(Tenant.precio_mensual), 0)).filter(
        Tenant.estado == EstadoTenant.ACTIVO.value
    ).scalar()
    ingresos_mensuales = float(ingresos_raw or 0.0)

    por_vencer = Tenant.query.filter(
        Tenant.estado == EstadoTenant.ACTIVO.value,
        Tenant.fecha_corte >= hoy,
        Tenant.fecha_corte <= proximos_7_dias
    ).count()

    kpis = {
        "activas": total_activas,
        "suspendidas": total_suspendidas,
        "ingresos": ingresos_mensuales,
        "por_vencer": por_vencer
    }

    # 2. Lista de Empresas (Tenants)
    tenants = Tenant.query.order_by(Tenant.created_at.desc()).all()

    # 3. Datos auxiliares para el modal
    planes = [p.value for p in PlanSaaS]
    base_domain = current_app.config.get("SAAS_BASE_DOMAIN", "localhost:5000")

    return render_template(
        "saas/superadmin_dashboard.html",
        kpis=kpis,
        tenants=tenants,
        planes=planes,
        base_domain=base_domain,
        superadmin_name=session.get("superadmin_name")
    )


# ==================================================
# ACCIONES AJAX: CREACIÓN, ESTADO Y BACKUP
# ==================================================

@saas_admin_bp.route("/crear-empresa", methods=["POST"])
@superadmin_required
def crear_empresa():
    data = request.form
    nombre_comercial = data.get("nombre_comercial", "").strip()
    slug = data.get("slug", "").strip()
    propietario_nombre = data.get("propietario_nombre", "").strip()
    propietario_telefono = data.get("propietario_telefono", "").strip()
    propietario_email = data.get("propietario_email", "").strip()
    ruc = data.get("ruc", "").strip()
    username_admin = data.get("username_admin", "admin").strip()
    password_temporal = data.get("password_temporal", "Admin2026!").strip()
    plan = data.get("plan", PlanSaaS.PRO.value)

    try:
        precio_mensual = float(data.get("precio_mensual", 35.00))
    except (ValueError, TypeError):
        precio_mensual = 35.00

    try:
        dias_vigencia = int(data.get("dias_vigencia", 30))
    except (ValueError, TypeError):
        dias_vigencia = 30

    notas = data.get("notas", "").strip()
    base_domain = current_app.config.get("SAAS_BASE_DOMAIN", "localhost:5000")

    resultado = aprovisionar_nuevo_tenant(
        nombre_comercial=nombre_comercial,
        slug=slug,
        propietario_nombre=propietario_nombre,
        propietario_telefono=propietario_telefono,
        propietario_email=propietario_email,
        ruc=ruc,
        username_admin=username_admin,
        password_temporal=password_temporal,
        plan=plan,
        precio_mensual=precio_mensual,
        dias_vigencia=dias_vigencia,
        notas=notas,
        base_domain=base_domain
    )

    if not resultado["success"]:
        return jsonify({"success": False, "error": resultado["error"]}), 400

    return jsonify({
        "success": True,
        "subdominio": resultado["subdominio"],
        "url": resultado["url"],
        "mensaje_whatsapp": resultado["mensaje_whatsapp"]
    })


@saas_admin_bp.route("/toggle-estado/<int:tenant_id>", methods=["POST"])
@superadmin_required
def toggle_estado(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    if tenant.estado == EstadoTenant.ACTIVO.value:
        tenant.estado = EstadoTenant.SUSPENDIDO.value
    else:
        tenant.estado = EstadoTenant.ACTIVO.value

    db.session.commit()
    return jsonify({
        "success": True,
        "nuevo_estado": tenant.estado,
        "esta_activo": tenant.esta_activo
    })


@saas_admin_bp.route("/descargar-backup/<int:tenant_id>")
@superadmin_required
def descargar_backup(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    db_path = get_tenant_db_path(tenant.slug)

    if not os.path.exists(db_path):
        flash(f"El archivo de base de datos para {tenant.nombre_comercial} no existe.", "error")
        return redirect(url_for("saas_admin.dashboard"))

    download_name = f"backup_{tenant.slug}_{date.today().strftime('%Y%m%d')}.db"
    return send_file(
        db_path,
        as_attachment=True,
        download_name=download_name,
        mimetype="application/x-sqlite3"
    )


@saas_admin_bp.route("/reset-password/<int:tenant_id>", methods=["POST"])
@superadmin_required
def reset_password(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    username = request.form.get("username", "admin").strip()
    nueva_password = request.form.get("password_temporal", "").strip()
    forzar_cambio = request.form.get("forzar_cambio") in ("true", "1", "on", True)

    if not nueva_password or len(nueva_password) < 6:
        return jsonify({"success": False, "error": "La contraseña debe tener al menos 6 caracteres."}), 400

    from services.saas.tenant_engine import get_tenant_engine
    from models.usuario import Usuario
    from sqlalchemy.orm import Session

    engine = get_tenant_engine(tenant.slug)
    with Session(engine) as sess:
        user = sess.query(Usuario).filter_by(username=username).first()
        if not user:
            # Si no existe por username, buscar el primer usuario
            user = sess.query(Usuario).first()

        if not user:
            return jsonify({
                "success": False,
                "error": f"No se encontró ningún usuario en la base de datos de {tenant.nombre_comercial}."
            }), 404

        user.set_password(nueva_password)
        if forzar_cambio:
            user.debe_cambiar_password = True
            user.password_temporal_plana = nueva_password
        else:
            user.debe_cambiar_password = False
            user.password_temporal_plana = None

        sess.commit()
        username_final = user.username

    base_domain = current_app.config.get("SAAS_BASE_DOMAIN", "localhost:5000")
    subdominio_url = tenant.url_subdominio(base_domain)

    mensaje_wsp = (
        f"🔐 *¡Acceso Restablecido!*\n\n"
        f"Hola *{tenant.propietario_nombre}*, hemos restablecido la contraseña de acceso a tu sistema "
        f"para *{tenant.nombre_comercial}*:\n\n"
        f"🔗 *Enlace de acceso:* http://{subdominio_url}\n"
        f"👤 *Usuario:* {username_final}\n"
        f"🔑 *Nueva Clave Temporal:* {nueva_password}\n\n"
        f"*(El sistema te solicitará definir tu nueva clave personal al iniciar sesión).*\n\n"
        f"Cualquier duda, estamos a tu orden."
    )

    return jsonify({
        "success": True,
        "mensaje_whatsapp": mensaje_wsp
    })
