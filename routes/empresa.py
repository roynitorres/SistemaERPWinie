import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from werkzeug.utils import secure_filename

from database import db
from models.empresa import Empresa
from utils.permisos import roles_required

empresa_bp = Blueprint("empresa", __name__)


@empresa_bp.route("/mi-cuenta/informacion-empresa", methods=["GET", "POST"])
@login_required
@roles_required("ADMIN")
def informacion_empresa():
    empresa = Empresa.query.first()

    if request.method == "POST":
        if not empresa:
            empresa = Empresa()
            db.session.add(empresa)

        empresa.razon_social = request.form.get("razon_social", "").strip()
        empresa.ruc = request.form.get("ruc", "").strip()
        empresa.tipo_empresa = request.form.get("tipo_empresa")
        empresa.direccion = request.form.get("direccion", "").strip()
        empresa.ciudad = request.form.get("ciudad", "").strip()
        empresa.telefono = request.form.get("telefono", "").strip()
        empresa.email = request.form.get("email", "").strip()
        empresa.sitio_web = request.form.get("sitio_web", "").strip()
        empresa.regimen = request.form.get("regimen")
        empresa.serie_factura = request.form.get("serie_factura", "F001").strip()
        empresa.correlativo = request.form.get("correlativo", "00034").strip()
        empresa.iva = request.form.get("iva", 15)
        empresa.estado = request.form.get("estado") == "ACTIVO"

        logo = request.files.get("logo")
        if logo and logo.filename:
            filename = secure_filename(logo.filename)
            upload_folder = os.path.join("static", "uploads", "empresa")
            os.makedirs(upload_folder, exist_ok=True)

            logo_path = os.path.join(upload_folder, filename)
            logo.save(logo_path)

            empresa.logo = f"uploads/empresa/{filename}"

        if not empresa.razon_social:
            flash("La razón social es obligatoria", "danger")
            return redirect(url_for("empresa.informacion_empresa"))

        db.session.commit()
        flash("Información de la empresa guardada correctamente", "success")
        return redirect(url_for("empresa.informacion_empresa"))

    return render_template("empresa/informacion_empresa.html", empresa=empresa)