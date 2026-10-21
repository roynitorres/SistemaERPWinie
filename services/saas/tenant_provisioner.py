import os
import re
import unicodedata
from datetime import date, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from database import db
from models.saas.tenant import Tenant
from models.saas.enums import EstadoTenant, PlanSaaS
from models.rol import Rol
from models.usuario import Usuario
from models.empresa import Empresa
from models.banco import Banco
from services.saas.tenant_engine import get_tenant_engine, get_tenant_db_path


RESERVED_SLUGS = {
    "admin", "superadmin", "master", "static", "api", "login",
    "logout", "dashboard", "root", "system", "app", "saas"
}

DEFAULT_BANCOS = [
    "BAC Credomatic",
    "Banco Lafise Bancentro",
    "Banpro Grupo Promerica",
    "BDF (Banco de Finanzas)",
    "Ficohsa"
]


def sanitize_slug(text: str) -> str:
    """
    Normaliza y limpia un texto para convertirlo en un subdominio válido.
    Ej: 'Comercial Royni, S.A.' -> 'comercial-royni'
    """
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def validar_datos_provisionamiento(
    nombre_comercial: str,
    slug: str,
    propietario_nombre: str,
    username_admin: str,
    password_temporal: str
) -> Optional[str]:
    """Valida los campos obligatorios y formato de slug. Retorna None si todo es válido."""
    if not nombre_comercial or not nombre_comercial.strip():
        return "El nombre comercial de la empresa es obligatorio."

    if not slug or not slug.strip():
        return "El subdominio (slug) es obligatorio."

    clean_s = slug.strip().lower()
    if clean_s in RESERVED_SLUGS:
        return f"El subdominio '{clean_s}' está reservado por el sistema."

    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", clean_s):
        return "El subdominio solo puede contener letras minúsculas, números y guiones sencillos."

    # Verificar si ya existe en master.db
    existente = Tenant.query.filter_by(slug=clean_s).first()
    if existente:
        return f"El subdominio '{clean_s}' ya está en uso por otra empresa."

    if not propietario_nombre or not propietario_nombre.strip():
        return "El nombre del propietario/administrador es obligatorio."

    if not username_admin or not username_admin.strip():
        return "El nombre de usuario administrador es obligatorio."

    if not password_temporal or len(password_temporal) < 6:
        return "La contraseña temporal debe tener al menos 6 caracteres."

    return None


def generar_mensaje_bienvenida(
    tenant: Tenant,
    username_admin: str,
    password_temporal: str,
    base_domain: str = "localhost:5000"
) -> str:
    """Genera la plantilla de mensaje formateada para enviar por WhatsApp."""
    subdominio_url = tenant.url_subdominio(base_domain)
    return (
        f"🚀 *¡Bienvenido a tu Sistema de Cobro!*\n\n"
        f"Hola *{tenant.propietario_nombre}*, el espacio de trabajo para tu negocio "
        f"*{tenant.nombre_comercial}* ha sido aprovisionado con éxito y se encuentra 100% activo.\n\n"
        f"🔗 *Enlace de acceso:* http://{subdominio_url}\n"
        f"👤 *Usuario:* {username_admin}\n"
        f"🔑 *Clave temporal:* {password_temporal}\n\n"
        f"*(Por seguridad, el sistema te solicitará cambiar tu clave la primera vez que ingreses).*\n\n"
        f"¡Muchos éxitos en la administración de tu negocio!"
    )


