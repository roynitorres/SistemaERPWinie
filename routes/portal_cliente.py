from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.venta import Venta
from models.enums import EstadoVenta, TipoVenta
from database import db
from sqlalchemy.orm import joinedload
from datetime import datetime

portal_cliente_bp = Blueprint("portal_cliente", __name__)


def solo_cliente():
    return current_user.is_authenticated and current_user.rol and current_user.rol.nombre.upper() == "CLIENTE"


@portal_cliente_bp.route("/portal-cliente", methods=["GET", "POST"])
@login_required
def portal():
    if not solo_cliente():
        return redirect(url_for("dashboard"))

    if current_user.debe_cambiar_password:
        return redirect(url_for("portal_cliente.cambiar_password_cliente"))

    cliente = current_user.cliente

    if request.method == "POST":
        action = request.form.get("action")
        if action == "cambiar_password":
            password_actual    = request.form.get("password_actual", "")
            nueva_password     = request.form.get("nueva_password", "")
            confirmar_password = request.form.get("confirmar_password", "")

            if not password_actual or not nueva_password or not confirmar_password:
                flash("Debes ingresar todos los campos de contraseña.", "danger")
                return redirect(url_for("portal_cliente.portal", tab="seguridad"))

            if not current_user.check_password(password_actual):
                flash("La contraseña actual no es correcta.", "danger")
                return redirect(url_for("portal_cliente.portal", tab="seguridad"))

            if len(nueva_password) < 6:
                flash("La nueva contraseña debe tener al menos 6 caracteres.", "warning")
                return redirect(url_for("portal_cliente.portal", tab="seguridad"))

            if nueva_password != confirmar_password:
                flash("Las contraseñas no coinciden.", "warning")
                return redirect(url_for("portal_cliente.portal", tab="seguridad"))

            current_user.set_password(nueva_password)
            current_user.debe_cambiar_password = False
            current_user.password_temporal_plana = None
            db.session.commit()

            flash("¡Contraseña actualizada correctamente!", "success")
            return redirect(url_for("portal_cliente.portal", tab="seguridad"))

    active_tab = request.args.get("tab", "facturas")
    ventas = Venta.query.filter_by(
        cliente_id=current_user.cliente_id
    ).options(
        joinedload(Venta.pagos),
        joinedload(Venta.cuotas)
    ).order_by(Venta.fecha_venta.desc()).all()

    total_facturado = 0.0
    total_recaudado = 0.0
    saldo_pendiente_total = 0.0

    cnt_facturas_totales = 0
    cnt_facturas_contado = 0
    cnt_facturas_credito = 0
    cnt_facturas_pendientes = 0

    ventas_procesadas = []

    for venta in ventas:
        if venta.estado != EstadoVenta.ACTIVA:
            continue

        cnt_facturas_totales += 1
        monto_venta = float(venta.total_venta)
        total_facturado += monto_venta

        tipo_val = venta.tipo_venta.value if hasattr(venta.tipo_venta, 'value') else str(venta.tipo_venta)
        if tipo_val.upper() == 'CONTADO':
            cnt_facturas_contado += 1
        elif tipo_val.upper() == 'CREDITO':
            cnt_facturas_credito += 1

        total_abonado = sum(
            float(pago.monto_pago)
            for pago in venta.pagos
            if pago.estado == "ACTIVO"
        )
        total_recaudado += total_abonado

        saldo = monto_venta - total_abonado
        if saldo > 0.01:
            saldo_pendiente_total += saldo
            cnt_facturas_pendientes += 1

        ventas_procesadas.append({
            "venta": venta,
            "total_abonado": total_abonado,
            "saldo_pendiente": max(0.0, saldo),
            "es_pagada": saldo <= 0.01
        })

    kpis = {
        "total_facturas": cnt_facturas_totales,
        "facturas_contado": cnt_facturas_contado,
        "facturas_credito": cnt_facturas_credito,
        "facturas_pendientes": cnt_facturas_pendientes,
        "total_facturado": total_facturado,
        "total_recaudado": total_recaudado,
        "saldo_pendiente": saldo_pendiente_total,
    }

    return render_template(
        "cliente_portal/portal.html",
        cliente=cliente,
        ventas_procesadas=ventas_procesadas,
        ventas=ventas,
        kpis=kpis,
        active_tab=active_tab,
        now=datetime.now()
    )


@portal_cliente_bp.route("/portal-cliente/cambiar-password", methods=["GET", "POST"])
@login_required
def cambiar_password_cliente():
    if not solo_cliente():
        return redirect(url_for("dashboard"))

    cliente = current_user.cliente

    if request.method == "POST":
        password_actual    = request.form.get("password_actual", "")
        nueva_password     = request.form.get("nueva_password", "")
        confirmar_password = request.form.get("confirmar_password", "")

        if not current_user.check_password(password_actual):
            flash("La contraseña actual no es correcta.", "danger")
            return redirect(url_for("portal_cliente.cambiar_password_cliente"))

        if len(nueva_password) < 6:
            flash("La nueva contraseña debe tener al menos 6 caracteres.", "warning")
            return redirect(url_for("portal_cliente.cambiar_password_cliente"))

        if nueva_password != confirmar_password:
            flash("Las contraseñas no coinciden.", "warning")
            return redirect(url_for("portal_cliente.cambiar_password_cliente"))

        current_user.set_password(nueva_password)
        current_user.debe_cambiar_password = False
        current_user.password_temporal_plana = None
        db.session.commit()

        flash("¡Contraseña actualizada correctamente!", "success")
        return redirect(url_for("portal_cliente.portal"))

    return render_template(
        "cliente_portal/cambiar_password.html",
        cliente=cliente
    )