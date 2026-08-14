from database import db
from datetime import datetime, UTC

class CuotaVenta(db.Model):
    __tablename__ = "cuotas_venta"

    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"), nullable=False)
    numero_cuota = db.Column(db.Integer, nullable=False)
    monto_cuota = db.Column(db.Numeric(10, 2), nullable=False)
    monto_abonado = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    fecha_vencimiento_gracia = db.Column(db.Date, nullable=False)
    dias_gracia = db.Column(db.Integer, nullable=False, default=2)
    estado = db.Column(db.String(20), nullable=False, default="PENDIENTE") # PENDIENTE, GRACIA, PAGADA, VENCIDA

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    venta = db.relationship("Venta", back_populates="cuotas")
    pagos = db.relationship("Pago", back_populates="cuota", lazy=True)

    def __repr__(self):
        return f"<CuotaVenta Venta:{self.venta_id} Cuota:#{self.numero_cuota} Monto:{self.monto_cuota}>"
