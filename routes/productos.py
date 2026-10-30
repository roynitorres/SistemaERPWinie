from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sqlalchemy.orm import joinedload
from utils.permisos import roles_required
from datetime import datetime, date

# Modelos
from models.producto import Producto
from models.categoria import Categoria
from models.proveedor import Proveedor
from models.enums import EstadoProducto
from services.producto_service import crear_o_actualizar_producto

#=======BLUEPRINT PRODUCTOS=========
productos_bp = Blueprint("productos", __name__)

# ==================================================
# 1. LISTADO / CATÁLOGO DE PRODUCTOS (VISTA PRINCIPAL)
# ==================================================
@productos_bp.route("/productos", methods=["GET"])
@login_required
@roles_required("ADMIN")
def productos():
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


# ==================================================
# 2. CREAR NUEVO PRODUCTO (PÁGINA DEDICADA)
# ==================================================
@productos_bp.route("/productos/nuevo", methods=["GET", "POST"])
@login_required
@roles_required("ADMIN")
def nuevo_producto():
    if request.method == "POST":
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
            stock_minimo = int(request.form.get("stock_minimo", 5))
            fecha_compra_str = request.form.get("fecha_compra")
            fecha_compra = datetime.strptime(fecha_compra_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            flash("Error en los formatos numéricos o de fecha", "danger")
            return redirect(url_for("productos.nuevo_producto"))

        exito, mensaje = crear_o_actualizar_producto(
            producto_id=None,
            codigo_producto=codigo_producto,
            nombre=nombre,
            marca=marca,
            estado=estado,
            categoria_id=categoria_id,
            proveedor_id=proveedor_id,
            precio_compra=precio_compra,
            precio_venta=precio_venta,
            cantidad_comprada=cantidad_comprada,
            fecha_compra=fecha_compra,
            stock_minimo=stock_minimo
        )

        if exito:
            flash(mensaje, "success")
            return redirect(url_for("productos.productos"))
        else:
            flash(mensaje, "danger")
            return redirect(url_for("productos.nuevo_producto"))

    categorias = Categoria.query.order_by(Categoria.nombre.asc()).all()
    proveedores = Proveedor.query.order_by(Proveedor.nombre_proveedor.asc()).all()
    fecha_hoy = date.today().strftime("%Y-%m-%d")

    return render_template(
        "productos/form_producto.html",
        producto=None,
        categorias=categorias,
        proveedores=proveedores,
        fecha_hoy=fecha_hoy
    )


# ==================================================
# 3. EDITAR PRODUCTO (PÁGINA DEDICADA)
# ==================================================
@productos_bp.route("/productos/editar/<int:id>", methods=["GET", "POST"])
@login_required
@roles_required("ADMIN")
def editar_producto(id):
    producto = Producto.query.get_or_404(id)

    if request.method == "POST":
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
            stock_minimo = int(request.form.get("stock_minimo", 5))
            fecha_compra_str = request.form.get("fecha_compra")
            fecha_compra = datetime.strptime(fecha_compra_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            flash("Error en los formatos numéricos o de fecha", "danger")
            return redirect(url_for("productos.editar_producto", id=id))

        exito, mensaje = crear_o_actualizar_producto(
            producto_id=id,
            codigo_producto=codigo_producto,
            nombre=nombre,
            marca=marca,
            estado=estado,
            categoria_id=categoria_id,
            proveedor_id=proveedor_id,
            precio_compra=precio_compra,
            precio_venta=precio_venta,
            cantidad_comprada=cantidad_comprada,
            fecha_compra=fecha_compra,
            stock_minimo=stock_minimo
        )

        if exito:
            flash(mensaje, "success")
            return redirect(url_for("productos.productos"))
        else:
            flash(mensaje, "danger")
            return redirect(url_for("productos.editar_producto", id=id))

    categorias = Categoria.query.order_by(Categoria.nombre.asc()).all()
    proveedores = Proveedor.query.order_by(Proveedor.nombre_proveedor.asc()).all()

    return render_template(
        "productos/form_producto.html",
        producto=producto,
        categorias=categorias,
        proveedores=proveedores,
        fecha_hoy=producto.fecha_compra.strftime("%Y-%m-%d") if producto.fecha_compra else date.today().strftime("%Y-%m-%d")
    )


# ==================================================
# 4. AUTOCOMPLETADO POR CÓDIGO (AJAX)
# ==================================================
@productos_bp.route("/buscar/<codigo>", methods=["GET"])
@login_required
def buscar_producto(codigo):
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
        "precio_venta": float(producto.precio_venta),
        "stock_minimo": getattr(producto, 'stock_minimo', 5)
    })
