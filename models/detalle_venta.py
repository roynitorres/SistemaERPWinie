# Importamos instancia db
from database import db

class DetalleVenta(db.Model):

    __tablename__ = "detalle_ventas"

    id = db.Column(db.Integer,primary_key=True)
    venta_id = db.Column(db.Integer,db.ForeignKey("ventas.id"),nullable=False)
    producto_id = db.Column(db.Integer,db.ForeignKey("productos.id"),nullable=False)
    cantidad = db.Column( db.Integer,nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2),nullable=False)
    descuento_porcentaje = db.Column(db.Numeric(5, 2),nullable=False,default=0)
    descuento_monto = db.Column(db.Numeric(10, 2),nullable=False,default=0)
    subtotal = db.Column(db.Numeric(10, 2),nullable=False)
    venta = db.relationship("Venta",back_populates="detalle_ventas")
    producto = db.relationship("Producto",back_populates="detalle_ventas")
    def __repr__(self):
        return f"<DetalleVenta {self.id}>"