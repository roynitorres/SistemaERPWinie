"""
services/notificacion_service.py
Gestión centralizada de notificaciones del sistema (Cobranzas de Crédito y Stock).
Permite silenciar temporal o permanentemente alertas de productos que no se volverán a comprar,
y auto-reactivarlas si se compra inventario nuevo.
"""
from datetime import date, timedelta
from urllib.parse import quote
from sqlalchemy.orm import joinedload

from database import db
from models.venta import Venta
from models.producto import Producto
from models.alerta_silenciada import AlertaSilenciada
from models.enums import EstadoVenta, TipoVenta, EstadoProducto


def obtener_alertas_cobranza(hoy=None):
    """
    Retorna la lista de alertas de cobranzas activas (exclusivo para ventas a CRÉDITO):
    - Cuotas o facturas de crédito vencidas (morosos).
    - Cuotas o facturas de crédito que vencen hoy.
    """
    if hoy is None:
        hoy = date.today()

    ventas_credito = Venta.query.filter(
        Venta.estado == EstadoVenta.ACTIVA,
        Venta.tipo_venta == TipoVenta.CREDITO
    ).options(
        joinedload(Venta.pagos),
        joinedload(Venta.cliente),
        joinedload(Venta.cuotas)
    ).all()

    alertas = []

    for venta in ventas_credito:
        if not venta.cliente:
            continue

        total_venta = float(venta.total_venta)
        total_pagado = sum(
            float(pago.monto_pago)
            for pago in venta.pagos
            if pago.estado == "ACTIVO"
        )
        saldo_total = max(total_venta - total_pagado, 0)

        if saldo_total <= 0:
            continue

        # 1. Si la venta a crédito tiene cuotas detalladas
        if venta.cuotas and len(venta.cuotas) > 0:
            for cuota in venta.cuotas:
                monto_c = float(cuota.monto_cuota)
                abonado_c = float(cuota.monto_abonado or 0)
                saldo_c = max(monto_c - abonado_c, 0)

                if saldo_c <= 0 or cuota.estado == "PAGADA":
                    continue

                if cuota.fecha_vencimiento <= hoy:
                    dias_mora = (hoy - cuota.fecha_vencimiento).days
                    dias_gracia = cuota.dias_gracia or 2

                    if dias_mora > dias_gracia:
                        estado_label = "Moroso"
                        tipo_alerta = "danger"
                    elif dias_mora > 0:
                        estado_label = "En Gracia"
                        tipo_alerta = "warning"
                    else:
                        estado_label = "Cobrar hoy"
                        tipo_alerta = "info"

                    tel_raw = str(venta.cliente.telefono or "").strip()
                    tel_clean = "".join(filter(str.isdigit, tel_raw))
                    tel_wa = f"505{tel_clean}" if len(tel_clean) == 8 else tel_clean

                    msg = (
                        f"Hola {venta.cliente.nombres}, le recordamos que tiene la cuota #{cuota.numero_cuota} "
                        f"por un saldo de C$ {saldo_c:.2f} con fecha de vencimiento {cuota.fecha_vencimiento.strftime('%d/%m/%Y')}. "
                        f"Por favor comuníquese con nosotros para registrar su pago."
                    )

                    alertas.append({
                        "id": f"cobro_{venta.id}_{cuota.numero_cuota}",
                        "tipo": "COBRANZA",
                        "venta_id": venta.id,
                        "cliente_id": venta.cliente.id,
                        "cliente": f"{venta.cliente.nombres}".strip(),
                        "telefono": tel_clean,
                        "whatsapp_url": f"https://wa.me/{tel_wa}?text={quote(msg)}" if tel_wa else None,
                        "factura": venta.numero_factura,
                        "numero_cuota": cuota.numero_cuota,
                        "monto_pendiente": saldo_c,
                        "fecha_vencimiento": cuota.fecha_vencimiento.strftime("%d/%m/%Y"),
                        "dias_mora": dias_mora,
                        "estado": estado_label,
                        "tipo_alerta": tipo_alerta,
                    })
        else:
            # 2. Venta a crédito sin desglose de cuotas
            fecha_cobro = venta.fecha_limite_credito or venta.fecha_venta.date()

            if fecha_cobro <= hoy:
                dias_mora = (hoy - fecha_cobro).days
                estado_label = "Moroso" if dias_mora > 0 else "Cobrar hoy"
                tipo_alerta = "danger" if dias_mora > 0 else "info"

                tel_raw = str(venta.cliente.telefono or "").strip()
                tel_clean = "".join(filter(str.isdigit, tel_raw))
                tel_wa = f"505{tel_clean}" if len(tel_clean) == 8 else tel_clean

                msg = (
                    f"Hola {venta.cliente.nombres}, le recordamos que tiene un saldo pendiente de "
                    f"C$ {saldo_total:.2f} correspondiente a la factura {venta.numero_factura}. "
                    f"Por favor comuníquese con nosotros para coordinar su pago."
                )

                alertas.append({
                    "id": f"cobro_{venta.id}",
                    "tipo": "COBRANZA",
                    "venta_id": venta.id,
                    "cliente_id": venta.cliente.id,
                    "cliente": f"{venta.cliente.nombres}".strip(),
                    "telefono": tel_clean,
                    "whatsapp_url": f"https://wa.me/{tel_wa}?text={quote(msg)}" if tel_wa else None,
                    "factura": venta.numero_factura,
                    "numero_cuota": None,
                    "monto_pendiente": saldo_total,
                    "fecha_vencimiento": fecha_cobro.strftime("%d/%m/%Y"),
                    "dias_mora": dias_mora,
                    "estado": estado_label,
                    "tipo_alerta": tipo_alerta,
                })

    alertas.sort(key=lambda item: item["dias_mora"], reverse=True)
    return alertas


