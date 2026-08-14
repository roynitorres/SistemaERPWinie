from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from database import db
from models.venta import Venta
from models.detalle_venta import DetalleVenta
from models.producto import Producto
from models.cliente import Cliente
from models.pago import Pago
from models.proveedor import Proveedor
from models.enums import EstadoVenta, TipoVenta
from datetime import datetime, timedelta
from sqlalchemy import extract, func

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")

@reportes_bp.route("/financiero")
@login_required
def financiero():
    # Obtener meses únicos con actividad
    meses_ventas  = db.session.query(Venta.fecha_venta).all()
    meses_pagos   = db.session.query(Pago.fecha_pago).all()
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

    return render_template("reportes/financiero.html", meses=meses_formateados)


@reportes_bp.route("/api/datos")
@login_required
def api_datos():
    mes_str = request.args.get('mes', datetime.now().strftime('%Y-%m'))
    try:
        anio, mes = map(int, mes_str.split('-'))
    except:
        anio, mes = datetime.now().year, datetime.now().month

    # ──────────────────────────────────────────────
    # 1. VENTAS DEL MES
    # ──────────────────────────────────────────────
    ventas_mes = Venta.query.filter(
        extract('year',  Venta.fecha_venta) == anio,
        extract('month', Venta.fecha_venta) == mes,
        Venta.estado == EstadoVenta.ACTIVA
    ).all()

    total_facturado_mes = sum(float(v.total_venta) for v in ventas_mes)
    ventas_contado_total = sum(float(v.total_venta) for v in ventas_mes if v.tipo_venta == TipoVenta.CONTADO)
    ventas_credito_total = sum(float(v.total_venta) for v in ventas_mes if v.tipo_venta == TipoVenta.CREDITO)

    lista_ventas_todas = [{
        "factura":  v.numero_factura,
        "cliente":  f"{v.cliente.nombres}" if v.cliente else "-",
        "tipo":     v.tipo_venta.value,
        "cantidad": sum(float(d.cantidad) for d in v.detalle_ventas),
        "total":    float(v.total_venta),
        "fecha":    v.fecha_venta.strftime('%d/%m/%Y') if v.fecha_venta else ""
    } for v in ventas_mes]

    lista_ventas_contado = [x for x in lista_ventas_todas if x["tipo"] == "CONTADO"]
    lista_ventas_credito = [x for x in lista_ventas_todas if x["tipo"] == "CREDITO"]

    # ──────────────────────────────────────────────
    # 2. MEJORES CLIENTES DEL MES
    # ──────────────────────────────────────────────
    clientes_monto = {}
    for v in ventas_mes:
        if v.cliente:
            cid = v.cliente_id
            if cid not in clientes_monto:
                clientes_monto[cid] = {
                    "nombre": v.cliente.nombres,
                    "telefono": v.cliente.telefono or "-",
                    "total":  0.0,
                    "cantidad_compras": 0
                }
            clientes_monto[cid]["total"] += float(v.total_venta)
            clientes_monto[cid]["cantidad_compras"] += 1

    mejores_clientes = sorted(clientes_monto.values(), key=lambda x: x["total"], reverse=True)
    total_ventas_clientes = sum(c["total"] for c in mejores_clientes)

    # ──────────────────────────────────────────────
    # 3. CLIENTES NUEVOS DEL MES
    # ──────────────────────────────────────────────
    clientes_nuevos_query = Cliente.query.filter(
        extract('year',  Cliente.created_at) == anio,
        extract('month', Cliente.created_at) == mes
    ).all()
    lista_clientes_nuevos = [{
        "nombre":   c.nombres,
        "telefono": c.telefono or "-",
        "fecha":    c.created_at.strftime('%d/%m/%Y') if c.created_at else ""
    } for c in clientes_nuevos_query]

    # ──────────────────────────────────────────────
    # 4. PRODUCTOS MÁS VENDIDOS
    # ──────────────────────────────────────────────
    productos_vendidos_dict = {}
    for venta in ventas_mes:
        for detalle in venta.detalle_ventas:
            prod_id = detalle.producto_id
            cantidad = float(detalle.cantidad)
            precio_venta = float(detalle.precio_unitario) if detalle.precio_unitario else 0.0
            subtotal = cantidad * precio_venta

            prov_nombre = "-"
            if detalle.producto and detalle.producto.proveedor:
                prov_nombre = detalle.producto.proveedor.nombre_proveedor

            if prod_id not in productos_vendidos_dict:
                productos_vendidos_dict[prod_id] = {
                    "nombre":       detalle.producto.nombre if detalle.producto else "-",
                    "proveedor":    prov_nombre,
                    "precio_venta": precio_venta,
                    "cantidad":     0.0,
                    "subtotal":     0.0,
                    "clientes":     []
                }
            productos_vendidos_dict[prod_id]["cantidad"] += cantidad
            productos_vendidos_dict[prod_id]["subtotal"] += subtotal

            nombre_cliente = f"{venta.cliente.nombres}" if venta.cliente else "-"
            # Agrupa por cliente dentro del mismo producto
            cliente_entry = next(
                (c for c in productos_vendidos_dict[prod_id]["clientes"] if c["nombre"] == nombre_cliente),
                None
            )
            if cliente_entry:
                cliente_entry["cantidad"] += cantidad
            else:
                productos_vendidos_dict[prod_id]["clientes"].append({
                    "nombre":   nombre_cliente,
                    "cantidad": cantidad
                })

    lista_productos_mas_vendidos = sorted(
        productos_vendidos_dict.values(), key=lambda x: x["cantidad"], reverse=True
    )
    total_unidades_vendidas = sum(p["cantidad"] for p in lista_productos_mas_vendidos)
    total_ingresos_productos = sum(p["subtotal"] for p in lista_productos_mas_vendidos)

    producto_mas_vendido  = lista_productos_mas_vendidos[0]  if lista_productos_mas_vendidos else {"nombre": "-", "cantidad": 0, "detalles": []}
    producto_menos_vendido = lista_productos_mas_vendidos[-1] if lista_productos_mas_vendidos else {"nombre": "-", "cantidad": 0, "detalles": []}

    # ──────────────────────────────────────────────
    # 5. PROVEEDORES — productos comprados en el mes
    # ──────────────────────────────────────────────
    productos_comprados_mes = Producto.query.filter(
        extract('year',  Producto.fecha_compra) == anio,
        extract('month', Producto.fecha_compra) == mes
    ).order_by(Producto.fecha_compra.desc()).all()

    proveedores_dict = {}
    for p in productos_comprados_mes:
        prov_id = p.proveedor_id
        if prov_id not in proveedores_dict:
            nombre_prov = p.proveedor.nombre_proveedor if p.proveedor else "-"
            proveedores_dict[prov_id] = {
                "nombre":    nombre_prov,
                "productos": [],
                "monto_total": 0.0
            }
        monto_producto = float(p.cantidad_comprada) * float(p.precio_compra)
        proveedores_dict[prov_id]["productos"].append({
            "nombre":       p.nombre,
            "cantidad":     p.cantidad_comprada,
            "precio_compra": float(p.precio_compra),
            "monto":        monto_producto
        })
        proveedores_dict[prov_id]["monto_total"] += monto_producto

    lista_proveedores = sorted(proveedores_dict.values(), key=lambda x: x["monto_total"], reverse=True)
    total_compras_proveedores = sum(pv["monto_total"] for pv in lista_proveedores)

    inversion_compra  = sum(float(p.cantidad_comprada) * float(p.precio_compra) for p in productos_comprados_mes)
    proyeccion_venta  = sum(float(p.cantidad_comprada) * float(p.precio_venta)  for p in productos_comprados_mes)

    lista_compras = [{
        "codigo":       p.codigo_producto,
        "nombre":       p.nombre,
        "proveedor":    p.proveedor.nombre_proveedor if p.proveedor else "-",
        "cantidad":     p.cantidad_comprada,
        "precio_compra": float(p.precio_compra),
        "precio_venta": float(p.precio_venta),
        "inversion":    float(p.cantidad_comprada) * float(p.precio_compra),
        "proyeccion":   float(p.cantidad_comprada) * float(p.precio_venta)
    } for p in productos_comprados_mes]

    # ──────────────────────────────────────────────
    # 6. PAGOS DEL MES (ORDENADOS POR FECHA MAYOR A MENOR)
    # ──────────────────────────────────────────────
    pagos_mes = Pago.query.filter(
        extract('year',  Pago.fecha_pago) == anio,
        extract('month', Pago.fecha_pago) == mes,
        Pago.estado == 'ACTIVO'
    ).order_by(Pago.fecha_pago.desc()).all()

    total_abonos = sum(float(p.monto_pago) for p in pagos_mes)

    lista_pagos_contado = []
    lista_pagos_credito = []
    total_pagos_contado = 0.0
    total_pagos_credito = 0.0

    for p in pagos_mes:
        tipo_venta = p.venta.tipo_venta.value if p.venta else "CONTADO"
        entrada = {
            "factura": p.venta.numero_factura if p.venta else "-",
            "cliente": f"{p.venta.cliente.nombres}" if p.venta and p.venta.cliente else "-",
            "monto":   float(p.monto_pago),
            "fecha":   p.fecha_pago.strftime('%d/%m/%Y') if p.fecha_pago else ""
        }
        if tipo_venta == "CONTADO":
            lista_pagos_contado.append(entrada)
            total_pagos_contado += float(p.monto_pago)
        else:
            lista_pagos_credito.append(entrada)
            total_pagos_credito += float(p.monto_pago)

    lista_abonos = [{
        "factura": p.venta.numero_factura if p.venta else "-",
        "cliente": f"{p.venta.cliente.nombres}" if p.venta and p.venta.cliente else "-",
        "monto":   float(p.monto_pago),
        "fecha":   p.fecha_pago.strftime('%d/%m/%Y') if p.fecha_pago else ""
    } for p in pagos_mes]

    # ──────────────────────────────────────────────
    # 7. PAGOS PENDIENTES
    # ──────────────────────────────────────────────
    pendiente_mes  = 0.0
    lista_pendientes = []
    for v in ventas_mes:
        abonos_venta = sum(float(p.monto_pago) for p in v.pagos if p.estado == 'ACTIVO')
        pendiente = float(v.total_venta) - abonos_venta
        pendiente_mes += pendiente
        if pendiente > 0:
            lista_pendientes.append({
                "factura":  v.numero_factura,
                "cliente":  f"{v.cliente.nombres}" if v.cliente else "-",
                "total":    float(v.total_venta),
                "abonado":  abonos_venta,
                "pendiente": pendiente,
                "fecha":    v.fecha_venta.strftime('%d/%m/%Y') if v.fecha_venta else ""
            })

    # ──────────────────────────────────────────────
    # 8. INVENTARIO ESTANCADO (> 30 días)
    # ──────────────────────────────────────────────
    hoy         = datetime.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    productos_activos = Producto.query.filter(Producto.estado == 'ACTIVO', Producto.stock > 0).all()

    estancados = []
    total_cantidad_estancada = 0
    total_valor_estancado    = 0.0

    for p in productos_activos:
        if p.fecha_compra and p.fecha_compra < hace_30_dias:
            dias_estancado = (hoy - p.fecha_compra).days
            estancados.append({
                "codigo":      p.codigo_producto,
                "nombre":      p.nombre,
                "cantidad":    p.stock,
                "precio":      float(p.precio_compra),
                "fecha_compra": p.fecha_compra.strftime('%d/%m/%Y'),
                "dias":        dias_estancado
            })
            total_cantidad_estancada += p.stock
            total_valor_estancado    += (p.stock * float(p.precio_compra))

    estancados = sorted(estancados, key=lambda x: x["dias"], reverse=True)

    # ──────────────────────────────────────────────
    # 9. RESUMEN FINANCIERO
    # ──────────────────────────────────────────────
    # Ganancia real = lo cobrado (abonos del mes) - inversión en compras del mes
    ganancia_aproximada = total_abonos - inversion_compra
    # Ganancia proyectada = proyección de venta total - inversión en compras
    ganancia_proyectada = proyeccion_venta - inversion_compra

    unidades_compradas_mes = sum(p.cantidad_comprada for p in productos_comprados_mes)

    return jsonify({
        # Ventas
        "ventas": {
            "contado":        ventas_contado_total,
            "credito":        ventas_credito_total,
            "conteo_contado": len(lista_ventas_contado),
            "conteo_credito": len(lista_ventas_credito),
            "total":          total_facturado_mes,
            "lista":          lista_ventas_todas,
            "lista_contado":  lista_ventas_contado,
            "lista_credito":  lista_ventas_credito,
        },
        # Clientes
        "mejores_clientes":      mejores_clientes,
        "top_cliente":           mejores_clientes[0] if mejores_clientes else None,
        "total_ventas_clientes": total_ventas_clientes,
        "clientes_nuevos":       len(lista_clientes_nuevos),
        "lista_clientes_nuevos": lista_clientes_nuevos,
        # Productos
        "productos_mas_vendidos": lista_productos_mas_vendidos,
        "total_unidades_vendidas": total_unidades_vendidas,
        "total_ingresos_productos": total_ingresos_productos,
        # Proveedores
        "proveedores": lista_proveedores,
        "total_compras_proveedores": total_compras_proveedores,
        # Compras (inventario comprado en el mes)
        "compras": {
            "unidades_compradas": unidades_compradas_mes,
            "inversion":        inversion_compra,
            "proyeccion_venta": proyeccion_venta,
            "ganancia":         proyeccion_venta - inversion_compra,
            "lista":            lista_compras
        },
        # Pagos
        "pagos": {
            "abonos":               total_abonos,
            "pendiente":            pendiente_mes,
            "total_mes":            total_facturado_mes,
            "lista_abonos":         lista_abonos,
            "lista_pendientes":      lista_pendientes,
            "lista_pagos_contado":  lista_pagos_contado,
            "lista_pagos_credito":  lista_pagos_credito,
            "total_pagos_contado":  total_pagos_contado,
            "total_pagos_credito":  total_pagos_credito,
            "conteo_pagos_contado": len(lista_pagos_contado),
            "conteo_pagos_credito": len(lista_pagos_credito),
        },
        # Rendimiento
        "rendimiento": {
            "mas_vendido":   producto_mas_vendido,
            "menos_vendido": producto_menos_vendido
        },
        # Inventario estancado
        "inventario_estancado": {
            "lista": estancados,
            "totales": {
                "cantidad": total_cantidad_estancada,
                "valor":    total_valor_estancado
            }
        },
        # Resumen financiero
        "resumen": {
            "inversion":           inversion_compra,
            "total_cobrado":       total_abonos,
            "pendiente":           pendiente_mes,
            "ganancia_real":       ganancia_aproximada,
            "ganancia_proyectada": ganancia_proyectada,
            "total_ventas":        total_facturado_mes,
        }
    })
