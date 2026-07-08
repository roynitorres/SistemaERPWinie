from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from database import db
from models.rol import Rol
from utils.permisos import roles_required


roles_bp = Blueprint("roles", __name__)


@roles_bp.route("/roles", methods=["GET", "POST"])
@login_required
@roles_required("ADMIN")
def roles():
    if request.method == "POST":
        rol_id = request.form.get("rol_id")
        descripcion = request.form.get("descripcion", "").strip()
        descuento_maximo = request.form.get("descuento_maximo", 0)
        estado = True if request.form.get("estado") == "on" else False

        rol = Rol.query.get_or_404(rol_id)

        try:
            descuento_maximo = float(descuento_maximo)
        except ValueError:
            flash("El descuento máximo debe ser numérico", "warning")
            return redirect(url_for("roles.roles"))

        if descuento_maximo < 0 or descuento_maximo > 100:
            flash("El descuento máximo debe estar entre 0 y 100", "warning")
            return redirect(url_for("roles.roles"))

        if rol.nombre.upper() == "CLIENTE" and descuento_maximo != 0:
            flash("El rol CLIENTE no debe tener descuento", "warning")
            return redirect(url_for("roles.roles"))

        rol.descripcion = descripcion
        rol.descuento_maximo = descuento_maximo
        rol.estado = estado

        db.session.commit()

        flash("Rol actualizado correctamente", "success")
        return redirect(url_for("roles.roles"))

    roles = Rol.query.order_by(Rol.nombre.asc()).all()

    return render_template(
        "roles/roles.html",
        roles=roles
    )