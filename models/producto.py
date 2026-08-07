from database import db
from datetime import datetime, UTC
from models.enums import EstadoProducto

class Producto(db.Model):
    # Nombre tabla
    __tablename__ = "productos"
    id = db.Column(db.Integer,primary_key=True)
    codigo_producto = db.Column(db.String(50),nullable=False)
    nombre = db.Column(db.String(150),nullable=False)
    marca = db.Column(db.String(100),nullable=False)
    estado = db.Column(db.Enum(EstadoProducto), default=EstadoProducto.ACTIVO, nullable=False)
    categoria_id = db.Column(db.Integer,db.ForeignKey("categorias.id"),nullable=False)
    proveedor_id = db.Column(db.Integer,db.ForeignKey("proveedores.id"),nullable=False)
    cantidad_comprada = db.Column(db.Integer,nullable=False)
    stock = db.Column(db.Integer,default=0)
    precio_compra = db.Column(db.Numeric(10, 2),nullable=False)
    precio_venta = db.Column(db.Numeric(10, 2),nullable=False)
    fecha_compra = db.Column(db.Date,nullable=False)
    created_at = db.Column(db.DateTime,default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime,default=lambda: datetime.now(UTC),onupdate=lambda: datetime.now(UTC))

  
    # RELACIONES
    categoria = db.relationship("Categoria",back_populates="productos")
    proveedor = db.relationship("Proveedor",back_populates="productos")
    detalle_ventas = db.relationship("DetalleVenta",back_populates="producto",lazy=True)

    def __repr__(self):
        return f"<Producto {self.nombre}>"