# Importamos instancia db
from database import db

# Importamos datetime
from datetime import datetime, UTC


# Modelo Pago
class Pago(db.Model):

    # Nombre tabla
    __tablename__ = "pagos"

    # ==================================================
    # CLAVE PRIMARIA
    # ==================================================

    # ID único pago
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==================================================
    # LLAVES FORÁNEAS
    # ==================================================

    # Venta asociada
    venta_id = db.Column(
        db.Integer,
        db.ForeignKey("ventas.id"),
        nullable=False
    )

    # Usuario registra pago
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    # ==================================================
    # INFORMACIÓN PAGO
    # ==================================================

    # Fecha y hora pago
    fecha_pago = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC)
    )

    # Monto abonado
    monto_pago = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )
    
    # Tipo pago
    # EFECTIVO
    # TRANSFERENCIA
    tipo_pago = db.Column(
        db.String(20),
        nullable=False
    )
    referencia = db.Column(
        db.String(100),
        nullable=True
    )

    # Observaciones pago
    observaciones = db.Column(
        db.Text,
        nullable=True
    )

    # ==================================================
    # CONTROL FINANCIERO
    # ==================================================

    # Estado pago
    # ACTIVO
    # ANULADO
    estado = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVO"
    )

    # Motivo anulación
    motivo_anulacion = db.Column(
        db.Text,
        nullable=True
    )

    # ==================================================
    # CONTROL SISTEMA
    # ==================================================

    # Fecha creación registro
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC)
    )

    # ==================================================
    # RELACIONES
    # ==================================================

    # Pago pertenece venta
    venta = db.relationship(
        "Venta",
        back_populates="pagos"
    )

    # Pago registrado usuario
    usuario = db.relationship(
        "Usuario",
        back_populates="pagos"
    )

    # ==================================================
    # REPRESENTACIÓN OBJETO
    # ==================================================

    # Representación amigable consola
    def __repr__(self):

        return f"<Pago {self.id}>"