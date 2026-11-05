from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from utils.permisos import roles_required

from services.notificacion_service import (
    obtener_resumen_notificaciones,
    silenciar_alerta_producto,
    reactivar_alerta_producto
)

notificaciones_bp = Blueprint("notificaciones", __name__)


@notificaciones_bp.route("/notificaciones", methods=["GET"])
@login_required
@roles_required("ADMIN", "VENDEDOR")
def index():
    filtro_inicial = request.args.get("filtro", "todas").lower()
    if filtro_inicial not in ["todas", "cobranzas", "stock", "silenciados"]:
        filtro_inicial = "todas"

    datos = obtener_resumen_notificaciones()

    return render_template(
        "notificaciones/notificaciones.html",
        notificaciones=datos,
        filtro_inicial=filtro_inicial
    )


@notificaciones_bp.route("/notificaciones/silenciar-producto", methods=["POST"])
@login_required
@roles_required("ADMIN")
def silenciar_producto():
    data = request.get_json() if request.is_json else request.form
    producto_id = data.get("producto_id")
    dias = data.get("dias")

    if not producto_id:
        if request.is_json:
            return jsonify({"success": False, "message": "ID de producto requerido"}), 400
        flash("ID de producto requerido", "danger")
        return redirect(url_for("notificaciones.index"))

    try:
        producto_id = int(producto_id)
        dias = int(dias) if dias and str(dias).isdigit() else None
    except (ValueError, TypeError):
        dias = None

    exito, mensaje = silenciar_alerta_producto(producto_id=producto_id, dias=dias)

    if request.is_json:
        return jsonify({"success": exito, "message": mensaje})

    flash(mensaje, "success" if exito else "danger")
    return redirect(url_for("notificaciones.index", filtro="stock"))


@notificaciones_bp.route("/notificaciones/reactivar-producto", methods=["POST"])
@login_required
@roles_required("ADMIN")
def reactivar_producto():
    data = request.get_json() if request.is_json else request.form
    producto_id = data.get("producto_id")

    if not producto_id:
        if request.is_json:
            return jsonify({"success": False, "message": "ID de producto requerido"}), 400
        flash("ID de producto requerido", "danger")
        return redirect(url_for("notificaciones.index"))

    try:
        producto_id = int(producto_id)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "ID inválido"}), 400

    exito, mensaje = reactivar_alerta_producto(producto_id=producto_id)

    if request.is_json:
        return jsonify({"success": exito, "message": mensaje})

    flash(mensaje, "success" if exito else "danger")
    return redirect(url_for("notificaciones.index", filtro="silenciados"))
