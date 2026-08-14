from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy.orm import joinedload
from utils.permisos import roles_required

# Modelos
from models.producto import Producto
from models.categoria import Categoria
from models.proveedor import Proveedor
from models.enums import EstadoProducto
from services.producto_service import crear_o_actualizar_producto

from datetime import datetime

#=======BLUEPRINT PRODUCTOS=========
productos_bp = Blueprint("productos", __name__)

# ==================================================
# VISTA PRODUCTOS
# ==================================================
@productos_bp.route("/productos", methods=["GET", "POST"])
@login_required
@roles_required("ADMIN")
def productos():
    # GUARDAR / ACTUALIZAR
    if request.method == "POST":
        producto_id = request.form.get("producto_id")
        codigo_producto = request.form.get("codigo_producto", "").strip().upper()
        nombre = request.form.get("nombre", "").strip().title()
        marca = request.form.get("marca", "").strip().title()
        estado_val = request.form.get("estado", "ACTIVO")
        estado = EstadoProducto(estado_val)
        categoria_id = request.form.get("categoria_id")
        proveedor_id = request.form.get("proveedor_id")
        
        try:
            precio_compra = float(request.form.get("precio_compra", 0))
            precio_venta = float(request.form.get("precio_venta", 0))
            cantidad_comprada = int(request.form.get("cantidad_comprada", 0))
            fecha_compra_str = request.form.get("fecha_compra")
            fecha_compra = datetime.strptime(fecha_compra_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            flash("Error en los formatos numéricos o de fecha", "danger")
            return redirect(url_for("productos.productos"))

        exito, mensaje = crear_o_actualizar_producto(
            producto_id=producto_id,
            codigo_producto=codigo_producto,
            nombre=nombre,
            marca=marca,
            estado=estado,
            categoria_id=categoria_id,
            proveedor_id=proveedor_id,
            precio_compra=precio_compra,
            precio_venta=precio_venta,
            cantidad_comprada=cantidad_comprada,
            fecha_compra=fecha_compra
        )

        if exito:
            flash(mensaje, "success")
        else:
            flash(mensaje, "danger")
            
        return redirect(url_for("productos.productos"))

    # ==============================================
    # LISTAR PRODUCTOS
    # ==============================================
    lista_productos = Producto.query.options(
        joinedload(Producto.categoria),
        joinedload(Producto.proveedor)
    ).order_by(Producto.id.desc()).all()

    categorias = Categoria.query.order_by(Categoria.nombre.asc()).all()
    proveedores = Proveedor.query.order_by(Proveedor.nombre_proveedor.asc()).all()

    return render_template(
        "productos/productos.html",
        productos=lista_productos,
        categorias=categorias,
        proveedores=proveedores
    )

@productos_bp.route("/buscar/<codigo>", methods=["GET"])
@login_required
def buscar_producto(codigo):
    from flask import jsonify
    # Buscar el último producto con este código
    producto = Producto.query.filter(Producto.codigo_producto.ilike(codigo)).order_by(Producto.fecha_compra.desc(), Producto.id.desc()).first()
    
    if not producto:
        return jsonify({"encontrado": False})
        
    return jsonify({
        "encontrado": True,
        "nombre": producto.nombre,
        "marca": producto.marca,
        "categoria_id": producto.categoria_id,
        "proveedor_id": producto.proveedor_id,
        "precio_compra": float(producto.precio_compra),
        "precio_venta": float(producto.precio_venta)
    })