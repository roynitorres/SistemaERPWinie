from database import db
from datetime import datetime, UTC
from models.enums import EstadoCliente

# Modelo Cliente
class Cliente(db.Model):
    # Nombre de la tabla en la base de datos
    __tablename__ = "clientes"

    id = db.Column(db.Integer,primary_key=True)
    codigo = db.Column(db.String(20),unique=True,nullable=True)
    nombres = db.Column(db.String(100),nullable=False)
    telefono = db.Column(db.String(8),nullable=False,unique=True)
    ciudad = db.Column(db.String(100),nullable=True)
    estado = db.Column(db.Enum(EstadoCliente),default=EstadoCliente.ACTIVO)
    created_at = db.Column(db.DateTime,default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime,default=lambda: datetime.now(UTC),onupdate=lambda: datetime.now(UTC))

    # RELACIONES

    ventas = db.relationship("Venta",back_populates="cliente",lazy=True)
    usuario = db.relationship("Usuario",back_populates="cliente",uselist=False)

    # REPRESENTACIÓN OBJETO

    # Representación amigable consola
    def __repr__(self):
        return f"<Cliente {self.nombres}>"