def aprovisionar_nuevo_tenant(
    nombre_comercial: str,
    slug: str,
    propietario_nombre: str,
    propietario_telefono: Optional[str] = None,
    propietario_email: Optional[str] = None,
    ruc: Optional[str] = None,
    username_admin: str = "admin",
    password_temporal: str = "Temporal2026!",
    plan: str = PlanSaaS.PRO.value,
    precio_mensual: float = 35.00,
    dias_vigencia: int = 30,
    notas: Optional[str] = None,
    base_domain: str = "localhost:5000"
) -> Dict[str, Any]:
    """
    Fábrica de Inquilinos (Tenant Factory):
    1. Valida reglas de negocio y unicidad.
    2. Crea físicamente la base de datos aislada `tenants/<slug>.db`.
    3. Clona todas las tablas del sistema de cobro.
    4. Siembra roles (ADMIN, CLIENTE, VENDEDOR), bancos, empresa y el usuario inicial.
    5. Registra el tenant en `master.db`.
    6. Retorna el resultado con el texto de bienvenida para WhatsApp.
    """
    clean_s = sanitize_slug(slug)
    error = validar_datos_provisionamiento(
        nombre_comercial, clean_s, propietario_nombre, username_admin, password_temporal
    )
    if error:
        return {"success": False, "error": error}

    db_path = get_tenant_db_path(clean_s)
    tenant_engine = get_tenant_engine(clean_s)

    try:
        # 1. Crear las tablas operativas en la nueva base de datos aislada
        tenant_tables = [
            table for table in db.metadata.sorted_tables
            if table.info.get("bind_key") != "master" and table.name not in ("tenants", "super_usuarios")
        ]
        db.metadata.create_all(bind=tenant_engine, tables=tenant_tables)

        # 2. Sembrar datos esenciales en la base del nuevo cliente
        with Session(tenant_engine) as session:
            # Roles estándar del sistema
            rol_admin = Rol(nombre="ADMIN", descripcion="Administrador del sistema", estado=True)
            rol_cliente = Rol(nombre="CLIENTE", descripcion="Portal de clientes", estado=True)
            rol_vendedor = Rol(nombre="VENDEDOR", descripcion="Vendedor de mostrador", estado=True)
            session.add_all([rol_admin, rol_cliente, rol_vendedor])
            session.flush()

            # Configuración de empresa
            empresa = Empresa(
                razon_social=nombre_comercial.strip(),
                ruc=ruc.strip() if ruc else None,
                serie_factura="F001",
                correlativo="00001",
                estado=True
            )
            session.add(empresa)

            # Bancos iniciales
            for b_nombre in DEFAULT_BANCOS:
                session.add(Banco(nombre=b_nombre, estado="ACTIVO"))

            # Usuario Administrador inicial
            nuevo_admin = Usuario(
                username=username_admin.strip(),
                nombre_completo=propietario_nombre.strip(),
                telefono=propietario_telefono.strip() if propietario_telefono else None,
                email=propietario_email.strip() if propietario_email else None,
                rol_id=rol_admin.id,
                estado=True,
                debe_cambiar_password=True,
                password_temporal_plana=password_temporal
            )
            nuevo_admin.set_password(password_temporal)
            session.add(nuevo_admin)
            session.commit()

        # 3. Registrar el inquilino en la base central master.db
        fecha_corte = date.today() + timedelta(days=dias_vigencia)
        tenant = Tenant(
            slug=clean_s,
            nombre_comercial=nombre_comercial.strip(),
            ruc=ruc.strip() if ruc else None,
            propietario_nombre=propietario_nombre.strip(),
            propietario_telefono=propietario_telefono.strip() if propietario_telefono else None,
            propietario_email=propietario_email.strip() if propietario_email else None,
            db_filename=f"tenants/{clean_s}.db",
            plan=plan,
            precio_mensual=precio_mensual,
            estado=EstadoTenant.ACTIVO.value,
            fecha_corte=fecha_corte,
            notas=notas
        )
        db.session.add(tenant)
        db.session.commit()

        # 4. Generar mensaje de bienvenida
        mensaje_wsp = generar_mensaje_bienvenida(tenant, username_admin, password_temporal, base_domain)

        return {
            "success": True,
            "tenant": tenant,
            "subdominio": clean_s,
            "url": tenant.url_subdominio(base_domain),
            "mensaje_whatsapp": mensaje_wsp
        }

    except Exception as e:
        db.session.rollback()
        # Si falló, limpiar el archivo creado para evitar basura
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass
        return {"success": False, "error": f"Fallo al aprovisionar empresa: {str(e)}"}
