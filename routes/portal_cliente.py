from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.venta import Venta
from models.detalle_venta import DetalleVenta
from models.pago import Pago
from models.enums import EstadoVenta, TipoVenta
from database import db
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

portal_cliente_bp = Blueprint("portal_cliente", __name__)


def format_datetime_local(dt, created_at=None):
    if not dt:
        return ''
    # Si viene con hora real (diferente de medianoche 00:00:00)
    if dt.hour != 0 or dt.minute != 0:
        return dt.strftime('%d/%m/%Y %I:%M %p')

    # Si viene a las 00:00 y tenemos created_at con hora real
    if created_at and (created_at.hour != 0 or created_at.minute != 0):
        # created_at se guarda en UTC; zona local es UTC-6
        local_time = (created_at - timedelta(hours=6)).time()
        combined = datetime.combine(dt.date(), local_time)
        return combined.strftime('%d/%m/%Y %I:%M %p')

    # Si no hay hora o es medianoche, mostrar únicamente la fecha
    return dt.strftime('%d/%m/%Y')


def extract_nombre_apellido(nombre_completo):
    """
    Extrae únicamente el primer nombre y primer apellido para una visualización
    limpia y minimalista en el portal (ej: 'Winie Garcia' en lugar de 4 nombres).
    """
    if not nombre_completo:
        return "Cliente", "CL"
    palabras = [p.capitalize() for p in nombre_completo.strip().split()]
    if len(palabras) == 1:
        return palabras[0], palabras[0][:2].upper()
    elif len(palabras) == 2:
        return f"{palabras[0]} {palabras[1]}", f"{palabras[0][0]}{palabras[1][0]}".upper()
    elif len(palabras) == 3:
        return f"{palabras[0]} {palabras[2]}", f"{palabras[0][0]}{palabras[2][0]}".upper()
    else:
        # 4 o más palabras: ej. WINIE LAURISSA GARCIA SANDOVAL -> Winie Garcia
        nombre = f"{palabras[0]} {palabras[2]}"
        iniciales = f"{palabras[0][0]}{palabras[2][0]}".upper()
        return nombre, iniciales


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
        joinedload(Venta.pagos).joinedload(Pago.banco),
        joinedload(Venta.cuotas),
        joinedload(Venta.detalle_ventas).joinedload(DetalleVenta.producto)
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

        json_data = {
            "id": venta.id,
            "numero_factura": venta.numero_factura,
            "fecha_venta": format_datetime_local(venta.fecha_venta, venta.created_at),
            "tipo_venta": tipo_val,
            "total_venta": monto_venta,
            "total_abonado": total_abonado,
            "saldo_pendiente": float(max(0.0, saldo)),
            "es_pagada": saldo <= 0.01,
            "productos": [
                {
                    "nombre": d.producto.nombre if d.producto else "Producto",
                    "codigo": d.producto.codigo_producto if d.producto else "",
                    "cantidad": d.cantidad,
                    "precio_unitario": float(d.precio_unitario),
                    "descuento_monto": float(d.descuento_monto or 0.0),
                    "subtotal": float(d.subtotal)
                }
                for d in venta.detalle_ventas
            ],
            "pagos": [
                {
                    "id": p.id,
                    "fecha": format_datetime_local(p.fecha_pago, p.created_at),
                    "monto": float(p.monto_pago),
                    "tipo": p.tipo_pago,
                    "metodo": p.tipo_pago,
                    "banco": p.banco.nombre if p.banco else '',
                    "referencia": p.referencia or '',
                    "estado": p.estado
                }
                for p in venta.pagos if p.estado == "ACTIVO"
            ],
            "url_imprimir": url_for('pagos.factura', venta_id=venta.id)
        }

        ventas_procesadas.append({
            "venta": venta,
            "total_abonado": total_abonado,
            "saldo_pendiente": max(0.0, saldo),
            "es_pagada": saldo <= 0.01,
            "json_data": json_data
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

    nombre_mostrar, iniciales_mostrar = extract_nombre_apellido(cliente.nombres if cliente else "")

    return render_template(
        "cliente_portal/portal.html",
        cliente=cliente,
        nombre_cliente=nombre_mostrar,
        iniciales_cliente=iniciales_mostrar,
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