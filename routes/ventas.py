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

# Servicios
from services.venta_service import generar_numero_factura, crear_venta

# Fechas
from datetime import datetime, date

# BLUEPRINT
ventas_bp = Blueprint("ventas", __name__)

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
@login_required
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
        data = request.get_json()
        descuento_maximo = float(current_user.rol.descuento_maximo or 0)
        
        # Delegar toda la lógica al servicio transaccional
        exito, resultado = crear_venta(data, current_user.id, descuento_maximo)
        
        if exito:
            return jsonify({
                "success": True, 
                "message": resultado["mensaje"], 
                "venta_id": resultado["venta_id"]
            })
        else:
            return jsonify({
                "success": False, 
                "message": resultado
            })
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Error inesperado: {str(e)}"})