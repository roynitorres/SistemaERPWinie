from database import db
from datetime import datetime, UTC
from models.enums import EstadoProveedor

class Proveedor(db.Model):
    __tablename__ = "proveedores"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=True)
    nombre_proveedor = db.Column(db.String(150), nullable=False)
    nombre_contacto = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    departamento = db.Column(db.String(100), nullable=False)
    municipio = db.Column(db.String(100), nullable=False)
    ruc = db.Column(db.String(50), unique=True, nullable=True)
    direccion = db.Column(db.String(255), nullable=True)
    estado = db.Column(db.Enum(EstadoProveedor), default=EstadoProveedor.ACTIVO)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    productos = db.relationship("Producto", back_populates="proveedor", lazy=True)

    def __repr__(self):
        return f"<Proveedor {self.nombre_proveedor}>"
