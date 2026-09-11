from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from flask_login import login_required
from config import Config
from database import db, migrate
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract

# MODELOS

from models.rol import Rol
from models.cliente import Cliente
from models.usuario import Usuario
from models.categoria import Categoria
from models.producto import Producto
from models.venta import Venta
from models.detalle_venta import DetalleVenta
from models.pago import Pago
from models.banco import Banco
from models.cuota_venta import CuotaVenta
from models.empresa import Empresa
from models.proveedor import Proveedor
from models.enums import EstadoVenta, TipoVenta, EstadoProducto, EstadoCliente, EstadoProveedor
from sqlalchemy.orm import joinedload
       
# BLUEPRINTS

from routes.auth import auth_bp
from routes.clientes import clientes_bp
from routes.categorias import categorias_bp
from routes.productos import productos_bp
from routes.ventas import ventas_bp
from routes.pagos import pagos_bp
from routes.portal_cliente import portal_cliente_bp
from routes.empresa import empresa_bp
from routes.proveedores import proveedores_bp
from routes.usuarios import usuarios_bp
from routes.roles import roles_bp

from routes.reportes import reportes_bp
from routes.perfil import perfil_bp

# APP

app = Flask(__name__)

# Configuración general
app.config.from_object(Config)

# Inicializar base de datos
db.init_app(app)

