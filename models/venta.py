# Importamos instancia db
from database import db

# Importamos datetime para fechas automáticas
from datetime import datetime, UTC


# Modelo Venta
class Venta(db.Model):

    # Nombre de la tabla
    __tablename__ = "ventas"

    # ==================================================
    # CLAVE PRIMARIA
    # ==================================================

    # ID único de la venta
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==================================================
    # LLAVES FORÁNEAS
    # ==================================================

    # Cliente que realiza la compra
    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id"),
        nullable=False
    )

    # Usuario que registra la venta
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    # ==================================================
    # INFORMACIÓN GENERAL VENTA
    # ==================================================

    # Fecha y hora de la venta
    fecha_venta = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC)
    )

    # Fecha límite del crédito
    # Solo aplica para ventas al crédito
    fecha_limite_credito = db.Column(
        db.Date,
        nullable=True
    )

    # Tipo de venta:
    # CONTADO
    # CREDITO
    tipo_venta = db.Column(
        db.String(20),
        nullable=False
    )
    # Número factura
    numero_factura = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    # ==================================================
    # INFORMACIÓN FINANCIERA
    # ==================================================

    # Monto total de la venta
    total_venta = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    
    # ==============================================
    # ESTADO FACTURA
    # ==============================================

    estado = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVA"
    )

    # ==================================================
    # OBSERVACIONES
    # ==================================================

    # Comentarios adicionales
    observaciones = db.Column(
        db.Text,
        nullable=True
    )

    

    # Fecha creación registro
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC)
    )

    # Fecha última actualización
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    # ==================================================
    # RELACIONES
    # ==================================================

    # La venta pertenece a un cliente
    cliente = db.relationship(
        "Cliente",
        back_populates="ventas"
    )

    # La venta fue registrada por un usuario
    usuario = db.relationship(
        "Usuario",
        back_populates="ventas"
    )

    # Una venta puede tener muchos productos
    detalle_ventas = db.relationship(
        "DetalleVenta",
        back_populates="venta",
        lazy=True
    )

    # Una venta puede tener muchos pagos
    pagos = db.relationship(
        "Pago",
        back_populates="venta",
        lazy=True,
        order_by="Pago.fecha_pago.desc()"
    )

    # ==================================================
    # REPRESENTACIÓN OBJETO
    # ==================================================

    # Representación amigable consola
    def __repr__(self):

        return f"<Venta {self.id}>"