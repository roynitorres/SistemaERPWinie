from datetime import datetime, date, UTC
from database import db
from models.saas.enums import EstadoTenant, PlanSaaS


class Tenant(db.Model):
    """
    Modelo de Inquilino / Empresa en la Base Central (master.db).
    Representa una empresa u organización suscrita al SaaS.
    """
    __bind_key__ = "master"
    __tablename__ = "tenants"

    id = db.Column(db.Integer, primary_key=True)

    # Identificador único de subdominio (ej: 'royni' -> royni.micobro.com)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # Datos comerciales
    nombre_comercial = db.Column(db.String(150), nullable=False)
    ruc = db.Column(db.String(30), nullable=True)

    # Datos del titular / administrador
    propietario_nombre = db.Column(db.String(150), nullable=False)
    propietario_telefono = db.Column(db.String(30), nullable=True)
    propietario_email = db.Column(db.String(120), nullable=True)

    # Ubicación física de su base de datos aislada (ej: 'tenants/royni.db')
    db_filename = db.Column(db.String(255), nullable=False)

    # Suscripción y cobro
    plan = db.Column(db.String(50), nullable=False, default=PlanSaaS.PRO.value)
    precio_mensual = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    estado = db.Column(db.String(30), nullable=False, default=EstadoTenant.ACTIVO.value)
    fecha_corte = db.Column(db.Date, nullable=False)

    # Notas internas del Super Admin
    notas = db.Column(db.Text, nullable=True)

    # Auditoría
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    @property
    def esta_activo(self) -> bool:
        return self.estado == EstadoTenant.ACTIVO.value

    @property
    def dias_restantes(self) -> int:
        if not self.fecha_corte:
            return 0
        return (self.fecha_corte - date.today()).days

    @property
    def esta_vencido(self) -> bool:
        return self.dias_restantes < 0

    def url_subdominio(self, base_domain: str = "localhost:5000") -> str:
        return f"{self.slug}.{base_domain}"

    def __repr__(self) -> str:
        return f"<Tenant {self.slug} - {self.nombre_comercial}>"
