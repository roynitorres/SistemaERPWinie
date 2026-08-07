from database import db
from datetime import datetime, UTC
from models.enums import EstadoCategoria


# Modelo Categoria
class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer,primary_key=True)
    
    codigo = db.Column(db.String(20),unique=True,nullable=True)
    nombre = db.Column(db.String(100),nullable=False,unique=True)
    descripcion = db.Column(db.Text,nullable=True)
    estado = db.Column(db.Enum(EstadoCategoria), default=EstadoCategoria.ACTIVO)

    created_at = db.Column(db.DateTime,default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime,default=lambda: datetime.now(UTC),onupdate=lambda: datetime.now(UTC))

    
    # RELACIONES
    productos = db.relationship("Producto",back_populates="categoria",lazy=True)

    # REPRESENTACIÓN OBJETO
    # Representación amigable consola
    def __repr__(self):
        return f"<Categoria {self.nombre}>"