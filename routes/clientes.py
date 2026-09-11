from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required
from utils.permisos import roles_required

# Modelo cliente
from models.cliente import Cliente
from models.venta import Venta
from models.pago import Pago
from models.enums import EstadoCliente, EstadoVenta, TipoVenta
from sqlalchemy.orm import joinedload
from datetime import datetime

# Servicios
from services.cliente_service import (
    crear_o_actualizar_cliente, 
    generar_siguiente_codigo_cliente,
    exportar_clientes_csv,
    restaurar_password_cliente_service
)


# ==================================================
# BLUEPRINT CLIENTES
# ==================================================

clientes_bp = Blueprint("clientes", __name__)


# VISTA CLIENTES
@clientes_bp.route("/clientes", methods=["GET", "POST"])
@login_required
@roles_required("ADMIN", "VENDEDOR")
def clientes():
    # ==========================================
    # POST
    # ==========================================
    if request.method == "POST":
        cliente_id = request.form.get("cliente_id")
        nombre = request.form.get("nombres", "").strip().upper()
        telefono = request.form.get("telefono", "").strip()
        ciudad = request.form.get("ciudad", "").strip().upper()
        estado_val = request.form.get("estado", "ACTIVO")
        estado = EstadoCliente(estado_val)

        exito, mensaje = crear_o_actualizar_cliente(
            cliente_id=cliente_id,
            nombre=nombre,
            telefono=telefono,
            ciudad=ciudad,
            estado=estado
        )

        if exito:
            flash(mensaje, "success")
        else:
            flash(mensaje, "danger")
            
        return redirect(url_for("clientes.clientes"))

    # ==========================================
    # GET
    # ==========================================
    lista_clientes = Cliente.query.order_by(Cliente.id.desc()).all()
    siguiente_codigo = generar_siguiente_codigo_cliente()

    return render_template(
        "clientes/clientes.html",
        clientes=lista_clientes,
        siguiente_codigo=siguiente_codigo
    )


# ==================================================
# EXPORTAR CLIENTES A CSV
# ==================================================
@clientes_bp.route("/clientes/exportar")
@login_required
@roles_required("ADMIN")
def exportar_clientes():
    csv_data = exportar_clientes_csv()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=clientes.csv"}
    )


# ==================================================
# RESTAURAR CONTRASEÑA DE CLIENTE
# ==================================================
@clientes_bp.route("/clientes/restaurar-password/<int:cliente_id>", methods=["POST"])
@login_required
@roles_required("ADMIN")
def restaurar_password_cliente(cliente_id):
    exito, mensaje, username = restaurar_password_cliente_service(cliente_id)
    
    if exito:
        flash(mensaje, "success")
    else:
        flash(mensaje, "warning")

    return redirect(url_for("clientes.clientes"))


# ==================================================
# HISTORIAL DE COMPRAS DEL CLIENTE
# ==================================================
@clientes_bp.route("/clientes/<int:cliente_id>/historial", methods=["GET"])
@login_required
@roles_required("ADMIN", "VENDEDOR")
def historial_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    ventas = Venta.query.filter_by(cliente_id=cliente_id).options(
        joinedload(Venta.pagos),
        joinedload(Venta.cuotas)
    ).order_by(Venta.fecha_venta.desc()).all()

    ventas_procesadas = []
    for venta in ventas:
        if venta.estado != EstadoVenta.ACTIVA:
            continue

        monto_venta = float(venta.total_venta)
        total_abonado = sum(
            float(pago.monto_pago)
            for pago in venta.pagos
            if pago.estado == "ACTIVO"
        )
        saldo = monto_venta - total_abonado

        ventas_procesadas.append({
            "venta": venta,
            "total_abonado": total_abonado,
            "saldo_pendiente": max(0.0, saldo),
            "es_pagada": saldo <= 0.01
        })

    return render_template(
        "clientes/historial_cliente.html",
        cliente=cliente,
        ventas_procesadas=ventas_procesadas,
        now=datetime.now()
    )