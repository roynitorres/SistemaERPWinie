from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from database import db
from models.venta import Venta
from models.detalle_venta import DetalleVenta
from models.producto import Producto
from models.cliente import Cliente
from models.pago import Pago
from models.enums import EstadoVenta, TipoVenta
from datetime import datetime, timedelta
from sqlalchemy import extract, func

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")

@reportes_bp.route("/financiero")
@login_required
def financiero():
    # Obtener meses únicos con actividad
    meses_ventas = db.session.query(Venta.fecha_venta).all()
    meses_pagos = db.session.query(Pago.fecha_pago).all()
    meses_compras = db.session.query(Producto.fecha_compra).all()
    
    meses_set = set()
    for (fecha,) in meses_ventas:
        if fecha: meses_set.add(fecha.strftime('%Y-%m'))
    for (fecha,) in meses_pagos:
        if fecha: meses_set.add(fecha.strftime('%Y-%m'))
    for (fecha,) in meses_compras:
        if fecha: meses_set.add(fecha.strftime('%Y-%m'))
        
    meses_disponibles = sorted(list(meses_set), reverse=True)
    if not meses_disponibles:
        meses_disponibles = [datetime.now().strftime('%Y-%m')]

    meses_nombres = {
        "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr",
        "05": "May", "06": "Jun", "07": "Jul", "08": "Ago",
        "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic"
    }
    
    meses_formateados = []
    for m in meses_disponibles:
        try:
            anio, mes = m.split("-")
            meses_formateados.append({
                "valor": m,
                "texto": f"{meses_nombres.get(mes, mes)} {anio}"
            })
        except:
            pass

    return render_template(
        "reportes/financiero.html",
        meses=meses_formateados
    )

