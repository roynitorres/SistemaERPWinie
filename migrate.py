from app import app
from database import db
from models.producto import Producto

with app.app_context():
    productos_activos = Producto.query.filter_by(estado="ACTIVO").all()
    for p in productos_activos:
        p.estado = "EN STOCK"
        
    productos_inactivos = Producto.query.filter_by(estado="INACTIVO").all()
    for p in productos_inactivos:
        p.estado = "VENDIDO"
        
    db.session.commit()
    print(f"Migrados {len(productos_activos)} activos a EN STOCK, {len(productos_inactivos)} inactivos a VENDIDO.")
