import json
from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask import jsonify
from sqlalchemy import or_

from flask_login import login_required
from flask_login import current_user

from database import db

# Modelos
from models.venta import Venta
from models.detalle_venta import DetalleVenta
from models.producto import Producto
from models.cliente import Cliente
from models.empresa import Empresa
from utils.permisos import roles_required
# Fechas
from datetime import datetime, date

# BLUEPRINT
ventas_bp = Blueprint("ventas", __name__)

# ==================================================
# GENERAR NÚMERO FACTURA
# ==================================================

def generar_numero_factura():
    empresa = Empresa.query.first()

    serie = "F001"
    correlativo_base = "00001"

    if empresa:
        serie = empresa.serie_factura or "F001"
        correlativo_base = empresa.correlativo or "00001"

    ultima_venta = Venta.query.order_by(Venta.id.desc()).first()

    if not ultima_venta:
        return f"{serie}-{correlativo_base}"

    try:
        ultimo_correlativo = int(ultima_venta.numero_factura.split("-")[1])
    except Exception:
        ultimo_correlativo = int(correlativo_base)

    nuevo_correlativo = ultimo_correlativo + 1

    return f"{serie}-{nuevo_correlativo:05d}"

# ==================================================
# VISTA NUEVA VENTA
# ==================================================
@ventas_bp.route("/ventas",methods=["GET"])
@login_required
@roles_required("ADMIN", "VENDEDOR")
def ventas():
    clientes = Cliente.query.order_by(Cliente.nombres.asc()).all()
    productos = Producto.query.filter(Producto.stock > 0).all()
    numero_factura = generar_numero_factura()
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    empresa = Empresa.query.first()
    descuento_maximo = float(current_user.rol.descuento_maximo or 0)
    return render_template(
        "ventas/ventas.html",
        clientes=clientes,
        productos=productos,
        numero_factura=numero_factura,
        fecha_actual=fecha_actual,
        descuento_maximo=descuento_maximo,
        empresa=empresa
    )


# BUSCAR PRODUCTOS AJAX
@ventas_bp.route("/buscar-productos")
def buscar_productos():
    busqueda = request.args.get("busqueda","").strip()
    if not busqueda:
        return jsonify([])
    productos = Producto.query.filter(
        Producto.stock > 0,
        or_(
            Producto.codigo_producto.ilike(f"%{busqueda}%"),
            Producto.marca.ilike(f"%{busqueda}%"),
            Producto.nombre.ilike(f"%{busqueda}%")
        ),
    ).all()

    resultado = []
    for producto in productos:
        resultado.append({
            "id":producto.id,
            "codigo":producto.codigo_producto,
            "nombre":producto.nombre,
            "marca":producto.marca,
            "categoria":producto.categoria.nombre,
            "precio":float(producto.precio_venta),
            "unidad":producto.unidad,
            "stock":producto.stock
        })
    return jsonify(resultado)

# ==================================================
# GUARDAR VENTA
# ==================================================

@ventas_bp.route("/guardar-venta",methods=["POST"])
@login_required
@roles_required("ADMIN", "VENDEDOR")
def guardar_venta():
    try:
        # OBTENER JSON
        data = request.get_json()
        # DATOS PRINCIPALES
        cliente_id = data.get("cliente_id")
        tipo_venta = data.get("tipo_venta")
        observaciones = data.get("observaciones")
        productos = data.get("productos")
        fecha_venta = data.get("fecha_venta")
        fecha_limite_credito = data.get("fecha_limite_credito")
        # VALIDACIONES
        if not cliente_id:
            return jsonify({"success": False,"message":"Seleccione un cliente"})
        if not productos:
            return jsonify({"success": False,"message":"Agregue productos"})
        
        # CALCULAR TOTAL
        descuento_maximo = float(current_user.rol.descuento_maximo or 0)

        subtotal = 0
        
        for item in productos:
            cantidad = int(item["cantidad"])
            precio = float(item["precio"])
            descuento_porcentaje = float(item.get("descuento_porcentaje", 0))
        
            if descuento_porcentaje < 0:
                return jsonify({
                    "success": False,
                    "message": "El descuento no puede ser negativo"
                })
        
            if descuento_porcentaje > descuento_maximo:
                return jsonify({
                    "success": False,
                    "message": f"Su rol permite máximo {descuento_maximo}% de descuento"
                })
        
            bruto = cantidad * precio
            descuento_monto = bruto * (descuento_porcentaje / 100)
            subtotal += bruto - descuento_monto
        
        empresa = Empresa.query.first()
        iva_porcentaje = float(empresa.iva) if empresa else 15
        iva = subtotal * (iva_porcentaje / 100)
        total = subtotal + iva
        
        # CREAR VENTA
        nueva_venta = Venta(
            numero_factura=generar_numero_factura(),
            cliente_id=cliente_id,
            usuario_id=current_user.id,
            fecha_venta=datetime.strptime(fecha_venta, "%Y-%m-%d") if fecha_venta else datetime.now(),
            fecha_limite_credito=datetime.strptime(fecha_limite_credito, "%Y-%m-%d").date() if fecha_limite_credito else None,
            tipo_venta=tipo_venta,
            total_venta=total,
            observaciones=observaciones
        )
        
        # GUARDAR VENTA
        db.session.add(nueva_venta)
        db.session.flush()
        # RECORRER PRODUCTO
        for item in productos:
            producto = Producto.query.get(item["producto_id"])
            # VALIDAR STOCK
            if not producto:
                return jsonify({"success": False,"message":"Producto no encontrado"})
            if cantidad > producto.stock:
                return jsonify({"success": False,"message":f"Stock insuficiente para {producto.nombre}"})
            # DETALLE VENTA
            cantidad = int(item["cantidad"])
            precio = float(item["precio"])
            descuento_porcentaje = float(item.get("descuento_porcentaje", 0))
            
            bruto = cantidad * precio
            descuento_monto = bruto * (descuento_porcentaje / 100)
            subtotal_item = bruto - descuento_monto
            
            detalle = DetalleVenta(
                venta_id=nueva_venta.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=precio,
                descuento_porcentaje=descuento_porcentaje,
                descuento_monto=descuento_monto,
                subtotal=subtotal_item
            )
            db.session.add(detalle)
            # DESCONTAR STOCK
            producto.stock -= cantidad
        db.session.commit()

        # RESPUESTA
        return jsonify({"success": True,"message":"Venta guardada correctamente","venta_id":nueva_venta.id })

    # ERROR
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False,"message": str(e)})
    

