from database import db
from datetime import datetime, UTC

class AlertaSilenciada(db.Model):
    __tablename__ = "alertas_silenciadas"

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False) # 'PRODUCTO', 'COBRANZA'
    referencia_id = db.Column(db.Integer, nullable=False)
    silenciado_hasta = db.Column(db.Date, nullable=True) # None = indefinido / descontinuado
    motivo = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self):
        return f"<AlertaSilenciada {self.tipo} ref:{self.referencia_id} hasta:{self.silenciado_hasta}>"
