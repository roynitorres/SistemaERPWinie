from database import db
from models.proveedor import Proveedor
from models.enums import EstadoProveedor
from validators.common_validators import validar_telefono_nicaraguense
from datetime import datetime
import csv
from io import StringIO

def generar_siguiente_codigo_proveedor():
    """Retorna un string con formato 'P001', 'P002', etc."""
    ultimo_proveedor = Proveedor.query.order_by(Proveedor.id.desc()).first()
    next_id = 1 if not ultimo_proveedor else (ultimo_proveedor.id + 1)
    return f"P{next_id:03d}"

def crear_o_actualizar_proveedor(proveedor_id, codigo, nombre_proveedor, nombre_contacto, telefono, departamento, municipio, ruc, direccion, estado):
    """
    Crea o actualiza un proveedor.
    Retorna un tuple: (éxito: bool, mensaje: str)
    """
    # Validaciones básicas
    if not nombre_proveedor or len(nombre_proveedor) < 3:
        return False, "El Nombre del Proveedor debe tener al menos 3 caracteres"
        
    if not nombre_contacto or len(nombre_contacto) < 3:
        return False, "El Nombre del Contacto debe tener al menos 3 caracteres"
        
    if not departamento:
        return False, "El Departamento es obligatorio"

    if not municipio:
        return False, "El Municipio es obligatorio"
        
    es_valido, msg_error = validar_telefono_nicaraguense(telefono)
    if not es_valido:
        return False, msg_error

    # Verificar nombre único
    proveedor_nombre_existente = Proveedor.query.filter(Proveedor.nombre_proveedor == nombre_proveedor).first()
    if proveedor_nombre_existente and (not proveedor_id or proveedor_nombre_existente.id != int(proveedor_id)):
        return False, "Ya existe un proveedor con ese nombre"

    # Verificar RUC único (si fue proporcionado)
    if ruc:
        proveedor_ruc_existente = Proveedor.query.filter(Proveedor.ruc == ruc).first()
        if proveedor_ruc_existente and (not proveedor_id or proveedor_ruc_existente.id != int(proveedor_id)):
            return False, "Ya existe un proveedor con ese número RUC"

    if proveedor_id:
        # ACTUALIZAR PROVEEDOR
        proveedor = db.session.get(Proveedor, int(proveedor_id))
        if not proveedor:
            return False, "Proveedor no encontrado"
            
        # Validar desactivación si hay productos asociados
        es_inactivo_target = (estado == EstadoProveedor.INACTIVO) or (hasattr(estado, 'value') and estado.value == "INACTIVO")
        if es_inactivo_target:
            cant_productos = len(proveedor.productos) if proveedor.productos else 0
            if cant_productos > 0:
                return False, f"No se puede inactivar al proveedor '{proveedor.nombre_proveedor}' porque tiene {cant_productos} producto(s) asociado(s)."
                
        proveedor.nombre_proveedor = nombre_proveedor
        proveedor.nombre_contacto = nombre_contacto
        proveedor.telefono = telefono
        proveedor.departamento = departamento
        proveedor.municipio = municipio
        proveedor.ruc = ruc if ruc else None
        proveedor.direccion = direccion
        proveedor.estado = estado
        
        db.session.commit()
        return True, "Proveedor actualizado correctamente"
    else:
        # CREAR NUEVO PROVEEDOR
        if not codigo:
            codigo = generar_siguiente_codigo_proveedor()
            
        nuevo_proveedor = Proveedor(
            codigo=codigo,
            nombre_proveedor=nombre_proveedor,
            nombre_contacto=nombre_contacto,
            telefono=telefono,
            departamento=departamento,
            municipio=municipio,
            ruc=ruc if ruc else None,
            direccion=direccion,
            estado=estado
        )
        db.session.add(nuevo_proveedor)
        db.session.commit()
        return True, "Proveedor guardado correctamente"

def exportar_proveedores_csv():
    """
    Genera un archivo CSV con la lista de proveedores.
    Retorna el contenido en formato string, incluyendo un BOM de UTF-8 (\ufeff) para compatibilidad con Excel.
    """
    proveedores = Proveedor.query.order_by(Proveedor.id.asc()).all()
    si = StringIO()
    cw = csv.writer(si)
    
    # Encabezados
    cw.writerow(["Código", "Nombre del Proveedor", "Nombre del Contacto", "Teléfono", "Departamento", "Municipio", "RUC", "Dirección", "Estado", "Fecha Creación"])
    
    # Filas
    for p in proveedores:
        estado_str = "Activo" if p.estado == EstadoProveedor.ACTIVO else "Inactivo"
        fecha_creacion_str = p.created_at.strftime("%d/%m/%Y %H:%M") if p.created_at else ""
        cw.writerow([
            p.codigo or f"P{p.id:03d}",
            p.nombre_proveedor,
            p.nombre_contacto,
            p.telefono,
            p.departamento,
            p.municipio,
            p.ruc or "",
            p.direccion or "",
            estado_str,
            fecha_creacion_str
        ])
        
    return "\ufeff" + si.getvalue()
