

from flask import Blueprint
from flask import render_template
from flask import request
from flask import jsonify
from flask import redirect
from flask import url_for
from flask import flash

from flask_login import login_required
from flask_login import current_user

from sqlalchemy import func

from database import db

# Modelos
from models.cliente import Cliente
from models.venta import Venta
from models.pago import Pago
from utils.permisos import roles_required

# Fechas
from datetime import datetime


# ==================================================
# BLUEPRINT
# ==================================================

pagos_bp = Blueprint("pagos",__name__)


# ==================================================
# VISTA PRINCIPAL PAGOS
# ==================================================

@pagos_bp.route("/pagos",methods=["GET"])
@login_required
@roles_required("ADMIN", "VENDEDOR")
def pagos():
    clientes = Cliente.query.order_by(Cliente.nombres.asc()).all()
    ventas = Venta.query.order_by(Venta.fecha_venta.desc()).all()
    
    total_facturado_pagado = 0
    total_facturas = 0
    facturas_pagadas = 0
    facturas_pendientes = 0
    ventas_pendientes = []
    
    for venta in ventas:
        if venta.estado != "ACTIVA":
            continue
    
        total_facturas += 1
    
        total_abonado = sum(
            float(pago.monto_pago)
            for pago in venta.pagos
            if pago.estado == "ACTIVO"
        )
    
        saldo = float(venta.total_venta) - total_abonado
    
        if saldo <= 0:
            facturas_pagadas += 1
            total_facturado_pagado += float(venta.total_venta)
        else:
            facturas_pendientes += 1
            ventas_pendientes.append(venta)
    
    kpis = {
        "total_facturado_pagado": total_facturado_pagado,
        "total_facturas": total_facturas,
        "facturas_pagadas": facturas_pagadas,
        "facturas_pendientes": facturas_pendientes
    }
    


    return render_template(
        "pagos/pagos.html",
        clientes=clientes,
        ventas=ventas,
        ventas_pendientes=ventas_pendientes,
        kpis=kpis
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
        Venta.estado == "ACTIVA"
    ).all()

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
# GUARDAR PAGO
# ==================================================

@pagos_bp.route(

    "/guardar-pago",

    methods=["POST"]

)
@login_required
@roles_required("ADMIN", "VENDEDOR")
def guardar_pago():

    try:
        venta_id = request.form.get("venta_id")
        monto_pago = request.form.get("monto_pago")
        tipo_pago = request.form.get("tipo_pago")
        referencia = request.form.get("referencia")
        observaciones = request.form.get("observaciones")
        fecha_pago_form = request.form.get("fecha_pago")

        if not venta_id:
            return jsonify({"success": False,"message": "Factura inválida"})
        if not monto_pago:
            return jsonify({"success": False,"message": "Ingrese monto"})

        # ==========================================
        # BUSCAR VENTA
        # ==========================================
        venta = Venta.query.get(venta_id)
        if not venta:
            return jsonify({"success": False,"message": "Venta no encontrada"})
        
        # TOTAL ABONADO
        total_abonado = sum(float(pago.monto_pago)for pago in venta.pagos if pago.estado == "ACTIVO")
        # SALDO
        saldo_pendiente = (float(venta.total_venta) - total_abonado)
        # VALIDAR MONTO
        monto_pago = float( monto_pago)
        if monto_pago <= 0:
            return jsonify({"success": False,"message": "Monto inválido"})
        if monto_pago > saldo_pendiente: return jsonify({"success": False,"message": "Monto supera saldo pendiente"})
        fecha_pago = (datetime.strptime(fecha_pago_form, "%Y-%m-%d")
            if fecha_pago_form
            else datetime.now())
        
        # CREAR PAGO
        nuevo_pago = Pago(
            venta_id=venta.id,
            usuario_id=current_user.id,
            monto_pago=monto_pago,
            tipo_pago=tipo_pago,
            referencia=referencia,
            observaciones=observaciones,
            fecha_pago = fecha_pago,
            estado="ACTIVO"
        )

        db.session.add(nuevo_pago)
        db.session.commit()
        # RESPUESTA
        return jsonify({"success": True,"message": "Pago registrado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False,"message": str(e)})


# ==================================================
# ANULAR PAGO
# ==================================================

@pagos_bp.route("/anular-pago/<int:pago_id>", methods=["POST"])
@login_required
@roles_required("ADMIN")
def anular_pago(pago_id):
    try:
        # BUSCAR PAGO
        pago = Pago.query.get(pago_id)
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