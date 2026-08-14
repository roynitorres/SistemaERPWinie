
from flask import Blueprint
from flask import render_template
from flask import request
from flask import jsonify
from flask import redirect
from flask import url_for
from flask import flash
from flask import abort

from flask_login import login_required
from flask_login import current_user

from sqlalchemy import func

from database import db

# Modelos
from models.cliente import Cliente
from models.venta import Venta
from models.pago import Pago
from models.banco import Banco
from models.cuota_venta import CuotaVenta
from models.empresa import Empresa
from models.enums import EstadoVenta, TipoVenta
from utils.permisos import roles_required
from services.venta_service import anular_venta_service
from sqlalchemy.orm import joinedload

# Fechas
from datetime import datetime, date, timedelta


# ==================================================
# BLUEPRINT
# ==================================================

pagos_bp = Blueprint("pagos",__name__)


# ==================================================
# VISTA PRINCIPAL PAGOS
# ==================================================

@pagos_bp.route("/facturas/<tipo>", defaults={"estado": "todas"}, methods=["GET"])
@pagos_bp.route("/facturas/<tipo>/<estado>", methods=["GET"])
@login_required
@roles_required("ADMIN", "VENDEDOR")
def facturas(tipo, estado):
    if tipo not in ["contado", "credito"]:
        flash("Tipo de factura inválido.", "error")
        return redirect(url_for("dashboard"))
        
    if estado not in ["todas", "pagadas", "pendientes"]:
        estado = "todas"

    tipo_filtro = TipoVenta.CONTADO if tipo == "contado" else TipoVenta.CREDITO

    clientes = Cliente.query.order_by(Cliente.nombres.asc()).all()

    ventas = Venta.query.filter_by(tipo_venta=tipo_filtro).options(
        joinedload(Venta.cliente),
        joinedload(Venta.pagos),
        joinedload(Venta.cuotas)
    ).order_by(Venta.fecha_venta.desc()).all()
    
    total_facturado_pagado = 0
    total_facturas = 0
    facturas_pagadas = 0
    facturas_pendientes = 0
    ventas_pendientes = []
    ventas_filtradas = []
    
    for venta in ventas:
        if venta.estado != EstadoVenta.ACTIVA:
            continue
    
        total_facturas += 1
    
        total_abonado = sum(
            float(pago.monto_pago)
            for pago in venta.pagos
            if pago.estado == "ACTIVO"
        )
    
        saldo = float(venta.total_venta) - total_abonado
    
        es_pagada = saldo <= 0

        if es_pagada:
            facturas_pagadas += 1
            total_facturado_pagado += float(venta.total_venta)
        else:
            facturas_pendientes += 1
            ventas_pendientes.append(venta)

        if estado == "todas":
            ventas_filtradas.append(venta)
        elif estado == "pagadas" and es_pagada:
            ventas_filtradas.append(venta)
        elif estado == "pendientes" and not es_pagada:
            ventas_filtradas.append(venta)
    
    kpis = {
        "total_facturado_pagado": total_facturado_pagado,
        "total_facturas": total_facturas,
        "facturas_pagadas": facturas_pagadas,
        "facturas_pendientes": facturas_pendientes
    }
    

    if tipo_filtro == TipoVenta.CONTADO:
        plantilla = "pagos/pagos_contado.html"
    else:
        plantilla = "pagos/pagos_credito.html"

    return render_template(
        plantilla,
        clientes=clientes,
        ventas=ventas_filtradas,
        ventas_pendientes=ventas_pendientes,
        kpis=kpis,
        tipo_factura=tipo_filtro,
        estado_factura=estado,
        now=datetime.now()
    )


# ==================================================
# BUSCAR FACTURAS CLIENTE
# ==================================================

@pagos_bp.route(

    "/buscar-facturas-cliente/<int:cliente_id>",

    methods=["GET"]

)
@login_required
@roles_required("ADMIN", "VENDEDOR")
def buscar_facturas_cliente(cliente_id):

    ventas = Venta.query.filter(
        Venta.cliente_id == cliente_id,
        Venta.estado == EstadoVenta.ACTIVA
    ).options(joinedload(Venta.pagos)).all()

    resultado = []

    for venta in ventas:

        total_abonado = sum(
    
            float(pago.monto_pago)
    
            for pago in venta.pagos
    
            if pago.estado == "ACTIVO"
    
        )
    
        saldo_pendiente = (
    
            float(venta.total_venta)
    
            - total_abonado
    
        )
    
        # ==================================
        # SOLO FACTURAS CON SALDO
        # ==================================
    
        if saldo_pendiente <= 0:
    
            continue
    
        resultado.append({
    
            "id":
                venta.id,
    
            "numero_factura":
                venta.numero_factura,
    
            "total_venta":
                float(venta.total_venta),
    
            "total_abonado":
                total_abonado,
    
            "saldo_pendiente":
                saldo_pendiente
    
        })

    return jsonify(resultado)

# ==================================================
# RUTAS DE BANCOS (AJAX)
# ==================================================
@pagos_bp.route("/bancos/lista", methods=["GET"])
@login_required
def lista_bancos():
    bancos = Banco.query.filter_by(estado="ACTIVO").order_by(Banco.nombre.asc()).all()
    resultado = [{"id": b.id, "nombre": b.nombre} for b in bancos]
    return jsonify({"success": True, "bancos": resultado})

@pagos_bp.route("/bancos/guardar", methods=["POST"])
@login_required
@roles_required("ADMIN", "VENDEDOR")
def guardar_banco():
    try:
        data = request.get_json() or request.form
        nombre = data.get("nombre", "").strip()
        if not nombre:
            return jsonify({"success": False, "message": "El nombre del banco es obligatorio."})

        banco_existente = Banco.query.filter_by(nombre=nombre).first()
        if banco_existente:
            if banco_existente.estado != "ACTIVO":
                banco_existente.estado = "ACTIVO"
                db.session.commit()
                return jsonify({"success": True, "message": "Banco reactivado con éxito", "banco": {"id": banco_existente.id, "nombre": banco_existente.nombre}})
            return jsonify({"success": True, "message": "El banco ya se encuentra registrado", "banco": {"id": banco_existente.id, "nombre": banco_existente.nombre}})

        nuevo_banco = Banco(nombre=nombre, estado="ACTIVO")
        db.session.add(nuevo_banco)
        db.session.commit()

        return jsonify({"success": True, "message": "Banco registrado correctamente", "banco": {"id": nuevo_banco.id, "nombre": nuevo_banco.nombre}})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error guardando banco: {str(e)}"})


# ==================================================
# GUARDAR PAGO / ABONO DE CUOTA
# ==================================================

@pagos_bp.route("/guardar-pago", methods=["POST"])
@login_required
@roles_required("ADMIN", "VENDEDOR")
def guardar_pago():
    try:
        venta_id = request.form.get("venta_id")
        monto_pago_val = request.form.get("monto_pago")
        tipo_pago = request.form.get("tipo_pago", "EFECTIVO").upper()
        banco_id = request.form.get("banco_id")
        cuota_id = request.form.get("cuota_id")
        referencia = request.form.get("referencia", "").strip()
        observaciones = request.form.get("observaciones", "").strip()
        fecha_pago_form = request.form.get("fecha_pago")

        monto_efectivo_val = request.form.get("monto_efectivo", 0)
        monto_transferencia_val = request.form.get("monto_transferencia", 0)

        if not venta_id:
            return jsonify({"success": False, "message": "Factura inválida"})
        if not monto_pago_val:
            return jsonify({"success": False, "message": "Ingrese un monto válido"})

        venta = db.session.get(Venta, int(venta_id))
        if not venta:
            return jsonify({"success": False, "message": "Venta no encontrada"})

        # TOTAL ABONADO PREVIO
        total_abonado_previo = sum(float(pago.monto_pago) for pago in venta.pagos if pago.estado == "ACTIVO")
        saldo_pendiente = float(venta.total_venta) - total_abonado_previo

        monto_pago = float(monto_pago_val)
        if monto_pago <= 0:
            return jsonify({"success": False, "message": "El monto del pago debe ser mayor a 0"})

        if round(monto_pago, 2) > round(saldo_pendiente + 0.05, 2):
            return jsonify({"success": False, "message": f"El monto (C$ {monto_pago:.2f}) supera el saldo pendiente (C$ {saldo_pendiente:.2f})"})

        # PROCESAR PAGO MIXTO
        monto_efectivo = 0.0
        monto_transferencia = 0.0

        if tipo_pago == "MIXTO":
            monto_efectivo = float(monto_efectivo_val or 0)
            monto_transferencia = float(monto_transferencia_val or 0)
            if round(monto_efectivo + monto_transferencia, 2) != round(monto_pago, 2):
                monto_efectivo = monto_pago - monto_transferencia
        elif tipo_pago == "TRANSFERENCIA":
            monto_transferencia = monto_pago
        else:
            monto_efectivo = monto_pago

        fecha_pago = (datetime.strptime(fecha_pago_form, "%Y-%m-%d")
            if fecha_pago_form
            else datetime.now())

        b_id = int(banco_id) if banco_id and banco_id.isdigit() else None
        c_id = int(cuota_id) if cuota_id and cuota_id.isdigit() else None

        # CREAR PAGO
        nuevo_pago = Pago(
            venta_id=venta.id,
            usuario_id=current_user.id,
            cuota_id=c_id,
            banco_id=b_id,
            monto_pago=monto_pago,
            monto_efectivo=monto_efectivo,
            monto_transferencia=monto_transferencia,
            tipo_pago=tipo_pago,
            referencia=referencia,
            observaciones=observaciones,
            fecha_pago=fecha_pago,
            estado="ACTIVO"
        )
        db.session.add(nuevo_pago)
        db.session.flush()

        # IMPUTAR A CUOTA(S) SI LA VENTA ES A CRÉDITO Y POSEE CUOTAS
        if venta.tipo_venta == TipoVenta.CREDITO and venta.cuotas:
            monto_restante_abono = monto_pago
            
            # Si se especificó una cuota en particular, empezar por esa cuota
            cuotas_ordenadas = list(venta.cuotas)
            if c_id:
                cuota_target = next((c for c in cuotas_ordenadas if c.id == c_id), None)
                if cuota_target:
                    cuotas_ordenadas.remove(cuota_target)
                    cuotas_ordenadas.insert(0, cuota_target)

            for cuota in cuotas_ordenadas:
                if monto_restante_abono <= 0:
                    break

                pendiente_cuota = float(cuota.monto_cuota) - float(cuota.monto_abonado)
                if pendiente_cuota <= 0:
                    continue

                abono_aplicar = min(monto_restante_abono, pendiente_cuota)
                cuota.monto_abonado = float(cuota.monto_abonado) + abono_aplicar
                monto_restante_abono -= abono_aplicar

                if float(cuota.monto_abonado) >= float(cuota.monto_cuota) - 0.01:
                    cuota.estado = "PAGADA"

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Pago registrado correctamente",
            "pago_id": nuevo_pago.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})


