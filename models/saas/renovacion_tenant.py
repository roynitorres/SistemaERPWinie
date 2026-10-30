from datetime import datetime, date, UTC
from database import db


class RenovacionTenant(db.Model):
    """
    Registro histórico de cada pago y renovación de suscripción SaaS de una empresa.
    Almacenado en la base central (master.db).
    """
    __bind_key__ = "master"
    __tablename__ = "renovaciones_tenant"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    periodo_mes = db.Column(db.String(50), nullable=False)  # Ej: "Octubre 2026"
    monto = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    fecha_pago = db.Column(db.Date, nullable=False, default=date.today)
    fecha_corte_resultante = db.Column(db.Date, nullable=False)
    dias_agregados = db.Column(db.Integer, nullable=False, default=30)
    notas = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return f"<RenovacionTenant tenant={self.tenant_id} {self.periodo_mes}: {self.monto}>"
