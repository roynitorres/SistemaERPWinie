from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required
from utils.permisos import roles_required

# Modelo proveedor
from models.proveedor import Proveedor
from models.enums import EstadoProveedor

# Servicios
from services.proveedor_service import (
    crear_o_actualizar_proveedor, 
    generar_siguiente_codigo_proveedor,
    exportar_proveedores_csv
)

# ==================================================
# BLUEPRINT PROVEEDORES
# ==================================================

proveedores_bp = Blueprint("proveedores", __name__)

# VISTA PROVEEDORES
@proveedores_bp.route("/proveedores", methods=["GET", "POST"])
@login_required
@roles_required("ADMIN")
def proveedores():
    # ==========================================
    # POST
    # ==========================================
    if request.method == "POST":
        proveedor_id = request.form.get("proveedor_id")
        codigo = request.form.get("codigo", "").strip()
        nombre_proveedor = request.form.get("nombre_proveedor", "").strip().upper()
        nombre_contacto = request.form.get("nombre_contacto", "").strip().upper()
        telefono = request.form.get("telefono", "").strip()
        departamento = request.form.get("departamento", "").strip().upper()
        municipio = request.form.get("municipio", "").strip().upper()
        ruc = request.form.get("ruc", "").strip()
        direccion = request.form.get("direccion", "").strip().upper()
        estado_val = request.form.get("estado", "ACTIVO")
        estado = EstadoProveedor(estado_val)

        exito, mensaje = crear_o_actualizar_proveedor(
            proveedor_id=proveedor_id,
            codigo=codigo,
            nombre_proveedor=nombre_proveedor,
            nombre_contacto=nombre_contacto,
            telefono=telefono,
            departamento=departamento,
            municipio=municipio,
            ruc=ruc,
            direccion=direccion,
            estado=estado
        )

        if exito:
            flash(mensaje, "success")
        else:
            flash(mensaje, "danger")
            
        return redirect(url_for("proveedores.proveedores"))

    # ==========================================
    # GET
    # ==========================================
    lista_proveedores = Proveedor.query.order_by(Proveedor.id.desc()).all()
    siguiente_codigo = generar_siguiente_codigo_proveedor()

    return render_template(
        "proveedores/proveedores.html",
        proveedores=lista_proveedores,
        siguiente_codigo=siguiente_codigo
    )


# ==================================================
# EXPORTAR PROVEEDORES A CSV
# ==================================================
@proveedores_bp.route("/proveedores/exportar")
@login_required
@roles_required("ADMIN")
def exportar_proveedores():
    csv_data = exportar_proveedores_csv()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=proveedores.csv"}
    )