with app.app_context():
    db.create_all()
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns_usuarios = [c['name'] for c in inspector.get_columns('usuarios')]
        if 'password_temporal_plana' not in columns_usuarios:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE usuarios ADD COLUMN password_temporal_plana VARCHAR(100)"))
                conn.commit()

        # Migración de columnas en la tabla pagos
        columns_pagos = [c['name'] for c in inspector.get_columns('pagos')]
        with db.engine.connect() as conn:
            if 'banco_id' not in columns_pagos:
                conn.execute(text("ALTER TABLE pagos ADD COLUMN banco_id INTEGER"))
            if 'cuota_id' not in columns_pagos:
                conn.execute(text("ALTER TABLE pagos ADD COLUMN cuota_id INTEGER"))
            if 'monto_efectivo' not in columns_pagos:
                conn.execute(text("ALTER TABLE pagos ADD COLUMN monto_efectivo NUMERIC(10,2) DEFAULT 0.00"))
            if 'monto_transferencia' not in columns_pagos:
                conn.execute(text("ALTER TABLE pagos ADD COLUMN monto_transferencia NUMERIC(10,2) DEFAULT 0.00"))
            conn.commit()

        # Asignar clave temporal limpia a usuarios existentes que requieran cambio y no tengan clave almacenada
        sin_pass = Usuario.query.filter(
            Usuario.debe_cambiar_password == True,
            (Usuario.password_temporal_plana == None) | (Usuario.password_temporal_plana == '')
        ).all()
        if sin_pass:
            import random
            for u in sin_pass:
                nueva_temp = f"Cliente{random.randint(1000, 9999)}"
                u.set_password(nueva_temp)
        # Asignar fecha de creación a categorías existentes que tengan created_at nulo
        from models.categoria import Categoria
        from datetime import datetime, UTC
        cats_sin_fecha = Categoria.query.filter(Categoria.created_at == None).all()
        if cats_sin_fecha:
            for cat in cats_sin_fecha:
                cat.created_at = datetime.now(UTC)
            db.session.commit()

        # Sembrar Bancos por defecto si no existen
        bancos_defecto = ["BAC Credomatic", "Banco Lafise Bancentro", "Banpro Grupo Promerica", "BDF (Banco de Finanzas)", "Ficohsa"]
        for b_nom in bancos_defecto:
            b_exist = Banco.query.filter_by(nombre=b_nom).first()
            if not b_exist:
                db.session.add(Banco(nombre=b_nom, estado="ACTIVO"))
        db.session.commit()
    except Exception as e:
        print("Migración interna usuarios e inicialización bancos info:", e)

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
app.register_blueprint(proveedores_bp)
app.register_blueprint(perfil_bp)
# app.register_blueprint(usuarios_bp)
# app.register_blueprint(roles_bp)
app.register_blueprint(reportes_bp)
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
    clientes_activos = Cliente.query.filter_by(estado=EstadoCliente.ACTIVO).count()
    clientes_inactivos = Cliente.query.filter_by(estado=EstadoCliente.INACTIVO).count()
    clientes_pct = round((clientes_activos / clientes_total) * 100) if clientes_total else 0

    proveedores_total = Proveedor.query.count()
    proveedores_activos = Proveedor.query.filter_by(estado=EstadoProveedor.ACTIVO).count()
    proveedores_inactivos = Proveedor.query.filter_by(estado=EstadoProveedor.INACTIVO).count()

    productos_total = Producto.query.count()
    productos_stock_normal = Producto.query.filter(
        Producto.estado == EstadoProducto.ACTIVO,
        Producto.stock > 5
    ).count()
    productos_stock_critico = Producto.query.filter(
        Producto.estado == EstadoProducto.ACTIVO,
        Producto.stock > 0,
        Producto.stock <= 5
    ).count()
    productos_pct = round((productos_stock_normal / productos_total) * 100) if productos_total else 0

    ventas_activas = Venta.query.filter_by(estado=EstadoVenta.ACTIVA).options(
        joinedload(Venta.pagos),
        joinedload(Venta.cliente)
    ).all()
    facturas_total = len(ventas_activas)
    facturas_contado = len([v for v in ventas_activas if (v.tipo_venta == TipoVenta.CONTADO or (hasattr(v.tipo_venta, 'value') and v.tipo_venta.value == 'CONTADO') or str(v.tipo_venta) == 'CONTADO')])
    facturas_credito = len([v for v in ventas_activas if (v.tipo_venta == TipoVenta.CREDITO or (hasattr(v.tipo_venta, 'value') and v.tipo_venta.value == 'CREDITO') or str(v.tipo_venta) == 'CREDITO')])
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

        if venta.tipo_venta == TipoVenta.CONTADO:
            fecha_cobro = venta.fecha_venta.date()
        else:
            fecha_cobro = venta.fecha_limite_credito or venta.fecha_venta.date()

        if fecha_cobro <= hoy:
            dias_mora = (hoy - fecha_cobro).days
            clientes_a_cobrar.append({
                "cliente": f"{venta.cliente.nombres}".strip(),
                "estado": "Moroso" if dias_mora > 0 else "Cobrar hoy",
                "dias": dias_mora,
            })

    clientes_a_cobrar.sort(key=lambda item: item["dias"], reverse=True)

    pagos_pct = round((pagos_pagado_monto / pagos_total_monto) * 100) if pagos_total_monto else 0

    # Ventas del mes actual (Contado vs Crédito)
    ventas_mes_actual = [v for v in ventas_activas if v.fecha_venta.month == hoy.month and v.fecha_venta.year == hoy.year]
    total_mes_actual = sum(float(v.total_venta) for v in ventas_mes_actual)
    total_mes_contado = sum(
        float(v.total_venta) for v in ventas_mes_actual 
        if v.tipo_venta == TipoVenta.CONTADO or (hasattr(v.tipo_venta, 'value') and v.tipo_venta.value == 'CONTADO') or str(v.tipo_venta) == 'CONTADO'
    )
    total_mes_credito = sum(
        float(v.total_venta) for v in ventas_mes_actual 
        if v.tipo_venta == TipoVenta.CREDITO or (hasattr(v.tipo_venta, 'value') and v.tipo_venta.value == 'CREDITO') or str(v.tipo_venta) == 'CREDITO'
    )
    pct_contado = round((total_mes_contado / total_mes_actual) * 100) if total_mes_actual > 0 else 0
    pct_credito = round((total_mes_credito / total_mes_actual) * 100) if total_mes_actual > 0 else 0
    
    ventas_mes_breakdown = {
        "total": total_mes_actual,
        "contado_monto": total_mes_contado,
        "credito_monto": total_mes_credito,
        "contado_pct": pct_contado,
        "credito_pct": pct_credito
    }

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
        "proveedores": {
            "total": proveedores_total,
            "izquierda_label": "Activos",
            "izquierda": proveedores_activos,
            "derecha_label": "Inactivos",
            "derecha": proveedores_inactivos,
        },
    }

    anio_actual = hoy.year
    meses_nombres_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    ventas_por_mes = []

    for mes_num in range(1, 13):
        total_mes = db.session.query(func.coalesce(func.sum(Venta.total_venta), 0)).filter(
            extract('year', Venta.fecha_venta) == anio_actual,
            extract('month', Venta.fecha_venta) == mes_num,
            Venta.estado == EstadoVenta.ACTIVA
        ).scalar()
        
        ventas_por_mes.append({
            "mes": meses_nombres_es[mes_num - 1],
            "total": float(total_mes or 0.0)
        })

    chart_data = {
        "crecimiento_anual": {
            "anio": anio_actual,
            "labels": [m["mes"] for m in ventas_por_mes],
            "values": [m["total"] for m in ventas_por_mes],
        },
        "recaudacion_mes": {
            "labels": ["Contado", "Crédito"],
            "values": [total_mes_contado, total_mes_credito]
        }
    }

    # Cálculo de Clientes Principales con Facturas a Crédito PENDIENTES (Saldo > 0)
    ventas_credito_pendientes = []
    for v in ventas_activas:
        es_credito = (v.tipo_venta == TipoVenta.CREDITO or (hasattr(v.tipo_venta, 'value') and v.tipo_venta.value == 'CREDITO') or str(v.tipo_venta) == 'CREDITO')
        if es_credito:
            total_v = float(v.total_venta)
            pagado_v = sum(float(pago.monto_pago) for pago in v.pagos if pago.estado == "ACTIVO")
            saldo_v = max(total_v - pagado_v, 0)
            if saldo_v > 0:
                ventas_credito_pendientes.append((v, saldo_v))

    total_facturas_credito_cant = len(ventas_credito_pendientes)

    clientes_credito_dict = {}
    for v, saldo_v in ventas_credito_pendientes:
        c_id = v.cliente_id
        c_nombre = f"{v.cliente.nombres}".strip() if (v.cliente and v.cliente.nombres) else f"Cliente #{c_id}"
        if c_id not in clientes_credito_dict:
            clientes_credito_dict[c_id] = {
                "nombre": c_nombre,
                "facturas_cant": 0,
                "monto_total": 0.0
            }
        clientes_credito_dict[c_id]["facturas_cant"] += 1
        clientes_credito_dict[c_id]["monto_total"] += saldo_v

    top_clientes_credito = list(clientes_credito_dict.values())
    top_clientes_credito.sort(key=lambda x: (x["facturas_cant"], x["monto_total"]), reverse=True)
    top_clientes_credito = top_clientes_credito[:5]

    for c in top_clientes_credito:
        c["porcentaje"] = round((c["facturas_cant"] / total_facturas_credito_cant) * 100) if total_facturas_credito_cant > 0 else 0

    return render_template(
        "dashboard.html",
        saludo=saludo,
        ahora=ahora,
        fecha_larga=ahora.strftime("%d/%m/%Y"),
        clientes_a_cobrar=clientes_a_cobrar,
        top_clientes_credito=top_clientes_credito,
        kpis=kpis,
        chart_data=chart_data,
        ventas_mes_breakdown=ventas_mes_breakdown
    )




# MANEJADORES DE ERRORES PERSONALIZADOS (APEX DARK)

@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def error_interno_servidor(e):
    return render_template("errors/500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)