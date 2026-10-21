from datetime import datetime, UTC
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from database import db


class SuperUsuario(UserMixin, db.Model):
    """
    Modelo de Super Administrador en la Base Central (master.db).
    Usuario con privilegios exclusivos para gobernar clientes, licencias y respaldos.
    """

    ''''
    ¿Qué hace?: Le indica a Flask-SQLAlchemy que este modelo no va en la base de datos por defecto, sino en una base de datos secundaria o específica llamada "master"
    '''
    __bind_key__ = "master"
    __tablename__ = "super_usuarios"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    nombre_completo = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)

    estado = db.Column(db.Boolean, default=True, nullable=False)
    ultimo_acceso = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    @property
    def is_active(self) -> bool:
        return self.estado

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<SuperUsuario {self.username}>"
