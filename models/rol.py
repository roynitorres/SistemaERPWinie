from database import db


class Rol(db.Model):

    __tablename__ = "roles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(50),
        nullable=False,
        unique=True
    )

    descripcion = db.Column(
        db.Text,
        nullable=True
    )

    estado = db.Column(
        db.Boolean,
        default=True
    )
    descuento_maximo = db.Column(
        db.Numeric(5, 2),
        nullable=False,
        default=0
    )

    # Relación con usuarios
    usuarios = db.relationship(
        "Usuario",
        back_populates="rol",
        lazy=True
    )

    def __repr__(self):
        return f"<Rol {self.nombre}>"