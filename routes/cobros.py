from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db
from models.cliente import Cliente
from models.venta import Venta
from models.pago import Pago
from models.banco import Banco
from models.cuota_venta import CuotaVenta
from models.recibo_caja import ReciboCaja
from models.empresa import Empresa
from models.enums import EstadoVenta, TipoVenta
from utils.permisos import roles_required
from sqlalchemy.orm import joinedload
from datetime import datetime, UTC

cobros_bp = Blueprint("cobros", __name__, url_prefix="/cobros")


# ==================================================
# VISTA PRINCIPAL: REGISTRAR COBROS
# ==================================================
@cobros_bp.route("", methods=["GET"])
@login_required
@roles_required("ADMIN", "VENDEDOR")
def index():
    bancos = Banco.query.filter_by(estado="ACTIVO").order_by(Banco.nombre.asc()).all()
    cliente_id_param = request.args.get("cliente_id", type=int)
    
    # Clientes con crédito activo o saldo pendiente para carga rápida
    clientes = Cliente.query.order_by(Cliente.nombres.asc()).all()
    
    return render_template(
        "cobros/index.html",
        bancos=bancos,
        clientes=clientes,
        cliente_id_param=cliente_id_param,
        now=datetime.now()
    )


# ==================================================
# BÚSQUEDA AJAX DE CLIENTES CON SALDO
# ==================================================
@cobros_bp.route("/clientes-buscar", methods=["GET"])
@login_required
def clientes_buscar():
    query = request.args.get("q", "").strip()
    
    clientes_query = Cliente.query
    if query:
        clientes_query = clientes_query.filter(
            (Cliente.nombres.ilike(f"%{query}%")) |
            (Cliente.codigo.ilike(f"%{query}%")) |
            (Cliente.telefono.ilike(f"%{query}%"))
        )
    
    clientes_lista = clientes_query.order_by(Cliente.nombres.asc()).limit(15).all()
    resultado = []

    for c in clientes_lista:
        ventas_credito = Venta.query.filter_by(
            cliente_id=c.id,
            tipo_venta=TipoVenta.CREDITO,
            estado=EstadoVenta.ACTIVA
        ).options(joinedload(Venta.pagos)).all()

        saldo_total = 0.0
        facturas_count = 0
        facturas_vencidas = 0

        for v in ventas_credito:
            abonado = sum(float(p.monto_pago) for p in v.pagos if p.estado == "ACTIVO")
            saldo_v = float(v.total_venta) - abonado
            if saldo_v > 0.005:
                saldo_total += saldo_v
                facturas_count += 1
                if v.fecha_limite_credito and v.fecha_limite_credito < datetime.now().date():
                    facturas_vencidas += 1

        resultado.append({
            "id": c.id,
            "nombres": c.nombres,
            "codigo": c.codigo or "",
            "identificacion": c.codigo or "",
            "telefono": c.telefono or "",
            "ciudad": c.ciudad or "",
            "saldo_total": round(saldo_total, 2),
            "facturas_count": facturas_count,
            "facturas_vencidas": facturas_vencidas
        })

    return jsonify({"success": True, "clientes": resultado})


