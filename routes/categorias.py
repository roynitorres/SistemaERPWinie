from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from utils.permisos import roles_required

from models.categoria import Categoria
from models.enums import EstadoCategoria
from services.categoria_service import (
    crear_o_actualizar_categoria,
    generar_siguiente_codigo_categoria
)

# BLUEPRINT
categorias_bp = Blueprint("categorias", __name__)

# ==================================================
# VISTA CATEGORÍAS
# ==================================================

@categorias_bp.route("/categorias", methods=["GET", "POST"])
@login_required
@roles_required("ADMIN")
def categorias():
    # GUARDAR / ACTUALIZAR
    if request.method == "POST":
        categoria_id = request.form.get("categoria_id")
        codigo = request.form.get("codigo_categoria")
        nombre = request.form.get("nombre", "").strip().upper()
        descripcion = request.form.get("descripcion", "").strip().upper()
        
        estado_val = request.form.get("estado", "ACTIVO")
        estado = EstadoCategoria(estado_val)

        exito, mensaje = crear_o_actualizar_categoria(
            categoria_id=categoria_id,
            codigo=codigo,
            nombre=nombre,
            descripcion=descripcion,
            estado=estado
        )

        if exito:
            flash(mensaje, "success")
        else:
            flash(mensaje, "danger")
            
        return redirect(url_for("categorias.categorias"))

    # GET
    lista_categorias = Categoria.query.order_by(Categoria.id.desc()).all()
    siguiente_codigo = generar_siguiente_codigo_categoria()

    return render_template(
        "categorias/categorias.html",
        categorias=lista_categorias,
        siguiente_codigo=siguiente_codigo
    )