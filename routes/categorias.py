from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask_login import login_required
# Modelo
from models.categoria import Categoria
from models.producto import Producto
from utils.permisos import roles_required
# Base datos
from database import db

# BLUEPRINT

categorias_bp = Blueprint("categorias",__name__)

# ==================================================
# VISTA CATEGORÍAS
# ==================================================

@categorias_bp.route("/categorias",methods=["GET", "POST"])
@login_required
@roles_required("ADMIN")
def categorias():
    # GUARDAR / ACTUALIZAR
    if request.method == "POST":
        # OBTENER ID
        categoria_id = request.form.get("categoria_id")
        codigo = request.form.get("codigo_categoria")
        nombre = request.form.get("nombre").strip().title()
        descripcion = request.form.get("descripcion").strip().title()
        estado = request.form.get("estado") == "ACTIVO"
        # VALIDACIONES
        if not nombre:
            flash("El nombre es obligatorio","danger")
            return redirect(url_for("categorias.categorias"))
        # VALIDAR DUPLICADOS
        categoria_existente = Categoria.query.filter_by(nombre=nombre).first()
        if categoria_existente and (
            not categoria_id or
            categoria_existente.id != int(categoria_id)

        ):
            flash("La categoría ya existe","danger")
            return redirect(url_for("categorias.categorias"))
        # ACTUALIZAR
        if categoria_id:
            categoria = Categoria.query.get(categoria_id)
            categoria.codigo = codigo
            categoria.nombre = nombre
            categoria.descripcion = descripcion
            categoria.estado = estado
            mensaje = ("Categoría actualizada correctamente")
        # INSERTAR
        else:
            nueva_categoria = Categoria(
                 codigo=codigo,
                nombre=nombre,
                descripcion=descripcion,
                 estado=estado
            )
            db.session.add(nueva_categoria)
            mensaje = ("Categoría guardada correctamente")
        # GUARDAR CAMBIOS
        db.session.commit()
        flash(mensaje,"success")
        return redirect(url_for("categorias.categorias"))

    lista_categorias = Categoria.query.order_by(Categoria.id.asc()).all()
    #Calcular KPIS
    total_categorias = len(lista_categorias)
    activos = Categoria.query.filter_by(estado=True).count()
    cant_productos = Producto.query.order_by(Producto.id).all()
    total_productos = len(cant_productos)

    kpis ={
        "total":total_categorias,
        "activos":activos,
        "total_productos":total_productos
    }
    #Calculamos el ultimo codigo de categoria
    ultima_categoria = Categoria.query.order_by(Categoria.id.desc()).first()
    next_id =1 if not ultima_categoria else (ultima_categoria.id+1)
    siguiente_codigo = f"C{next_id:03d}"
    return render_template(
        "categorias/categorias.html",
        categorias=lista_categorias,
        kpis = kpis,
        siguiente_codigo = siguiente_codigo
    )