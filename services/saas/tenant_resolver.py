from typing import Optional
from flask import request, g, render_template, current_app, session
from models.saas.tenant import Tenant
from models.saas.enums import EstadoTenant
from services.saas.tenant_engine import get_tenant_engine


def extract_subdomain_from_host(host: str) -> Optional[str]:
    """
    Extrae el subdominio limpio de la cabecera Host de la petición.
    Ejemplos:
      - 'royni.localhost:5000' -> 'royni'
      - 'royni.localhost' -> 'royni'
      - 'royni.micobro.com' -> 'royni'
      - 'localhost:5000' -> None
      - '127.0.0.1:5000' -> None
      - 'admin.localhost' -> 'admin'
    """
    clean_host = host.split(":")[0].strip().lower()

    # Si es IP o localhost simple, no hay subdominio
    if clean_host in ("localhost", "127.0.0.1"):
        return None

    # Caso en local: *.localhost
    if clean_host.endswith(".localhost"):
        subdomain = clean_host[:-10]
        return subdomain if subdomain else None

    # Caso en producción: *.dominio.com o *.uni.miperfilnica.com
    base_domain = current_app.config.get("SAAS_BASE_DOMAIN", "").strip().lower()
    if base_domain:
        if clean_host == base_domain:
            return None
        if clean_host.endswith(f".{base_domain}"):
            subdomain = clean_host[:-(len(base_domain) + 1)]
            return subdomain if subdomain else None
        return None

    # Fallback genérico solo si no se configuró SAAS_BASE_DOMAIN
    parts = clean_host.split(".")
    if len(parts) >= 2:
        return parts[0]

    return None


def resolve_tenant_middleware():
    """
    Middleware ejecutado en before_request para resolver el Tenant activo.
    Configura `g.current_tenant` y `g.tenant_engine` en cada petición.
    """
    # 1. Ignorar archivos estáticos para máximo rendimiento
    if request.path.startswith("/static"):
        return None

    subdomain = extract_subdomain_from_host(request.host)

    # Permitir override de prueba por parámetro o sesión si estamos en localhost simple
    if not subdomain:
        subdomain = request.args.get("tenant") or session.get("active_tenant_slug")

    # 2. Zona del Super Administrador
    if subdomain == "admin" or request.path.startswith("/saas-master"):
        g.is_superadmin_zone = True
        g.current_tenant = None
        g.tenant_engine = None
        if subdomain == "admin" and request.path in ("/", "/login"):
            from flask import redirect, url_for
            return redirect(url_for("saas_admin.login"))
        return None

    g.is_superadmin_zone = False

    # 3. Si no hay subdominio especificado en la petición
    if not subdomain:
        g.current_tenant = None
        g.tenant_engine = None
        return None

    # 4. Buscar el tenant en la base central master.db
    tenant = Tenant.query.filter_by(slug=subdomain).first()

    if not tenant:
        return render_template("saas/empresa_no_encontrada.html", slug=subdomain), 404

    # 5. Validar estado de la cuenta (Suspensión por falta de pago)
    if tenant.estado == EstadoTenant.SUSPENDIDO.value:
        return render_template("saas/cuenta_suspendida.html", tenant=tenant), 403

    # 6. Tenant Activo: Inyectar contexto y motor de base de datos
    g.current_tenant = tenant
    g.tenant_engine = get_tenant_engine(tenant.slug)
    session["active_tenant_slug"] = tenant.slug
    return None
