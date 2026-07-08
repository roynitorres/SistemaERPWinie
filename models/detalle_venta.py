# Importamos instancia db
from database import db


# Modelo DetalleVenta
class DetalleVenta(db.Model):

    # Nombre tabla
    __tablename__ = "detalle_ventas"

    # ==================================================
    # CLAVE PRIMARIA
    # ==================================================

    # ID único detalle venta
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==================================================
    # LLAVES FORÁNEAS
    # ==================================================

    # Venta a la que pertenece
    venta_id = db.Column(
        db.Integer,
        db.ForeignKey("ventas.id"),
        nullable=False
    )

    # Producto vendido
    producto_id = db.Column(
        db.Integer,
        db.ForeignKey("productos.id"),
        nullable=False
    )

    # ==================================================
    # INFORMACIÓN PRODUCTO VENDIDO
    # ==================================================

    # Cantidad vendida
    cantidad = db.Column(
        db.Integer,
        nullable=False
    )

    # Precio unitario histórico
    # IMPORTANTE:
    # Guarda el precio exacto
    # al momento de la venta
    precio_unitario = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    descuento_porcentaje = db.Column(
        db.Numeric(5, 2),
        nullable=False,
        default=0
    )

    descuento_monto = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    # Subtotal histórico
    # cantidad * precio_unitario
    subtotal = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    # ==================================================
    # RELACIONES
    # ==================================================

    # Detalle pertenece venta
    venta = db.relationship(
        "Venta",
        back_populates="detalle_ventas"
    )

    # Detalle pertenece producto
    producto = db.relationship(
        "Producto",
        back_populates="detalle_ventas"
    )

    # ==================================================
    # REPRESENTACIÓN OBJETO
    # ==================================================

    # Representación amigable consola
    def __repr__(self):

        return f"<DetalleVenta {self.id}>"