from database import db
from models.cliente import Cliente
from models.usuario import Usuario
from models.rol import Rol
from models.enums import EstadoCliente
from validators.common_validators import validar_telefono_nicaraguense
from datetime import datetime
import csv
import secrets
from io import StringIO

def generar_siguiente_codigo_cliente():
    """Retorna un string con formato 'C001', 'C002', etc."""
    ultimo_cliente = Cliente.query.order_by(Cliente.id.desc()).first()
    next_id = 1 if not ultimo_cliente else (ultimo_cliente.id + 1)
    return f"C{next_id:03d}"

def generar_password_temporal():
    """Genera una contraseña temporal limpia y fácil de compartir para el cliente."""
    import random
    return f"Cliente{random.randint(1000, 9999)}"

def crear_o_actualizar_cliente(cliente_id, nombre, telefono, ciudad, estado):
    """
    Crea o actualiza un cliente.
    Retorna un tuple: (éxito: bool, mensaje: str)
    """
    # Validaciones básicas
    if not nombre or len(nombre) < 3:
        return False, "El Nombre / Razón Social debe tener al menos 3 caracteres"
        
    if not ciudad:
        return False, "La Ciudad es obligatoria"
        
    es_valido, msg_error = validar_telefono_nicaraguense(telefono)
    if not es_valido:
        return False, msg_error

    # Verificar nombre único
    cliente_nombre_existente = Cliente.query.filter(Cliente.nombres == nombre).first()
    if cliente_nombre_existente and (not cliente_id or cliente_nombre_existente.id != int(cliente_id)):
        return False, "Ya existe un cliente con ese nombre"

    # Verificar teléfono único
    cliente_telefono_existente = Cliente.query.filter(Cliente.telefono == telefono).first()
    if telefono and cliente_telefono_existente and (not cliente_id or cliente_telefono_existente.id != int(cliente_id)):
        return False, "Ya existe un cliente con ese número de teléfono"

    if cliente_id:
        # ACTUALIZAR CLIENTE
        cliente = db.session.get(Cliente, int(cliente_id))
        if not cliente:
            return False, "Cliente no encontrado"
            
        # Validar que no se puede inactivar si tiene facturas pendientes
        es_inactivo_target = (estado == EstadoCliente.INACTIVO) or (hasattr(estado, 'value') and estado.value == "INACTIVO")
        if es_inactivo_target:
            for venta in cliente.ventas:
                if venta.estado.value == "ACTIVA":
                    total_abonado = sum(
                        float(pago.monto_pago)
                        for pago in venta.pagos
                        if pago.estado == "ACTIVO"
                    )
                    saldo_pendiente = float(venta.total_venta) - total_abonado
                    if saldo_pendiente > 0.01:
                        return False, f"No se puede inactivar al cliente porque tiene facturas pendientes de pago (Factura #{venta.numero_factura} con saldo de C$ {saldo_pendiente:.2f})."

        cliente.nombres = nombre
        cliente.telefono = telefono
        if cliente.usuario:
            cliente.usuario.username = telefono
        cliente.ciudad = ciudad
        cliente.estado = estado
        
        db.session.commit()
        return True, "Cliente actualizado correctamente"
    else:
        # CREAR NUEVO CLIENTE
        codigo = generar_siguiente_codigo_cliente()
        nuevo_cliente = Cliente(
            codigo=codigo,
            nombres=nombre,
            telefono=telefono,
            ciudad=ciudad,
            estado=estado
        )
        db.session.add(nuevo_cliente)
        db.session.flush() # Para obtener el ID del cliente antes de hacer commit

        # Asignar usuario al nuevo cliente
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
                    debe_cambiar_password=True,
                    password_temporal_plana=password_temporal
                )
                usuario_cliente.set_password(password_temporal)
                db.session.add(usuario_cliente)
                db.session.commit()
                return True, f"Cliente guardado. Credenciales de acceso al portal — Usuario: {telefono} | Contraseña temporal: {password_temporal}"

        db.session.commit()
        return True, "Cliente guardado correctamente"

def exportar_clientes_csv():
    """
    Genera un archivo CSV con la lista de clientes.
    Retorna el contenido en formato string, incluyendo un BOM de UTF-8 (\ufeff) para compatibilidad con Excel.
    """
    clientes = Cliente.query.order_by(Cliente.id.asc()).all()
    si = StringIO()
    cw = csv.writer(si)
    
    # Encabezados
    cw.writerow(["Código", "Nombre / Razón Social", "Teléfono", "Ciudad", "Estado"])
    
    # Filas
    for c in clientes:
        estado_str = "Activo" if c.estado == EstadoCliente.ACTIVO else "Inactivo"
        cw.writerow([
            c.codigo or f"C{c.id:03d}",
            c.nombres,
            c.telefono,
            c.ciudad or "",
            estado_str
        ])
        
    return "\ufeff" + si.getvalue()

def restaurar_password_cliente_service(cliente_id):
    """
    Restaura la contraseña del usuario asociado al cliente a su valor temporal por defecto.
    Retorna un tuple: (éxito: bool, mensaje: str, username: str)
    """
    cliente = db.session.get(Cliente, int(cliente_id))
    if not cliente:
        return False, "Cliente no encontrado", None
        
    if not cliente.usuario:
        return False, "Este cliente no tiene usuario asociado", None

    if cliente.usuario.debe_cambiar_password:
        return False, f"El cliente aún no ha utilizado su contraseña temporal activa ('{cliente.usuario.password_temporal_plana or 'Temporal'}'). Puedes entregarle sus credenciales en 'Ver credenciales'.", None

    password_temporal = generar_password_temporal()
    cliente.usuario.set_password(password_temporal)
    cliente.usuario.debe_cambiar_password = True
    cliente.usuario.password_temporal_plana = password_temporal
    db.session.commit()
    
    return True, f"Contraseña restaurada. Credenciales — Usuario: {cliente.usuario.username} | Nueva contraseña temporal: {password_temporal}", cliente.usuario.username
