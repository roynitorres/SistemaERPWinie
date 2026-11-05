# Importamos instancia db
from database import db

# Importamos fechas automáticas
from datetime import datetime, UTC, timedelta

# Herramientas para manejo seguro contraseñas
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

# Flask-Login
# Le da automáticamente: is_authenticated, is_active, get_id
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
    # INFORMACIÓN DE PERFIL
    # =========================

    nombre_completo = db.Column(
        db.String(150),
        nullable=True
    )
    
    @property
    def nombre_mostrar(self):
        if not self.nombre_completo:
            return self.username
        
        partes = self.nombre_completo.strip().split()
        if len(partes) == 0:
            return self.username
        elif len(partes) == 1:
            return partes[0].capitalize()
        elif len(partes) == 2:
            # Nombre y primer apellido (ej: Juan Perez -> Juan P.)
            return f"{partes[0].capitalize()} {partes[1][0].upper()}."
        else:
            # Nombre, primer apellido, inicial del segundo apellido (ej: Juan Perez Gomez -> Juan Perez G.)
            return f"{partes[0].capitalize()} {partes[1].capitalize()} {partes[2][0].upper()}."

    direccion = db.Column(
        db.String(255),
        nullable=True
    )
    
    genero = db.Column(
        db.String(20),
        nullable=True
    )
    
    telefono = db.Column(
        db.String(20),
        nullable=True
    )
    
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=True
    )

    foto_perfil = db.Column(
        db.String(255),
        nullable=True
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

    # Guarda la contraseña temporal mientras no haya sido cambiada por el cliente
    password_temporal_plana = db.Column(
        db.String(100),
        nullable=True
    )

    # =========================
    # SEGURIDAD Y FUERZA BRUTA
    # =========================

    # Contador de intentos fallidos consecutivos
    intentos_fallidos = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    # Fecha y hora hasta la cual la cuenta permanece bloqueada
    bloqueado_hasta = db.Column(
        db.DateTime,
        nullable=True
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
    # MÉTODOS DE FUERZA BRUTA
    # =========================

    @property
    def esta_bloqueado(self):
        """Indica si la cuenta se encuentra bloqueada temporalmente."""
        if not self.bloqueado_hasta:
            return False
        
        bloq = self.bloqueado_hasta
        if bloq.tzinfo is None:
            bloq = bloq.replace(tzinfo=UTC)
        
        return bloq > datetime.now(UTC)

    def minutos_restantes_bloqueo(self):
        """Retorna los minutos restantes que le quedan a la cuenta bloqueada."""
        if not self.esta_bloqueado:
            return 0
        
        bloq = self.bloqueado_hasta
        if bloq.tzinfo is None:
            bloq = bloq.replace(tzinfo=UTC)
            
        delta = bloq - datetime.now(UTC)
        minutos = int((delta.total_seconds() + 59) // 60)
        return max(1, minutos)

    def registrar_fallo_login(self, max_intentos=5, bloqueo_minutos=15):
        """
        Incrementa los intentos fallidos. Si alcanza el máximo, bloquea la cuenta.
        Retorna True si la cuenta fue bloqueada en esta llamada.
        """
        self.intentos_fallidos = (self.intentos_fallidos or 0) + 1
        if self.intentos_fallidos >= max_intentos:
            self.bloqueado_hasta = datetime.now(UTC) + timedelta(minutes=bloqueo_minutos)
            return True
        return False

    def limpiar_intentos_fallidos(self):
        """Reinicia el contador de intentos fallidos y levanta el bloqueo."""
        self.intentos_fallidos = 0
        self.bloqueado_hasta = None

    # =========================
    # REPRESENTACIÓN OBJETO
    # =========================

    # Representación amigable consola
    def __repr__(self):
        return f"<Usuario {self.username}>"
