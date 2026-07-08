# Importamos instancia db
from database import db

# Importamos datetime
from datetime import datetime, UTC


# Modelo Categoria
class Categoria(db.Model):

    # Nombre tabla
    __tablename__ = "categorias"

    # =========================
    # CLAVE PRIMARIA
    # =========================

    # ID único categoría
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    # Código del cliente
    codigo = db.Column(
        db.String(20),
        unique=True,
        nullable=True
    )

    # =========================
    # INFORMACIÓN CATEGORÍA
    # =========================

    # Nombre categoría
    nombre = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    # Descripción categoría
    descripcion = db.Column(
        db.Text,
        nullable=True
    )
    # Estado lógico
    # True = Activo
    # False = Inactivo
    estado = db.Column(
        db.Boolean,
        default=True
    )

    # =========================
    # CONTROL SISTEMA
    # =========================


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

    # Una categoría puede tener muchos productos
    productos = db.relationship(
        "Producto",
        back_populates="categoria",
        lazy=True
    )

    # =========================
    # REPRESENTACIÓN OBJETO
    # =========================

    # Representación amigable consola
    def __repr__(self):

        return f"<Categoria {self.nombre}>"