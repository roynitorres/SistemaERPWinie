from database import db

from datetime import datetime, UTC
from models.enums import EstadoVenta, TipoVenta

class Venta(db.Model):

    
    __tablename__ = "ventas"
    id = db.Column(db.Integer,primary_key=True)
    cliente_id = db.Column(db.Integer,db.ForeignKey("clientes.id"),nullable=False)
    usuario_id = db.Column(db.Integer,db.ForeignKey("usuarios.id"),nullable=False)
    fecha_venta = db.Column(db.DateTime,nullable=False,default=lambda: datetime.now(UTC))
    fecha_limite_credito = db.Column(db.Date,nullable=True)
    tipo_venta = db.Column(db.Enum(TipoVenta),nullable=False)
    numero_factura = db.Column(db.String(30),unique=True,nullable=False)
    total_venta = db.Column(db.Numeric(10, 2),nullable=False)
    estado = db.Column(db.Enum(EstadoVenta),nullable=False,default=EstadoVenta.ACTIVA)
    observaciones = db.Column(db.Text,nullable=True)
    created_at = db.Column(db.DateTime,nullable=False,default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime,nullable=False,default=lambda: datetime.now(UTC),onupdate=lambda: datetime.now(UTC))
    cliente = db.relationship("Cliente",back_populates="ventas")
    usuario = db.relationship("Usuario",back_populates="ventas")
    detalle_ventas = db.relationship("DetalleVenta", back_populates="venta", lazy=True)
    pagos = db.relationship("Pago",back_populates="venta",lazy=True,order_by="Pago.fecha_pago.desc()")
    cuotas = db.relationship("CuotaVenta", back_populates="venta", lazy=True, cascade="all, delete-orphan", order_by="CuotaVenta.numero_cuota.asc()")

    def __repr__(self):

        return f"<Venta {self.id}>"