@reportes_bp.route("/api/datos")
@login_required
def api_datos():
    mes_str = request.args.get('mes', datetime.now().strftime('%Y-%m'))
    try:
        anio, mes = map(int, mes_str.split('-'))
    except:
        anio, mes = datetime.now().year, datetime.now().month

    # 1. CLIENTES NUEVOS DEL MES
    clientes_nuevos_query = Cliente.query.filter(
        extract('year', Cliente.created_at) == anio,
        extract('month', Cliente.created_at) == mes
    ).all()
    clientes_nuevos = len(clientes_nuevos_query)
    lista_clientes_nuevos = [{
        "nombre": f"{c.nombres}",
        "telefono": c.telefono,
        "fecha": c.created_at.strftime('%d/%m/%Y') if c.created_at else ""
    } for c in clientes_nuevos_query]

    # 2. COMPRAS (Inversión)
    productos_comprados_mes = Producto.query.filter(
        extract('year', Producto.fecha_compra) == anio,
        extract('month', Producto.fecha_compra) == mes
    ).all()
    
    inversion_compra = sum(float(p.cantidad_comprada) * float(p.precio_compra) for p in productos_comprados_mes)
    proyeccion_venta = sum(float(p.cantidad_comprada) * float(p.precio_venta) for p in productos_comprados_mes)
    ganancia_compras = proyeccion_venta - inversion_compra

    lista_compras = [{
        "codigo": p.codigo_producto,
        "nombre": p.nombre,
        "cantidad": p.cantidad_comprada,
        "precio_compra": float(p.precio_compra),
        "precio_venta": float(p.precio_venta),
        "inversion": float(p.cantidad_comprada) * float(p.precio_compra),
        "proyeccion": float(p.cantidad_comprada) * float(p.precio_venta)
    } for p in productos_comprados_mes]

    # 3. PAGOS (Flujo de Caja)
    pagos_mes = Pago.query.filter(
        extract('year', Pago.fecha_pago) == anio,
        extract('month', Pago.fecha_pago) == mes,
        Pago.estado == 'ACTIVO'
    ).all()
    total_abonos = sum(float(p.monto_pago) for p in pagos_mes)
    
    lista_abonos = [{
        "factura": p.venta.numero_factura if p.venta else "-",
        "cliente": f"{p.venta.cliente.nombres}" if p.venta and p.venta.cliente else "-",
        "monto": float(p.monto_pago),
        "fecha": p.fecha_pago.strftime('%d/%m/%Y') if p.fecha_pago else ""
    } for p in pagos_mes]
    
    ventas_mes = Venta.query.filter(
        extract('year', Venta.fecha_venta) == anio,
        extract('month', Venta.fecha_venta) == mes,
        Venta.estado == EstadoVenta.ACTIVA
    ).all()
    
    total_facturado_mes = sum(float(v.total_venta) for v in ventas_mes)
    
    pendiente_mes = 0.0
    lista_pendientes = []
    for v in ventas_mes:
        abonos_venta = sum(float(p.monto_pago) for p in v.pagos if p.estado == 'ACTIVO')
        pendiente = float(v.total_venta) - abonos_venta
        pendiente_mes += pendiente
        if pendiente > 0:
            lista_pendientes.append({
                "factura": v.numero_factura,
                "cliente": f"{v.cliente.nombres}" if v.cliente else "-",
                "total": float(v.total_venta),
                "pendiente": pendiente,
                "fecha": v.fecha_venta.strftime('%d/%m/%Y') if v.fecha_venta else ""
            })
        
    # 4. VENTAS
    ventas_contado = sum(float(v.total_venta) for v in ventas_mes if v.tipo_venta == TipoVenta.CONTADO)
    ventas_credito = sum(float(v.total_venta) for v in ventas_mes if v.tipo_venta == TipoVenta.CREDITO)
    
    lista_ventas = [{
        "factura": v.numero_factura,
        "cliente": f"{v.cliente.nombres}",
        "tipo": v.tipo_venta.value,
        "total": float(v.total_venta),
        "fecha": v.fecha_venta.strftime('%d/%m/%Y') if v.fecha_venta else ""
    } for v in ventas_mes]

    # 5. RENDIMIENTO DE PRODUCTOS
    productos_vendidos_dict = {}
    for venta in ventas_mes:
        for detalle in venta.detalle_ventas:
            prod_id = detalle.producto_id
            cantidad = float(detalle.cantidad)
            if prod_id not in productos_vendidos_dict:
                productos_vendidos_dict[prod_id] = {
                    "nombre": detalle.producto.nombre if detalle.producto else "-",
                    "cantidad": 0,
                    "detalles": []
                }
            productos_vendidos_dict[prod_id]["cantidad"] += cantidad
            productos_vendidos_dict[prod_id]["detalles"].append({
                "cliente": f"{venta.cliente.nombres}" if venta.cliente else "-",
                "factura": venta.numero_factura,
                "fecha": venta.fecha_venta.strftime('%d/%m/%Y') if venta.fecha_venta else "",
                "cantidad": cantidad
            })
            
    producto_mas_vendido = {"nombre": "-", "cantidad": 0, "detalles": []}
    producto_menos_vendido = {"nombre": "-", "cantidad": 0, "detalles": []}
    
    if productos_vendidos_dict:
        ordenados = sorted(productos_vendidos_dict.values(), key=lambda x: x["cantidad"])
        producto_menos_vendido = ordenados[0]
        producto_mas_vendido = ordenados[-1]

    # 6. INVENTARIO ESTANCADO (> 30 dias)
    hoy = datetime.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    
    productos_activos = Producto.query.filter(Producto.estado == 'ACTIVO', Producto.stock > 0).all()
    estancados = []
    
    total_cantidad_estancada = 0
    total_valor_estancado = 0.0
    
    for p in productos_activos:
        if p.fecha_compra and p.fecha_compra < hace_30_dias:
            dias_estancado = (hoy - p.fecha_compra).days
            estancados.append({
                "codigo": p.codigo_producto,
                "nombre": p.nombre,
                "cantidad": p.stock,
                "precio": float(p.precio_compra),
                "fecha_compra": p.fecha_compra.strftime('%d/%m/%Y'),
                "dias": dias_estancado
            })
            total_cantidad_estancada += p.stock
            total_valor_estancado += (p.stock * float(p.precio_compra))
            
    estancados = sorted(estancados, key=lambda x: x["dias"], reverse=True)

    return jsonify({
        "clientes_nuevos": clientes_nuevos,
        "lista_clientes_nuevos": lista_clientes_nuevos,
        "ventas": {
            "contado": ventas_contado,
            "credito": ventas_credito,
            "total": total_facturado_mes,
            "lista": lista_ventas
        },
        "compras": {
            "inversion": inversion_compra,
            "proyeccion_venta": proyeccion_venta,
            "ganancia": ganancia_compras,
            "lista": lista_compras
        },
        "pagos": {
            "abonos": total_abonos,
            "pendiente": pendiente_mes,
            "total_mes": total_facturado_mes,
            "lista_abonos": lista_abonos,
            "lista_pendientes": lista_pendientes
        },
        "rendimiento": {
            "mas_vendido": producto_mas_vendido,
            "menos_vendido": producto_menos_vendido
        },
        "inventario_estancado": {
            "lista": estancados,
            "totales": {
                "cantidad": total_cantidad_estancada,
                "valor": total_valor_estancado
            }
        }
    })
