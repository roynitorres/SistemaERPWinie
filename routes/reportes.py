from flask import Blueprint, render_template, request
from flask_login import login_required
from database import db
from models.venta import Venta
from models.detalle_venta import DetalleVenta
from models.producto import Producto
from models.cliente import Cliente
from models.pago import Pago
from datetime import datetime
from sqlalchemy import extract, func

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")

@reportes_bp.route("/financiero")
@login_required
def financiero():
    hoy = datetime.now()
    
    # Obtener mes y año de los parámetros GET, o usar el actual
    mes_str = request.args.get('mes')
    anio_str = request.args.get('anio')
    
    try:
        mes = int(mes_str) if mes_str else hoy.month
        anio = int(anio_str) if anio_str else hoy.year
    except ValueError:
        mes = hoy.month
        anio = hoy.year

    # Estructura de meses para el selector
    meses_nombres = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    # ==========================
    # 1. CLIENTES NUEVOS DEL MES
    # ==========================
    clientes_nuevos = Cliente.query.filter(
        extract('year', Cliente.created_at) == anio,
        extract('month', Cliente.created_at) == mes
    ).count()

    # ==========================
    # 2. INVERSIÓN (Ingreso de Productos)
    # ==========================
    productos_comprados_mes = Producto.query.filter(
        extract('year', Producto.fecha_compra) == anio,
        extract('month', Producto.fecha_compra) == mes
    ).all()
    inversion_mes = sum(float(p.cantidad_comprada) * float(p.precio_compra) for p in productos_comprados_mes)

    # ==========================
    # 3. PAGOS RECOGIDOS (Flujo de Caja Real)
    # ==========================
    pagos_mes = Pago.query.filter(
        extract('year', Pago.fecha_pago) == anio,
        extract('month', Pago.fecha_pago) == mes,
        Pago.estado == 'ACTIVO'
    ).all()
    pagos_recogidos = sum(float(p.monto_pago) for p in pagos_mes)

    # ==========================
    # 4. VENTAS, COSTOS Y GANANCIAS DEL MES
    # ==========================
    ventas_mes = Venta.query.filter(
        extract('year', Venta.fecha_venta) == anio,
        extract('month', Venta.fecha_venta) == mes,
        Venta.estado == 'ACTIVA'
    ).all()

    ventas_totales = 0.0
    costos_totales = 0.0

    # Para identificar productos vendidos en el mes
    productos_vendidos_dict = {}

    for venta in ventas_mes:
        ventas_totales += float(venta.total_venta)
        
        for detalle in venta.detalle_ventas:
            cantidad = float(detalle.cantidad)
            precio_compra = float(detalle.producto.precio_compra)
            costos_totales += (cantidad * precio_compra)

            # Rastrear cantidad vendida por producto
            prod_id = detalle.producto_id
            if prod_id not in productos_vendidos_dict:
                productos_vendidos_dict[prod_id] = {
                    "id": prod_id,
                    "nombre": detalle.producto.nombre,
                    "codigo": detalle.producto.codigo_producto,
                    "cantidad_vendida": 0
                }
            productos_vendidos_dict[prod_id]["cantidad_vendida"] += cantidad

    ganancia_aproximada = ventas_totales - costos_totales

    # ==========================
    # 5. RENDIMIENTO DE PRODUCTOS
    # ==========================
    producto_mas_vendido = None
    producto_menos_vendido = None
    
    if productos_vendidos_dict:
        # Ordenar lista por cantidad vendida
        productos_ordenados = sorted(productos_vendidos_dict.values(), key=lambda x: x["cantidad_vendida"], reverse=True)
        producto_mas_vendido = productos_ordenados[0]
        producto_menos_vendido = productos_ordenados[-1]

    # Productos Sin Movimiento (que están activos pero no se vendieron este mes)
    ids_vendidos = list(productos_vendidos_dict.keys())
    
    query_sin_movimiento = Producto.query.filter(Producto.estado == 'ACTIVO')
    if ids_vendidos:
        query_sin_movimiento = query_sin_movimiento.filter(~Producto.id.in_(ids_vendidos))
        
    productos_sin_movimiento = query_sin_movimiento.all()

    return render_template(
        "reportes/financiero.html",
        mes_actual=mes,
        anio_actual=anio,
        meses=meses_nombres,
        anios=range(hoy.year - 5, hoy.year + 2), # 5 años atrás y 1 adelante
        clientes_nuevos=clientes_nuevos,
        inversion_mes=inversion_mes,
        pagos_recogidos=pagos_recogidos,
        ventas_totales=ventas_totales,
        costos_totales=costos_totales,
        ganancia_aproximada=ganancia_aproximada,
        producto_mas_vendido=producto_mas_vendido,
        producto_menos_vendido=producto_menos_vendido,
        productos_sin_movimiento=productos_sin_movimiento
    )
