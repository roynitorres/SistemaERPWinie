from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, logout_user
from models.venta import Venta
from database import db

portal_cliente_bp = Blueprint("portal_cliente", __name__)


def solo_cliente():
    return current_user.is_authenticated and current_user.rol and current_user.rol.nombre.upper() == "CLIENTE"


@portal_cliente_bp.route("/portal-cliente")
@login_required
def portal():
    if not solo_cliente():
        return redirect(url_for("dashboard"))

    if current_user.debe_cambiar_password:
        return redirect(url_for("portal_cliente.cambiar_password_cliente"))

    cliente = current_user.cliente

    ventas = Venta.query.filter_by(
        cliente_id=cliente.id
    ).order_by(
        Venta.fecha_venta.desc()
    ).all()

    total_facturado = 0
    total_pagado = 0
    saldo_pendiente = 0

    for venta in ventas:
        if venta.estado != "ACTIVA":
            continue

        total = float(venta.total_venta)
        pagado = sum(
            float(pago.monto_pago)
            for pago in venta.pagos
            if pago.estado == "ACTIVO"
        )

        total_facturado += total
        total_pagado += pagado
        saldo_pendiente += max(total - pagado, 0)

    kpis = {
        "total_facturado": total_facturado,
        "total_pagado": total_pagado,
        "saldo_pendiente": saldo_pendiente,
        "facturas": len([v for v in ventas if v.estado == "ACTIVA"])
    }

    return render_template(
        "cliente_portal/portal.html",
        cliente=cliente,
        ventas=ventas,
        kpis=kpis
    )


@portal_cliente_bp.route("/portal-cliente/cambiar-password", methods=["GET", "POST"])
@login_required
def cambiar_password_cliente():
    if not solo_cliente():
        return redirect(url_for("dashboard"))

    cliente = current_user.cliente

    if request.method == "POST":
        password_actual = request.form.get("password_actual", "")
        nueva_password = request.form.get("nueva_password", "")
        confirmar_password = request.form.get("confirmar_password", "")

        if not current_user.check_password(password_actual):
            flash("La contraseña actual no es correcta", "danger")
            return redirect(url_for("portal_cliente.cambiar_password_cliente"))

        if len(nueva_password) < 8:
            flash("La nueva contraseña debe tener al menos 8 caracteres", "warning")
            return redirect(url_for("portal_cliente.cambiar_password_cliente"))

        if nueva_password != confirmar_password:
            flash("Las contraseñas no coinciden", "warning")
            return redirect(url_for("portal_cliente.cambiar_password_cliente"))

        current_user.set_password(nueva_password)
        current_user.debe_cambiar_password = False
        db.session.commit()

        flash("Contraseña actualizada correctamente", "success")
        return redirect(url_for("portal_cliente.portal"))

    return render_template(
        "cliente_portal/cambiar_password.html",
        cliente=cliente
    )