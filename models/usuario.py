# Importamos instancia db
from database import db

# Importamos fechas automáticas
from datetime import datetime, UTC

# Herramientas para manejo seguro contraseñas
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

# Flask-Login
#Le da automáticamente: is_authenticated, is_active, get_id
from flask_login import UserMixin


# Modelo Usuario
class Usuario(UserMixin, db.Model):

    # Nombre tabla
    __tablename__ = "usuarios"

    # =========================
    # CLAVE PRIMARIA
    # =========================

    # ID único usuario
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =========================
    # INFORMACIÓN LOGIN
    # =========================

    # Nombre usuario login
    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    # Contraseña encriptada
    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # =========================
    # LLAVES FORÁNEAS
    # =========================

    # Relación tabla roles
    rol_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.id"),
        nullable=False
    )

    # Relación opcional cliente
    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id"),
        nullable=True
    )

    # =========================
    # CONTROL SISTEMA
    # =========================

    # Estado lógico
    estado = db.Column(
        db.Boolean,
        default=True
    )

    debe_cambiar_password = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    # Fecha creación registro
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC)
    )

    # Fecha actualización registro
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    # =========================
    # RELACIONES
    # =========================

    # Usuario pertenece rol
    rol = db.relationship(
        "Rol",
        back_populates="usuarios"
    )

    # Usuario puede pertenecer cliente
    cliente = db.relationship(
        "Cliente",
        back_populates="usuario"
    )

    # Usuario registra ventas
    ventas = db.relationship(
        "Venta",
        back_populates="usuario",
        lazy=True
    )

    # Usuario registra pagos
    pagos = db.relationship(
        "Pago",
        back_populates="usuario",
        lazy=True
    )

    # =========================
    # MÉTODOS CONTRASEÑA
    # =========================

    # Generar hash contraseña
    def set_password(self, password):

        self.password_hash = generate_password_hash(password)

    # Verificar contraseña
    def check_password(self, password):

        return check_password_hash(
            self.password_hash,
            password
        )

    # =========================
    # REPRESENTACIÓN OBJETO
    # =========================

    # Representación amigable consola
    def __repr__(self):

        return f"<Usuario {self.username}>"