# ==================================================
# ANULAR PAGO
# ==================================================

@pagos_bp.route("/anular-pago/<int:pago_id>", methods=["POST"])
@login_required
@roles_required("ADMIN")
def anular_pago(pago_id):
    try:
        # BUSCAR PAGO
        pago = db.session.get(Pago, pago_id)
        data = request.get_json()
        motivo = data.get("motivo", "").strip()
        if not pago:
            return jsonify({"success": False,"message": "Pago no encontrado"})
        if not motivo:
            return jsonify({"success": False,"message": "Debe indicar el motivo de anulación"})
        # VALIDAR ESTADO
        if pago.estado == "ANULADO":
            return jsonify({"success": False,"message": "Pago ya anulado"})
        # ANULAR
        pago.estado = "ANULADO"
        pago.motivo_anulacion = motivo
        db.session.commit()

        return jsonify({"success": True,"message": "Pago anulado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False,"message": str(e)})

# ==================================================
# FACTURA
# ==================================================
@pagos_bp.route("/factura/<int:venta_id>")
@login_required
def factura(venta_id):
    # BUSCAR VENTA
    venta = db.session.get(Venta, venta_id)
    if not venta:
        abort(404)

    # VALIDAR AUTORIZACIÓN: el cliente solo puede ver sus propias facturas
    if current_user.rol and current_user.rol.nombre.upper() == "CLIENTE":
        if venta.cliente_id != current_user.cliente_id:
            abort(403)

    empresa = Empresa.query.first()
    # MOSTRAR FACTURA
    return render_template(
        "ventas/factura.html",
        venta=venta,
        empresa=empresa
    )

# ==================================================
# ANULAR FACTURA
# ==================================================

@pagos_bp.route("/anular-venta/<int:venta_id>", methods=["POST"])
@login_required
@roles_required("ADMIN")
def anular_venta(venta_id):
    venta = Venta.query.get_or_404(venta_id)
    tipo_venta_url = venta.tipo_venta.value.lower()

    exito, mensaje = anular_venta_service(venta_id)

    if exito:
        flash(mensaje, "success")
    else:
        flash(mensaje, "danger")

    return redirect(url_for("pagos.facturas", tipo=tipo_venta_url))


# ==================================================
# VISTA DEDICADA: HISTORIAL DE PAGOS DE FACTURA
# ==================================================
@pagos_bp.route("/facturas/<int:venta_id>/historial", methods=["GET"])
@login_required
def historial_factura(venta_id):
    venta = Venta.query.get_or_404(venta_id)

    # VALIDAR AUTORIZACIÓN: el cliente solo puede ver sus propias facturas
    if current_user.rol and current_user.rol.nombre.upper() == "CLIENTE":
        if venta.cliente_id != current_user.cliente_id:
            abort(403)

    total_facturado = float(venta.total_venta)
    total_abonado = sum(
        float(pago.monto_pago)
        for pago in venta.pagos
        if pago.estado == "ACTIVO"
    )
    saldo_pendiente = max(0.0, total_facturado - total_abonado)

    kpis = {
        "total_facturado": total_facturado,
        "total_abonado": total_abonado,
        "saldo_pendiente": saldo_pendiente,
        "es_pagada": saldo_pendiente <= 0
    }

    return render_template(
        "pagos/historial_factura.html",
        venta=venta,
        kpis=kpis,
        now=datetime.now()
    )


@pagos_bp.route("/facturas/<int:venta_id>/cuotas/imprimir", methods=["GET"])
@login_required
def imprimir_cuotas(venta_id):
    venta = Venta.query.get_or_404(venta_id)
    if current_user.rol and current_user.rol.nombre.upper() == "CLIENTE":
        if venta.cliente_id != current_user.cliente_id:
            abort(403)

    empresa = Empresa.query.first()
    return render_template(
        "pagos/imprimir_cuotas.html",
        venta=venta,
        empresa=empresa,
        now=datetime.now()
    )
