from database import db
from datetime import datetime, UTC

class Banco(db.Model):
    __tablename__ = "bancos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="ACTIVO")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    def __repr__(self):
        return f"<Banco {self.nombre}>"
