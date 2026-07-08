# Importamos la instancia db
from database import db

# Importamos datetime para fechas automáticas
from datetime import datetime, UTC


# Modelo Cliente
class Cliente(db.Model):

    # Nombre de la tabla en la base de datos
    __tablename__ = "clientes"

    # =========================
    # CLAVE PRIMARIA
    # =========================

    # ID único del cliente
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =========================
    # INFORMACIÓN CLIENTE
    # =========================

    # Nombres del cliente
    nombres = db.Column(
        db.String(100),
        nullable=False
    )

    # Código del cliente
    codigo = db.Column(
        db.String(20),
        unique=True,
        nullable=True
    )

    # Apellidos del cliente
    apellidos = db.Column(
        db.String(100),
        nullable=True
    )

    # Número telefónico
    telefono = db.Column(
        db.String(8),
        nullable=False,
        unique=True
    )

    # Correo electrónico
    email = db.Column(
        db.String(100),
        nullable=True
    )

    # Ciudad
    ciudad = db.Column(
        db.String(100),
        nullable=True
    )

    # Dirección del cliente
    direccion = db.Column(
        db.Text,
        nullable=True
    )
    # Fecha ingreso cliente
    fecha_ingreso = db.Column(
        db.Date,
        nullable=False
    )

    # =========================
    # CONTROL DEL SISTEMA
    # =========================

    # Estado lógico
    # True = Activo
    # False = Inactivo
    estado = db.Column(
        db.Boolean,
        default=True
    )

    # Fecha creación registro
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC)
    )

    # Fecha actualización registro
    # datetime.utcnow Inserta automáticamente:
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    # =========================
    # RELACIONES
    # =========================

    # Un cliente puede tener muchas ventas
    ventas = db.relationship(
        "Venta",
        back_populates="cliente",
        lazy=True
    )

    # Un cliente puede tener un usuario
    usuario = db.relationship(
        "Usuario",
        back_populates="cliente",
        uselist=False
    )

    # =========================
    # REPRESENTACIÓN OBJETO
    # =========================

    # Representación amigable consola
    def __repr__(self):

        return f"<Cliente {self.nombres} {self.apellidos}>"