def obtener_alertas_stock(hoy=None):
    """
    Retorna dos listas:
    1. alertas_activas: Productos agotados o bajos que NO están silenciados.
    2. alertas_silenciadas: Productos silenciados actualmente (para la pestaña de silenciados).
    Auto-reactiva productos si se compró nuevo stock.
    """
    if hoy is None:
        hoy = date.today()

    # Mapeo de productos silenciados vigentes
    silenciados = AlertaSilenciada.query.filter_by(tipo="PRODUCTO").all()
    silenciados_dict = {}
    for s in silenciados:
        if s.silenciado_hasta is None or s.silenciado_hasta >= hoy:
            silenciados_dict[s.referencia_id] = s
        else:
            # Expiró el periodo silenciado -> eliminar registro para reactivar
            db.session.delete(s)
    db.session.commit()

    productos = Producto.query.filter_by(estado=EstadoProducto.ACTIVO).options(
        joinedload(Producto.categoria)
    ).all()

    alertas_activas = []
    alertas_silenciadas = []

    for p in productos:
        stock_val = p.stock if p.stock is not None else 0
        min_val = p.stock_minimo if p.stock_minimo is not None else 5

        # Si el producto recuperó stock saludable (> stock_minimo) y estaba silenciado:
        # Auto-limpiar el silenciado porque el producto ya volvió a circular normalmente
        if stock_val > min_val:
            if p.id in silenciados_dict:
                registro = silenciados_dict[p.id]
                db.session.delete(registro)
                db.session.commit()
            continue

        item_data = {
            "id": f"stock_{p.id}",
            "tipo": "STOCK",
            "producto_id": p.id,
            "nombre": p.nombre,
            "marca": p.marca or "",
            "codigo": p.codigo_producto,
            "categoria": p.categoria.nombre if p.categoria else "-",
            "stock": stock_val,
            "stock_minimo": min_val,
            "estado_stock": "AGOTADO" if stock_val <= 0 else "BAJO",
            "tipo_alerta": "danger" if stock_val <= 0 else "warning",
            "mensaje": "Agotado (0 unidades)" if stock_val <= 0 else f"Stock bajo ({stock_val} de {min_val})"
        }

        # Si está silenciado
        if p.id in silenciados_dict:
            reg = silenciados_dict[p.id]
            item_data["silenciado"] = True
            item_data["silenciado_hasta"] = reg.silenciado_hasta.strftime("%d/%m/%Y") if reg.silenciado_hasta else "Indefinido"
            item_data["alerta_silenciada_id"] = reg.id
            alertas_silenciadas.append(item_data)
        else:
            item_data["silenciado"] = False
            alertas_activas.append(item_data)

    alertas_activas.sort(key=lambda item: (item["stock"], item["nombre"]))
    alertas_silenciadas.sort(key=lambda item: item["nombre"])

    return alertas_activas, alertas_silenciadas


def silenciar_alerta_producto(producto_id, dias=None, motivo=None):
    """
    Silencia la alerta de un producto por N días o de forma indefinida (dias=None).
    """
    hoy = date.today()
    fecha_limite = (hoy + timedelta(days=dias)) if dias else None

    existente = AlertaSilenciada.query.filter_by(tipo="PRODUCTO", referencia_id=producto_id).first()
    if existente:
        existente.silenciado_hasta = fecha_limite
        existente.motivo = motivo or "Silenciado por el usuario"
    else:
        nueva = AlertaSilenciada(
            tipo="PRODUCTO",
            referencia_id=producto_id,
            silenciado_hasta=fecha_limite,
            motivo=motivo or "Silenciado por el usuario"
        )
        db.session.add(nueva)

    db.session.commit()
    return True, "Alerta silenciada correctamente"


def reactivar_alerta_producto(producto_id):
    """
    Elimina el silenciado de un producto para que vuelva a alertar activamente.
    """
    existente = AlertaSilenciada.query.filter_by(tipo="PRODUCTO", referencia_id=producto_id).first()
    if existente:
        db.session.delete(existente)
        db.session.commit()
        return True, "Alerta reactivada correctamente"
    return False, "La alerta no estaba silenciada"


def obtener_resumen_notificaciones(hoy=None):
    """
    Consolida las alertas para el Dropdown flotante en el Topbar y la página completa.
    """
    cobranzas = obtener_alertas_cobranza(hoy=hoy)
    stock_activos, stock_silenciados = obtener_alertas_stock(hoy=hoy)

    return {
        "total_alertas": len(cobranzas) + len(stock_activos),
        "total_cobranzas": len(cobranzas),
        "total_stock": len(stock_activos),
        "total_silenciados": len(stock_silenciados),
        "cobranzas": cobranzas,
        "stock": stock_activos,
        "silenciados": stock_silenciados
    }
