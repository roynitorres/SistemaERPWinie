from database import db
from datetime import datetime, UTC


class Empresa(db.Model):
    __tablename__ = "empresa"

    id = db.Column(db.Integer, primary_key=True)

    razon_social = db.Column(db.String(150), nullable=False)
    ruc = db.Column(db.String(30), nullable=True)
    tipo_empresa = db.Column(db.String(20), nullable=True)

    direccion = db.Column(db.String(250), nullable=True)
    ciudad = db.Column(db.String(100), nullable=True)
    telefono = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    sitio_web = db.Column(db.String(150), nullable=True)

    regimen = db.Column(db.String(80), nullable=True)
    serie_factura = db.Column(db.String(20), nullable=False, default="F001")
    correlativo = db.Column(db.String(20), nullable=False, default="00034")
    iva = db.Column(db.Numeric(5, 2), nullable=False, default=15)

    logo = db.Column(db.String(200), nullable=True)
    estado = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )