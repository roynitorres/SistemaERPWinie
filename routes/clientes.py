from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash

from flask_login import login_required
from utils.permisos import roles_required

# Modelo cliente
from models.cliente import Cliente

# Base datos
from database import db
from datetime import datetime
 
from models.usuario import Usuario
from models.rol import Rol

# ==================================================
# BLUEPRINT CLIENTES
# ==================================================

clientes_bp = Blueprint("clientes",__name__)

def generar_password_temporal():
    return "@123456789"


# VISTA CLIENTES
@clientes_bp.route("/clientes",methods=["GET", "POST"])
@login_required
@roles_required("ADMIN", "VENDEDOR")
def clientes():

    mensaje = ""

    # ==========================================
    # POST
    # ==========================================

    if request.method == "POST":
        cliente_id = request.form.get("cliente_id")
        nombre = request.form.get("nombres", "").strip().title()
        telefono = request.form.get("telefono", "").strip()
        email = request.form.get("email", "").strip()
        ciudad = request.form.get("ciudad", "").strip().title()
        direccion = request.form.get("direccion", "").strip().title()
        estado_val = request.form.get("estado", "ACTIVO")
        estado = True if estado_val == "ACTIVO" else False

        # Validar campos obligatorios
        if not nombre:
            flash("El Nombre / Razón Social es obligatorio", "danger")
            return redirect(url_for("clientes.clientes"))

        # Validar teléfono (si se ingresa, debe ser de exactamente 8 números)
        if not telefono or not telefono.isdigit() or len(telefono) != 8:
            flash("El teléfono debe contener exactamente 8 números", "danger")
            return redirect(url_for("clientes.clientes"))

        cliente_nombre_existente = Cliente.query.filter(Cliente.nombres == nombre).first()
        
        if cliente_nombre_existente and (
            not cliente_id or cliente_nombre_existente.id != int(cliente_id)
        ):
            flash("Ya existe un cliente con ese nombre", "danger")
            return redirect(url_for("clientes.clientes"))
        
        
        cliente_telefono_existente = Cliente.query.filter(
            Cliente.telefono == telefono
        ).first()
        
        if telefono and cliente_telefono_existente and (
            not cliente_id or cliente_telefono_existente.id != int(cliente_id)
        ):
            flash("Ya existe un cliente con ese número de teléfono", "danger")
            return redirect(url_for("clientes.clientes"))

        # ======================================
        # UPDATE
        # ======================================
        if cliente_id:
            cliente = Cliente.query.get(cliente_id)
            if cliente:
                cliente.nombres = nombre
                cliente.apellidos = ""
                cliente.telefono = telefono
                if cliente.usuario:
                    cliente.usuario.username = telefono
                cliente.email = email
                cliente.ciudad = ciudad
                cliente.direccion = direccion
                cliente.estado = estado
                mensaje = "Cliente actualizado correctamente"
        # ======================================
        # INSERT
        # ======================================
        else:
            ultimo_cliente = Cliente.query.order_by(Cliente.id.desc()).first()
            next_id = 1 if not ultimo_cliente else (ultimo_cliente.id + 1)
            codigo = f"C{next_id:03d}"

            nuevo_cliente = Cliente(
                codigo=codigo,
                nombres=nombre,
                apellidos="",
                telefono=telefono,
                email=email,
                ciudad=ciudad,
                direccion=direccion,
                fecha_ingreso=datetime.now().date(),
                estado=estado
            )
            db.session.add(nuevo_cliente)
            db.session.flush()

            rol_cliente = Rol.query.filter_by(nombre="CLIENTE").first()
            
            if rol_cliente and telefono:
                usuario_existente = Usuario.query.filter_by(username=telefono).first()
                if not usuario_existente:
                    password_temporal = generar_password_temporal()
                    usuario_cliente = Usuario(
                        username=telefono,
                        rol_id=rol_cliente.id,
                        cliente_id=nuevo_cliente.id,
                        estado=True,
                        debe_cambiar_password=True
                    )
                    usuario_cliente.set_password(password_temporal)
                    db.session.add(usuario_cliente)
                    mensaje = "Cliente guardado correctamente"

        db.session.commit()
        flash(mensaje, "success")
        return redirect(url_for("clientes.clientes"))

    # ==========================================
    # GET
    # ==========================================
    lista_clientes = Cliente.query.order_by(Cliente.id.asc()).all()

    # Calcular KPIs
    total_clientes = len(lista_clientes)
    activos = Cliente.query.filter_by(estado=True).count()
    inactivos = Cliente.query.filter_by(estado=False).count()

    # Nuevos este mes
    from datetime import date
    import calendar
    today = date.today()
    first_day_current_month = date(today.year, today.month, 1)

    nuevos_este_mes = Cliente.query.filter(Cliente.fecha_ingreso >= first_day_current_month).count()

    # Mes anterior
    if today.month == 1:
        first_day_prev_month = date(today.year - 1, 12, 1)
        last_day_prev_month = date(today.year - 1, 12, 31)
    else:
        first_day_prev_month = date(today.year, today.month - 1, 1)
        _, last_day = calendar.monthrange(today.year, today.month - 1)
        last_day_prev_month = date(today.year, today.month - 1, last_day)

    nuevos_mes_anterior = Cliente.query.filter(
        Cliente.fecha_ingreso >= first_day_prev_month,
        Cliente.fecha_ingreso <= last_day_prev_month
    ).count()

    # Crecimiento
    if nuevos_mes_anterior > 0:
        porcentaje_growth = round(((nuevos_este_mes - nuevos_mes_anterior) / nuevos_mes_anterior) * 100)
    else:
        porcentaje_growth = 100 if nuevos_este_mes > 0 else 0

    kpis = {
        "total": total_clientes,
        "activos": activos,
        "inactivos": inactivos,
        "nuevos": nuevos_este_mes,
        "porcentaje_nuevos": f"{porcentaje_growth:+d}" if porcentaje_growth != 0 else "0"
    }

    # Siguiente código
    ultimo_cliente = Cliente.query.order_by(Cliente.id.desc()).first()
    next_id = 1 if not ultimo_cliente else (ultimo_cliente.id + 1)
    siguiente_codigo = f"C{next_id:03d}"

    return render_template(
        "clientes/clientes.html",
        clientes=lista_clientes,
        kpis=kpis,
        siguiente_codigo=siguiente_codigo
    )


# ==================================================
# EXPORTAR CLIENTES A CSV
# ==================================================

@clientes_bp.route("/clientes/exportar")
@login_required
@roles_required("ADMIN")
def exportar_clientes():
    import csv
    from io import StringIO
    from flask import Response

    clientes = Cliente.query.order_by(Cliente.id.asc()).all()

    # Crear buffer
    si = StringIO()
    cw = csv.writer(si)

    # Encabezados (Sin RUC ni Categoría)
    cw.writerow(["Código", "Nombre / Razón Social", "Teléfono", "Email", "Ciudad", "Estado"])

    # Escribir filas
    for c in clientes:
        estado_str = "Activo" if c.estado else "Inactivo"
        cw.writerow([
            c.codigo or f"C{c.id:03d}",
            c.nombres,
            c.telefono,
            c.email or "",
            c.ciudad or "",
            estado_str
        ])

    output = si.getvalue()

    return Response(
        "\ufeff" + output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=clientes.csv"}
    )

@clientes_bp.route("/clientes/restaurar-password/<int:cliente_id>", methods=["POST"])
@login_required
@roles_required("ADMIN")
def restaurar_password_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    if not cliente.usuario:
        flash("Este cliente no tiene usuario asociado", "warning")
        return redirect(url_for("clientes.clientes"))

    password_temporal = generar_password_temporal()

    cliente.usuario.set_password(password_temporal)
    cliente.usuario.debe_cambiar_password = True

    db.session.commit()

    flash(
        f"Contraseña restaurada correctamente. Usuario: {cliente.usuario.username}",
        "success"
    )

    return redirect(url_for("clientes.clientes"))