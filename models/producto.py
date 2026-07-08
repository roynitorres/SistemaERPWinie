# Importamos instancia db
from database import db

# Importamos datetime
from datetime import datetime, UTC


# Modelo Producto
class Producto(db.Model):

    # Nombre tabla
    __tablename__ = "productos"

    # =========================
    # CLAVE PRIMARIA
    # =========================

    # ID único producto
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =========================
    # INFORMACIÓN PRODUCTO
    # =========================

    # Código producto
    codigo_producto = db.Column(
        db.String(50),
        nullable=False,
        unique=True
    )

    # Nombre producto
    nombre = db.Column(
        db.String(150),
        nullable=False
    )

    # Marca producto
    marca = db.Column(
        db.String(100),
        nullable=False
    )
     # UND
    unidad = db.Column(
        db.String(10),
        nullable=False,
        default="UND"
    )
     # Estado

    estado = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVO"
    )

    # =========================
    # LLAVES FORÁNEAS
    # =========================

    # Categoría producto
    categoria_id = db.Column(
        db.Integer,
        db.ForeignKey("categorias.id"),
        nullable=False
    )

    # =========================
    # INVENTARIO
    # =========================
    # Cantidad Comprada
    cantidad_comprada = db.Column(
    db.Integer,
    nullable=False
    )

    # Cantidad disponible
    stock = db.Column(
        db.Integer,
        default=0
    )

    # =========================
    # PRECIOS
    # =========================

    # Precio compra
    precio_compra = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    # Precio venta
    precio_venta = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    # =========================
    # CONTROL SISTEMA
    # =========================

    fecha_compra = db.Column(
    db.Date,
    nullable=False
    )

    # Fecha creación
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC)
    )

    # Fecha actualización
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    # =========================
    # RELACIONES
    # =========================

    # Producto pertenece categoría
    categoria = db.relationship(
        "Categoria",
        back_populates="productos"
    )

    # Producto participa ventas
    detalle_ventas = db.relationship(
        "DetalleVenta",
        back_populates="producto",
        lazy=True
    )

    # =========================
    # REPRESENTACIÓN OBJETO
    # =========================

    # Representación amigable consola
    def __repr__(self):

        return f"<Producto {self.nombre}>"