# ==================================================
# DETALLE DE FACTURAS PENDIENTES DEL CLIENTE (FIFO)
# ==================================================
@cobros_bp.route("/cliente/<int:cliente_id>/facturas", methods=["GET"])
@login_required
def cliente_facturas(cliente_id):
    cliente = db.session.get(Cliente, cliente_id)
    if not cliente:
        return jsonify({"success": False, "message": "Cliente no encontrado"}), 404

    ventas_credito = Venta.query.filter_by(
        cliente_id=cliente.id,
        tipo_venta=TipoVenta.CREDITO,
        estado=EstadoVenta.ACTIVA
    ).options(
        joinedload(Venta.pagos),
        joinedload(Venta.cuotas)
    ).order_by(Venta.fecha_venta.asc()).all()

    facturas = []
    saldo_total_global = 0.0
    hoy = datetime.now().date()

    for v in ventas_credito:
        abonado = sum(float(p.monto_pago) for p in v.pagos if p.estado == "ACTIVO")
        saldo_pendiente = float(v.total_venta) - abonado
        if saldo_pendiente <= 0.005:
            continue

        saldo_total_global += saldo_pendiente
        es_vencida = bool(v.fecha_limite_credito and v.fecha_limite_credito < hoy)
        dias_vencida = (hoy - v.fecha_limite_credito).days if es_vencida else 0

        # Calcular monto de la próxima cuota no pagada
        proxima_cuota_monto = saldo_pendiente
        if v.cuotas:
            for c in v.cuotas:
                if c.estado != "PAGADA":
                    saldo_c = (float(c.monto_cuota) - float(c.monto_abonado))
                    if saldo_c > 0.01:
                        proxima_cuota_monto = saldo_c
                        break

        facturas.append({
            "id": v.id,
            "numero_factura": v.numero_factura,
            "fecha_venta": v.fecha_venta.strftime("%d/%m/%Y") if v.fecha_venta else "-",
            "fecha_limite_credito": v.fecha_limite_credito.strftime("%d/%m/%Y") if v.fecha_limite_credito else "-",
            "total_venta": float(v.total_venta),
            "total_abonado": round(abonado, 2),
            "saldo_pendiente": round(saldo_pendiente, 2),
            "es_vencida": es_vencida,
            "dias_vencida": dias_vencida,
            "proxima_cuota": round(proxima_cuota_monto, 2)
        })

    return jsonify({
        "success": True,
        "cliente": {
            "id": cliente.id,
            "nombres": cliente.nombres,
            "codigo": cliente.codigo or "",
            "identificacion": cliente.codigo or "",
            "telefono": cliente.telefono or "",
            "ciudad": cliente.ciudad or "",
            "saldo_total": round(saldo_total_global, 2),
            "total_facturas": len(facturas)
        },
        "facturas": facturas
    })


