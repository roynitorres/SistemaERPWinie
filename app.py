from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from flask_login import login_required
from config import Config
from database import db, migrate
from datetime import datetime, date, timedelta
from sqlalchemy import func

# MODELOS

from models.rol import Rol
from models.cliente import Cliente
from models.usuario import Usuario
from models.categoria import Categoria
from models.producto import Producto
from models.venta import Venta
from models.detalle_venta import DetalleVenta
from models.pago import Pago
from models.empresa import Empresa
       
# BLUEPRINTS

from routes.auth import auth_bp
from routes.clientes import clientes_bp
from routes.categorias import categorias_bp
from routes.productos import productos_bp
from routes.ventas import ventas_bp
from routes.pagos import pagos_bp
from routes.portal_cliente import portal_cliente_bp
from routes.empresa import empresa_bp
from routes.usuarios import usuarios_bp
from routes.roles import roles_bp

# APP


app = Flask(__name__)

# Configuración general
app.config.from_object(Config)

# Inicializar base de datos
db.init_app(app)

# Inicializar migraciones
migrate.init_app(app, db)

# Login manager
login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
# =========================
# BLUEPRINTS
# =========================

app.register_blueprint(auth_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(categorias_bp)
app.register_blueprint(productos_bp)
app.register_blueprint(ventas_bp)
app.register_blueprint(pagos_bp)
app.register_blueprint(portal_cliente_bp)
app.register_blueprint(empresa_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(roles_bp)
# =========================
# USER LOADER
# =========================
@login_manager.user_loader
def load_user(user_id):

    return Usuario.query.get(int(user_id))





# =========================
# RUTA PRINCIPAL
# =========================

@app.route("/")
def inicio():
    return redirect(url_for("auth.login"))



@app.route("/dashboard")
@login_required
def dashboard():
    hoy = date.today()
    ahora = datetime.now()
    hora = ahora.hour

    if hora < 12:
        saludo = "Buenos dias"
    elif hora < 18:
        saludo = "Buenas tardes"
    else:
        saludo = "Buenas noches"

    clientes_total = Cliente.query.count()
    clientes_activos = Cliente.query.filter_by(estado=True).count()
    clientes_inactivos = Cliente.query.filter_by(estado=False).count()
    clientes_pct = round((clientes_activos / clientes_total) * 100) if clientes_total else 0

    productos_total = Producto.query.filter_by(estado="ACTIVO").count()
    productos_stock_normal = Producto.query.filter(
        Producto.estado == "ACTIVO",
        Producto.stock > 5
    ).count()
    productos_stock_critico = Producto.query.filter(
        Producto.estado == "ACTIVO",
        Producto.stock > 0,
        Producto.stock <= 5
    ).count()
    productos_pct = round((productos_stock_normal / productos_total) * 100) if productos_total else 0

    ventas_activas = Venta.query.filter_by(estado="ACTIVA").all()
    facturas_total = len(ventas_activas)
    facturas_contado = len([v for v in ventas_activas if v.tipo_venta == "CONTADO"])
    facturas_credito = len([v for v in ventas_activas if v.tipo_venta == "CREDITO"])
    ventas_pct = round((facturas_contado / facturas_total) * 100) if facturas_total else 0

    pagos_total_monto = 0
    pagos_pagado_monto = 0
    pagos_pendiente_monto = 0
    facturas_pagadas = 0
    facturas_pendientes = 0
    clientes_a_cobrar = []

    for venta in ventas_activas:
        total_venta = float(venta.total_venta)
        total_pagado = sum(
            float(pago.monto_pago)
            for pago in venta.pagos
            if pago.estado == "ACTIVO"
        )
        saldo = max(total_venta - total_pagado, 0)

        pagos_total_monto += total_venta
        pagos_pagado_monto += total_pagado
        pagos_pendiente_monto += saldo

        if saldo <= 0:
            facturas_pagadas += 1
            continue

        facturas_pendientes += 1

        if venta.tipo_venta == "CONTADO":
            fecha_cobro = venta.fecha_venta.date()
        else:
            fecha_cobro = venta.fecha_limite_credito or venta.fecha_venta.date()

        if fecha_cobro <= hoy:
            dias_mora = (hoy - fecha_cobro).days
            clientes_a_cobrar.append({
                "cliente": f"{venta.cliente.nombres} {venta.cliente.apellidos or ''}".strip(),
                "estado": "Moroso" if dias_mora > 0 else "Cobrar hoy",
                "dias": dias_mora,
            })

    clientes_a_cobrar.sort(key=lambda item: item["dias"], reverse=True)

    pagos_pct = round((pagos_pagado_monto / pagos_total_monto) * 100) if pagos_total_monto else 0

    ventas_ultimos_7 = []
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        total_dia = sum(
            float(v.total_venta)
            for v in ventas_activas
            if v.fecha_venta.date() == dia
        )
        ventas_ultimos_7.append({
            "label": dia.strftime("%d/%m"),
            "total": total_dia
        })

    productos_mas_vendidos = db.session.query(
        Producto.nombre.label("nombre"),
        func.sum(DetalleVenta.cantidad).label("cantidad")
    ).join(
        DetalleVenta,
        DetalleVenta.producto_id == Producto.id
    ).join(
        Venta,
        Venta.id == DetalleVenta.venta_id
    ).filter(
        Venta.estado == "ACTIVA"
    ).group_by(
        Producto.id
    ).order_by(
        func.sum(DetalleVenta.cantidad).desc()
    ).limit(5).all()

    kpis = {
        "clientes": {
            "total": clientes_total,
            "izquierda_label": "Activos",
            "izquierda": clientes_activos,
            "derecha_label": "Inactivos",
            "derecha": clientes_inactivos,
            "porcentaje": clientes_pct,
        },
        "productos": {
            "total": productos_total,
            "izquierda_label": "Stock normal",
            "izquierda": productos_stock_normal,
            "derecha_label": "Stock critico",
            "derecha": productos_stock_critico,
            "porcentaje": productos_pct,
        },
        "ventas": {
            "total": facturas_total,
            "izquierda_label": "Contado",
            "izquierda": facturas_contado,
            "derecha_label": "Credito",
            "derecha": facturas_credito,
            "porcentaje": ventas_pct,
        },
        "pagos": {
            "total": pagos_total_monto,
            "izquierda_label": "Pagado",
            "izquierda": pagos_pagado_monto,
            "derecha_label": "Pendiente",
            "derecha": pagos_pendiente_monto,
            "porcentaje": pagos_pct,
        },
    }

    chart_data = {
        "facturas_tipo": {
            "labels": ["Contado", "Credito"],
            "values": [facturas_contado, facturas_credito],
        },
        "pagos_estado": {
            "labels": ["Pagadas", "Pendientes"],
            "values": [facturas_pagadas, facturas_pendientes],
        },
        "ventas_7_dias": {
            "labels": [item["label"] for item in ventas_ultimos_7],
            "values": [item["total"] for item in ventas_ultimos_7],
        },
        "top_productos": {
            "labels": [p.nombre for p in productos_mas_vendidos],
            "values": [int(p.cantidad or 0) for p in productos_mas_vendidos],
        },
    }

    return render_template(
        "dashboard.html",
        saludo=saludo,
        ahora=ahora,
        fecha_larga=ahora.strftime("%d/%m/%Y"),
        clientes_a_cobrar=clientes_a_cobrar,
        kpis=kpis,
        chart_data=chart_data
    )




if __name__ == "__main__":
    app.run(debug=True)