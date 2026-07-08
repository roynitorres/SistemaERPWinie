from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask_login import login_required
# Modelos
from models.producto import Producto
from models.categoria import Categoria
from utils.permisos import roles_required
# Base datos
from database import db
from datetime import datetime

#=======BLUEPRINT PRODUCTOS=========
productos_bp = Blueprint("productos",__name__)
# ==================================================
# VISTA PRODUCTOS
# ==================================================
@productos_bp.route("/productos",methods=["GET", "POST"])
@login_required
@roles_required("ADMIN")
def productos():

    # GUARDAR / ACTUALIZAR
    if request.method == "POST":
        # OBTENER ID
        producto_id = request.form.get("producto_id")
        # OBTENER DATOS
        codigo_producto = request.form.get("codigo_producto").strip().upper()
        nombre = request.form.get("nombre").strip().title()
        marca = request.form.get("marca").strip().title()
        unidad = request.form.get("unidad", "UND").strip().upper()
        estado = request.form.get("estado","ACTIVO")
        categoria_id = request.form.get("categoria_id")
        precio_compra = float(request.form.get("precio_compra"))
        precio_venta = float(request.form.get("precio_venta"))
        cantidad_comprada = int(request.form.get("cantidad_comprada"))
        stock = cantidad_comprada
        fecha_compra = request.form.get("fecha_compra")
        fecha_compra = datetime.strptime(fecha_compra,"%Y-%m-%d").date()

        # VALIDACIONES
        if not codigo_producto:
            flash("El código producto es obligatorio","danger")
            return redirect(url_for("productos.productos"))
        if not nombre:
            flash("El nombre es obligatorio","danger")
            return redirect(url_for("productos.productos"))
        if not marca:
            flash("La marca es obligatoria","danger")
            return redirect(url_for("productos.productos"))

        # ACTUALIZAR
        if producto_id:
            producto = Producto.query.get(producto_id)
            producto.codigo_producto = codigo_producto
            producto.nombre = nombre
            producto.marca = marca
            producto.unidad = unidad
            producto.estado = estado
            producto.categoria_id = categoria_id
            producto.precio_compra = precio_compra
            producto.precio_venta = precio_venta
            producto.stock = stock
            producto.cantidad_comprada = cantidad_comprada
            producto.fecha_compra = fecha_compra
            mensaje = "Producto actualizado correctamente"
        # INSERTAR
        else:
            nuevo_producto = Producto(
                codigo_producto=codigo_producto,
                nombre=nombre,
                marca=marca,
                unidad= unidad,
                estado= estado,
                categoria_id=categoria_id,
                precio_compra=precio_compra,
                precio_venta=precio_venta,
                stock=stock,
                cantidad_comprada=cantidad_comprada,    
                fecha_compra=fecha_compra
            )

            db.session.add(nuevo_producto)
            mensaje = "Producto guardado correctamente"
        
        # GUARDAR CAMBIO
        db.session.commit()
        flash(mensaje,"success")
        return redirect(url_for("productos.productos"))

    # ==============================================
    # LISTAR PRODUCTOS
    # ==============================================
    lista_productos = Producto.query.order_by(Producto.id.asc()).all()
    # Calcular KPIs
    total_productos = len(lista_productos)
    stock_normal = sum(1 for p in lista_productos if p.stock > 5)
    stock_critico = sum(1 for p in lista_productos if 1 <= p.stock <= 5)
    sin_stock = sum(1 for p in lista_productos if p.stock <= 0)
    valor_inventario = sum(float(p.precio_compra) * p.stock for p in lista_productos)
    kpis={
        "total": total_productos,
        "stock_normal": stock_normal,
        "stock_critico": stock_critico,
        "sin_stock": sin_stock,
        "valor_inventario": valor_inventario
    }
    #Calculamos el ultimo codigo de producto
    ultimo_producto = Producto.query.order_by(Producto.id.desc()).first()
    next_id = 1 if not ultimo_producto else (ultimo_producto.id + 1)
    siguiente_codigo = f"P{next_id:03d}"
    # LISTAR CATEGORÍAS
    categorias = Categoria.query.order_by(Categoria.nombre.asc()).all()
    # MOSTRAR VISTA AL HTML
    return render_template(
        "productos/productos.html",
        productos=lista_productos,
        kpis=kpis,
        categorias=categorias,
        siguiente_codigo=siguiente_codigo
    )