# ==================================================
# PROCESAR COBRO Y EMITIR RECIBO DE CAJA
# ==================================================
@cobros_bp.route("/procesar", methods=["POST"])
@login_required
@roles_required("ADMIN", "VENDEDOR")
def procesar_cobro():
    try:
        data = request.get_json() or {}
        cliente_id = data.get("cliente_id")
        monto_total_val = data.get("monto_total")
        tipo_pago = (data.get("tipo_pago") or "EFECTIVO").upper()
        banco_id = data.get("banco_id")
        referencia = (data.get("referencia") or "").strip()
        observaciones = (data.get("observaciones") or "").strip()
        distribucion = data.get("distribucion") or []

        if not cliente_id:
            return jsonify({"success": False, "message": "Seleccione un cliente válido"}), 400
        
        try:
            monto_total = round(float(monto_total_val), 2)
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Monto de cobro inválido"}), 400

        if monto_total <= 0:
            return jsonify({"success": False, "message": "El monto a cobrar debe ser mayor a cero"}), 400

        if tipo_pago == "TRANSFERENCIA":
            if not banco_id:
                return jsonify({"success": False, "message": "Debe seleccionar un banco para cobros por transferencia"}), 400
            if not referencia:
                return jsonify({"success": False, "message": "Debe ingresar el número de referencia de la transferencia"}), 400

        cliente = db.session.get(Cliente, int(cliente_id))
        if not cliente:
            return jsonify({"success": False, "message": "Cliente no encontrado"}), 404

        # Calcular saldo total previo del cliente
        ventas_activas = Venta.query.filter_by(
            cliente_id=cliente.id,
            tipo_venta=TipoVenta.CREDITO,
            estado=EstadoVenta.ACTIVA
        ).options(joinedload(Venta.pagos), joinedload(Venta.cuotas)).all()

        saldo_anterior = sum(
            (float(v.total_venta) - sum(float(p.monto_pago) for p in v.pagos if p.estado == "ACTIVO"))
            for v in ventas_activas
        )
        saldo_anterior = max(0.0, round(saldo_anterior, 2))

        # Validar distribución
        suma_distribuida = sum(round(float(item.get("monto", 0)), 2) for item in distribucion)
        if abs(suma_distribuida - monto_total) > 0.05:
            return jsonify({
                "success": False,
                "message": f"La suma distribuida (C$ {suma_distribuida:.2f}) no coincide con el total cobrado (C$ {monto_total:.2f})"
            }), 400

        # Generar número correlativo de recibo (RC-000001)
        ultimo_recibo = ReciboCaja.query.order_by(ReciboCaja.id.desc()).first()
        siguiente_correlativo = (ultimo_recibo.id + 1) if ultimo_recibo else 1
        numero_recibo = f"RC-{str(siguiente_correlativo).zfill(6)}"

        # Determinar banco_id entero
        b_id = int(banco_id) if banco_id and str(banco_id).isdigit() else None
        saldo_nuevo = max(0.0, round(saldo_anterior - monto_total, 2))

        # Crear ReciboCaja
        nuevo_recibo = ReciboCaja(
            numero_recibo=numero_recibo,
            cliente_id=cliente.id,
            usuario_id=current_user.id,
            banco_id=b_id,
            monto_total=monto_total,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=saldo_nuevo,
            tipo_pago=tipo_pago,
            referencia=referencia,
            observaciones=observaciones or f"Cobro aplicado a cuenta corriente de {cliente.nombres}",
            estado="ACTIVO",
            created_at=datetime.now(UTC)
        )
        db.session.add(nuevo_recibo)
        db.session.flush()

        # Aplicar pagos a cada factura distribuida
        ventas_dict = {v.id: v for v in ventas_activas}

        for item in distribucion:
            v_id = item.get("venta_id")
            monto_item = round(float(item.get("monto", 0)), 2)
            if monto_item <= 0:
                continue

            venta = ventas_dict.get(int(v_id))
            if not venta:
                continue

            # Crear Pago asociado
            monto_ef = monto_item if tipo_pago == "EFECTIVO" else 0.0
            monto_tr = monto_item if tipo_pago == "TRANSFERENCIA" else 0.0

            pago_factura = Pago(
                venta_id=venta.id,
                usuario_id=current_user.id,
                recibo_caja_id=nuevo_recibo.id,
                banco_id=b_id,
                monto_pago=monto_item,
                monto_efectivo=monto_ef,
                monto_transferencia=monto_tr,
                tipo_pago=tipo_pago,
                referencia=referencia,
                observaciones=f"Recibo #{nuevo_recibo.numero_recibo}",
                fecha_pago=datetime.now(),
                estado="ACTIVO"
            )
            db.session.add(pago_factura)

            # Imputar a cuotas si tiene
            if venta.cuotas:
                monto_restante_abono = monto_item
                for cuota in venta.cuotas:
                    if monto_restante_abono <= 0:
                        break
                    pendiente_cuota = float(cuota.monto_cuota) - float(cuota.monto_abonado)
                    if pendiente_cuota <= 0:
                        continue
                    aplicar_c = min(monto_restante_abono, pendiente_cuota)
                    cuota.monto_abonado = float(cuota.monto_abonado) + aplicar_c
                    monto_restante_abono -= aplicar_c
                    if float(cuota.monto_abonado) >= float(cuota.monto_cuota) - 0.01:
                        cuota.estado = "PAGADA"

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Cobro registrado exitosamente",
            "recibo_id": nuevo_recibo.id,
            "numero_recibo": nuevo_recibo.numero_recibo,
            "monto_total": float(nuevo_recibo.monto_total),
            "saldo_anterior": float(nuevo_recibo.saldo_anterior),
            "saldo_nuevo": float(nuevo_recibo.saldo_nuevo)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error al procesar cobro: {str(e)}"}), 500