# ==================================================
# FACTURA
# ==================================================
@ventas_bp.route("/factura/<int:venta_id>")
@login_required
def factura(venta_id):
    
    # BUSCAR VENTA
    venta = Venta.query.get_or_404(venta_id)
    empresa = Empresa.query.first()
    # MOSTRAR FACTURA
    
    return render_template(
        "ventas/factura.html",
        venta=venta,
        empresa=empresa
    )
# ==================================================
# ANULAR FACTURA
# ==================================================

@ventas_bp.route("/anular-venta/<int:venta_id>", methods=["POST"])
@login_required
@roles_required("ADMIN")
def anular_venta(venta_id):
    venta = Venta.query.get_or_404(venta_id)

    if venta.estado == "ANULADA":
        flash("La factura ya está anulada", "warning")
        return redirect(url_for("ventas.historial_ventas"))

    for detalle in venta.detalle_ventas:
        detalle.producto.stock += detalle.cantidad

    venta.estado = "ANULADA"
    db.session.commit()

    flash("Factura anulada correctamente", "success")
    return redirect(url_for("ventas.historial_ventas"))
# ==============================================
# BUSQUEDA
# ==============================================

@ventas_bp.route("/historial-ventas")
@login_required
def historial_ventas():
    busqueda = request.args.get("busqueda", "").strip()
    estado = request.args.get("estado", "TODAS")
    fecha_inicio = request.args.get("fecha_inicio", "")
    fecha_fin = request.args.get("fecha_fin", "")
    cliente_id = request.args.get("cliente_id", "")

    query = Venta.query

    if busqueda:
        query = query.join(Cliente).filter(
            db.or_(
                Venta.numero_factura.ilike(f"%{busqueda}%"),
                Cliente.nombres.ilike(f"%{busqueda}%"),
                Cliente.apellidos.ilike(f"%{busqueda}%")
            )
        )

    if estado != "TODAS":
        query = query.filter(Venta.estado == estado)

    if cliente_id:
        query = query.filter(Venta.cliente_id == cliente_id)

    if fecha_inicio:
        query = query.filter(Venta.fecha_venta >= datetime.strptime(fecha_inicio, "%Y-%m-%d"))

    if fecha_fin:
        query = query.filter(Venta.fecha_venta <= datetime.strptime(fecha_fin, "%Y-%m-%d"))

    ventas = query.order_by(Venta.fecha_venta.desc()).all()
    clientes = Cliente.query.order_by(Cliente.nombres.asc()).all()

    facturas_activas = len([v for v in ventas if v.estado == "ACTIVA"])
    facturas_anuladas = len([v for v in ventas if v.estado == "ANULADA"])
    facturas_credito = len([v for v in ventas if v.tipo_venta == "CREDITO"])
    facturas_contado = len([v for v in ventas if v.tipo_venta == "CONTADO"])
    total_facturas = len(ventas)
    
    kpis = {
        "facturas_activas": facturas_activas,
        "facturas_anuladas": facturas_anuladas,
        "facturas_credito": facturas_credito,
        "facturas_contado": facturas_contado,
        "total_facturas": total_facturas
    }

    return render_template(
        "ventas/historial_ventas.html",
        ventas=ventas,
        clientes=clientes,
        kpis=kpis,
        busqueda=busqueda,
        estado_actual=estado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        cliente_id=cliente_id,
        hoy=date.today()
    )


@ventas_bp.route("/vista-previa-factura")
@login_required
def vista_previa_factura():
    empresa = Empresa.query.first()

    return render_template(
        "ventas/vista_previa_factura.html",
        empresa=empresa
    )