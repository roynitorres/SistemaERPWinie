from database import db
from datetime import datetime, UTC

class ReciboCaja(db.Model):
    __tablename__ = "recibos_caja"

    id = db.Column(db.Integer, primary_key=True)
    numero_recibo = db.Column(db.String(50), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    banco_id = db.Column(db.Integer, db.ForeignKey("bancos.id"), nullable=True)

    monto_total = db.Column(db.Numeric(10, 2), nullable=False)
    saldo_anterior = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    saldo_nuevo = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)

    tipo_pago = db.Column(db.String(20), nullable=False, default="EFECTIVO")
    referencia = db.Column(db.String(100), nullable=True)
    observaciones = db.Column(db.Text, nullable=True)

    estado = db.Column(db.String(20), nullable=False, default="ACTIVO")
    motivo_anulacion = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    cliente = db.relationship("Cliente", backref="recibos_caja")
    usuario = db.relationship("Usuario", backref="recibos_caja")
    banco = db.relationship("Banco", backref="recibos_caja")
    pagos = db.relationship("Pago", back_populates="recibo_caja", lazy=True)

    def __repr__(self):
        return f"<ReciboCaja #{self.numero_recibo} Cliente:{self.cliente_id} Monto:{self.monto_total}>"