# ==================================================
# VISTA / IMPRESIÓN DEL RECIBO DE CAJA
# ==================================================
@cobros_bp.route("/recibo/<int:recibo_id>", methods=["GET"])
@login_required
def ver_recibo(recibo_id):
    recibo = db.session.get(ReciboCaja, recibo_id)
    if not recibo:
        flash("Recibo no encontrado.", "error")
        return redirect(url_for("cobros.index"))

    empresa = Empresa.query.first()
    format_type = request.args.get("format", "html")

    if format_type == "json":
        facturas_afectadas = []
        for p in recibo.pagos:
            if p.estado == "ACTIVO" and p.venta:
                facturas_afectadas.append({
                    "numero_factura": p.venta.numero_factura,
                    "monto_abonado": float(p.monto_pago)
                })
        return jsonify({
            "success": True,
            "recibo": {
                "id": recibo.id,
                "numero_recibo": recibo.numero_recibo,
                "fecha": recibo.created_at.strftime("%d/%m/%Y %I:%M %p"),
                "cliente": recibo.cliente.nombres if recibo.cliente else "N/D",
                "tipo_pago": recibo.tipo_pago,
                "banco": recibo.banco.nombre if recibo.banco else "",
                "referencia": recibo.referencia or "",
                "monto_total": float(recibo.monto_total),
                "saldo_anterior": float(recibo.saldo_anterior),
                "saldo_nuevo": float(recibo.saldo_nuevo),
                "facturas_afectadas": facturas_afectadas
            }
        })

    return render_template(
        "cobros/recibo_imprimir.html",
        recibo=recibo,
        empresa=empresa,
        now=datetime.now()
    )


# ==================================================
# HISTORIAL DE RECIBOS DE CAJA
# ==================================================
@cobros_bp.route("/historial", methods=["GET"])
@login_required
@roles_required("ADMIN", "VENDEDOR")
def historial():
    recibos = ReciboCaja.query.options(
        joinedload(ReciboCaja.cliente),
        joinedload(ReciboCaja.usuario),
        joinedload(ReciboCaja.banco),
        joinedload(ReciboCaja.pagos)
    ).order_by(ReciboCaja.id.desc()).limit(100).all()

    return render_template(
        "cobros/historial.html",
        recibos=recibos,
        now=datetime.now()
    )


# ==================================================
# ANULAR RECIBO DE CAJA
# ==================================================
@cobros_bp.route("/recibo/<int:recibo_id>/anular", methods=["POST"])
@login_required
@roles_required("ADMIN")
def anular_recibo(recibo_id):
    try:
        recibo = db.session.get(ReciboCaja, recibo_id)
        if not recibo:
            return jsonify({"success": False, "message": "Recibo no encontrado"}), 404

        if recibo.estado == "ANULADO":
            return jsonify({"success": False, "message": "Este recibo ya se encuentra anulado"}), 400

        data = request.get_json() or {}
        motivo = data.get("motivo", "").strip()
        if not motivo:
            return jsonify({"success": False, "message": "Debe especificar un motivo de anulación"}), 400

        recibo.estado = "ANULADO"
        recibo.motivo_anulacion = motivo

        # Anular todos los pagos vinculados y restablecer cuotas
        for pago in recibo.pagos:
            pago.estado = "ANULADO"
            pago.motivo_anulacion = f"Anulación de Recibo #{recibo.numero_recibo}: {motivo}"

            # Revertir cuotas si aplica
            if pago.venta and pago.venta.cuotas:
                monto_a_revertir = float(pago.monto_pago)
                for cuota in reversed(pago.venta.cuotas):
                    if monto_a_revertir <= 0:
                        break
                    abonado_cuota = float(cuota.monto_abonado)
                    if abonado_cuota > 0:
                        descontar = min(monto_a_revertir, abonado_cuota)
                        cuota.monto_abonado = abonado_cuota - descontar
                        monto_a_revertir -= descontar
                        if float(cuota.monto_abonado) < float(cuota.monto_cuota):
                            cuota.estado = "PENDIENTE"

        db.session.commit()
        return jsonify({"success": True, "message": f"Recibo #{recibo.numero_recibo} anulado correctamente"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error al anular recibo: {str(e)}"}), 500
