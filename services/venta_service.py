from database import db
from models.venta import Venta
from models.detalle_venta import DetalleVenta
from models.producto import Producto
from models.empresa import Empresa
from models.cuota_venta import CuotaVenta
from models.pago import Pago
from models.banco import Banco
from models.enums import EstadoVenta, TipoVenta, EstadoProducto
from datetime import datetime, date, timedelta

def generar_numero_factura():
    """
    Genera y retorna el siguiente número correlativo de factura
    con base en la configuración de la Empresa y la última venta.
    Usa WITH FOR UPDATE para evitar race condition en entornos concurrentes.
    """
    empresa = Empresa.query.first()

    serie = "F001"
    correlativo_base = "00001"

    if empresa:
        serie = empresa.serie_factura or "F001"
        correlativo_base = empresa.correlativo or "00001"

    # WITH FOR UPDATE: bloquea la fila para evitar que dos usuarios generen el mismo correlativo
    ultima_venta = Venta.query.order_by(Venta.id.desc()).with_for_update().first()

    if not ultima_venta:
        return f"{serie}-{correlativo_base}"

    try:
        ultimo_correlativo = int(ultima_venta.numero_factura.split("-")[1])
    except Exception:
        ultimo_correlativo = int(correlativo_base)

    nuevo_correlativo = ultimo_correlativo + 1

    return f"{serie}-{nuevo_correlativo:05d}"

def crear_venta(data, usuario_id, descuento_maximo):
    """
    Crea una nueva venta de forma transaccional, validando reglas de negocio, 
    descuentos máximos del usuario y existencia de inventario.
    
    Retorna una tupla: (éxito: bool, respuesta: dict/str)
    """
    try:
        # Extraer datos principales
        cliente_id = data.get("cliente_id")
        tipo_venta = TipoVenta(data.get("tipo_venta"))
        observaciones = data.get("observaciones")
        productos_lista = data.get("productos")
        fecha_venta_str = data.get("fecha_venta")
        fecha_limite_credito_str = data.get("fecha_limite_credito")
        
        # Validaciones iniciales
        if not cliente_id:
            return False, "Seleccione un cliente válido"
        if not productos_lista:
            return False, "Debe agregar al menos un producto a la venta"

        # Calcular totales y validar límite de descuentos
        subtotal = 0
        
        for item in productos_lista:
            cantidad = int(item.get("cantidad", 0))
            precio = float(item.get("precio", 0))
            descuento_porcentaje = float(item.get("descuento_porcentaje", 0))
            
            if descuento_porcentaje < 0:
                return False, "El porcentaje de descuento no puede ser negativo"
            
            if descuento_porcentaje > descuento_maximo:
                return False, f"Su rol únicamente permite un máximo de {descuento_maximo}% de descuento"
            
            bruto = cantidad * precio
            descuento_monto = bruto * (descuento_porcentaje / 100)
            subtotal += bruto - descuento_monto
            
        empresa = Empresa.query.first()
        iva_porcentaje = float(empresa.iva) if empresa else 15
        iva = subtotal * (iva_porcentaje / 100)
        total = subtotal + iva

        # Extraer método de pago y datos de cobro
        metodo_pago = data.get("metodo_pago", "efectivo")
        monto_recibido_raw = data.get("monto_recibido")
        banco_id_raw = data.get("banco_id")
        banco_nombre = str(data.get("banco_nombre") or "").strip()
        referencia = str(data.get("referencia") or "").strip()

        # Validación obligatoria para ventas de contado
        if tipo_venta == TipoVenta.CONTADO:
            if metodo_pago == "transfer":
                if not banco_nombre and not banco_id_raw:
                    return False, "Debe especificar el banco para el pago por transferencia."
                if not referencia:
                    return False, "Debe ingresar el número de referencia para el pago por transferencia."
            else:
                # Efectivo
                if monto_recibido_raw is None or str(monto_recibido_raw).strip() == "":
                    return False, "Debe ingresar el monto recibido del cliente para procesar la venta al contado."
                try:
                    monto_recibido_val = float(monto_recibido_raw)
                    if monto_recibido_val <= 0:
                        return False, "El monto recibido debe ser mayor a cero."
                    if monto_recibido_val < total - 0.05:
                        return False, f"El monto recibido (C$ {monto_recibido_val:.2f}) no cubre el total de la venta (C$ {total:.2f})."
                except (ValueError, TypeError):
                    return False, "El monto recibido ingresado no es válido."

        # Formateo de fechas
        if fecha_venta_str:
            try:
                v_date = datetime.strptime(fecha_venta_str, "%Y-%m-%d").date()
                fecha_venta = datetime.combine(v_date, datetime.now().time())
            except Exception:
                fecha_venta = datetime.now()
        else:
            fecha_venta = datetime.now()
        fecha_limite_credito = datetime.strptime(fecha_limite_credito_str, "%Y-%m-%d").date() if fecha_limite_credito_str else None

        # Creación cabecera de la venta
        nueva_venta = Venta(
            numero_factura=generar_numero_factura(),
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            fecha_venta=fecha_venta,
            fecha_limite_credito=fecha_limite_credito,
            tipo_venta=tipo_venta,
            total_venta=total,
            observaciones=observaciones
        )
        
        db.session.add(nueva_venta)
        db.session.flush() # Flush para obtener nueva_venta.id sin hacer commit aún
        
        # Resolver banco si aplica a venta por transferencia
        banco_id = None
        if tipo_venta == TipoVenta.CONTADO and metodo_pago == "transfer":
            if banco_id_raw and str(banco_id_raw).isdigit():
                banco_obj = db.session.get(Banco, int(banco_id_raw))
                if banco_obj:
                    banco_id = banco_obj.id
            if not banco_id and banco_nombre:
                banco_obj = Banco.query.filter(Banco.nombre.ilike(f"%{banco_nombre}%")).first()
                if banco_obj:
                    banco_id = banco_obj.id
                else:
                    nuevo_banco = Banco(nombre=banco_nombre, estado="ACTIVO")
                    db.session.add(nuevo_banco)
                    db.session.flush()
                    banco_id = nuevo_banco.id
        
        # Procesamiento e inserción de detalles de productos
        for item in productos_lista:
            producto = db.session.get(Producto, int(item["producto_id"]))
            
            if not producto:
                db.session.rollback()
                return False, "Un producto de la lista no fue encontrado en la base de datos"
            
            cantidad = int(item["cantidad"])
            if cantidad > producto.stock:
                db.session.rollback()
                return False, f"Stock insuficiente para el producto: {producto.nombre} (Stock actual: {producto.stock})"
                
            precio = float(item["precio"])
            descuento_porcentaje = float(item.get("descuento_porcentaje", 0))
            
            bruto = cantidad * precio
            descuento_monto = bruto * (descuento_porcentaje / 100)
            subtotal_item = bruto - descuento_monto
            
            detalle = DetalleVenta(
                venta_id=nueva_venta.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=precio,
                descuento_porcentaje=descuento_porcentaje,
                descuento_monto=descuento_monto,
                subtotal=subtotal_item
            )
            db.session.add(detalle)
            
            # Ajustar inventario
            producto.stock -= cantidad

        # Si la venta es a Crédito, crear el plan de cuotas
        if tipo_venta == TipoVenta.CREDITO:
            cuotas_lista = data.get("cuotas", [])
            if cuotas_lista:
                for idx, c_item in enumerate(cuotas_lista, start=1):
                    num_cuota = int(c_item.get("numero_cuota", idx))
                    monto_c = float(c_item.get("monto_cuota", 0))
                    f_venc_str = c_item.get("fecha_vencimiento")
                    f_gracia_str = c_item.get("fecha_vencimiento_gracia")
                    dias_g = int(c_item.get("dias_gracia", 2))

                    f_venc = datetime.strptime(f_venc_str, "%Y-%m-%d").date() if f_venc_str else (fecha_limite_credito or date.today())
                    f_gracia = datetime.strptime(f_gracia_str, "%Y-%m-%d").date() if f_gracia_str else (f_venc + timedelta(days=dias_g))

                    nueva_cuota = CuotaVenta(
                        venta_id=nueva_venta.id,
                        numero_cuota=num_cuota,
                        monto_cuota=monto_c,
                        monto_abonado=0.00,
                        fecha_vencimiento=f_venc,
                        fecha_vencimiento_gracia=f_gracia,
                        dias_gracia=dias_g,
                        estado="PENDIENTE"
                    )
                    db.session.add(nueva_cuota)
            else:
                # Cuota por defecto si no se especificó tabla
                f_venc = fecha_limite_credito or (date.today() + timedelta(days=30))
                nueva_cuota = CuotaVenta(
                    venta_id=nueva_venta.id,
                    numero_cuota=1,
                    monto_cuota=total,
                    monto_abonado=0.00,
                    fecha_vencimiento=f_venc,
                    fecha_vencimiento_gracia=f_venc + timedelta(days=2),
                    dias_gracia=2,
                    estado="PENDIENTE"
                )
                db.session.add(nueva_cuota)

        # Si la venta es de Contado, registrar el pago de inmediato
        if tipo_venta == TipoVenta.CONTADO:
            tipo_pago_str = "TRANSFERENCIA" if metodo_pago == "transfer" else "EFECTIVO"
            pago_contado = Pago(
                venta_id=nueva_venta.id,
                usuario_id=usuario_id,
                cuota_id=None,
                banco_id=banco_id if metodo_pago == "transfer" else None,
                monto_pago=total,
                monto_efectivo=0.00 if metodo_pago == "transfer" else total,
                monto_transferencia=total if metodo_pago == "transfer" else 0.00,
                tipo_pago=tipo_pago_str,
                referencia=referencia if metodo_pago == "transfer" else None,
                observaciones=observaciones or (f"Pago al contado - {tipo_pago_str}"),
                fecha_pago=fecha_venta,
                estado="ACTIVO"
            )
            db.session.add(pago_contado)
            
        # Transacción completada con éxito
        db.session.commit()
        return True, {"mensaje": "Venta procesada y guardada correctamente", "venta_id": nueva_venta.id}
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error interno procesando la venta: {str(e)}"

def anular_venta_service(venta_id):
    """
    Anula una venta y devuelve el stock de los productos.
    No permite anular ventas que ya están pagadas o anuladas.
    Retorna una tupla: (éxito: bool, mensaje: str)
    """
    try:
        venta = db.session.get(Venta, int(venta_id))
        if not venta:
            return False, "Venta no encontrada"

        if venta.estado == EstadoVenta.ANULADA:
            return False, "La factura ya se encuentra anulada."

        # Validar si está pagada (Asumiendo que 'ACTIVO' es un estado de pago no modificado aún)
        total_abonado = sum(float(p.monto_pago) for p in venta.pagos if p.estado == "ACTIVO")
        saldo_pendiente = float(venta.total_venta) - total_abonado

        # Se puede anular si es al contado y está pagada?
        # En la lógica anterior de pagos.py, dice "No se puede anular una factura que ya está pagada"
        # pero para ventas al contado están pagadas de inmediato.
        # Oh, revisando la lógica original de pagos.py:
        if saldo_pendiente <= 0 and total_abonado > 0 and venta.tipo_venta == TipoVenta.CREDITO:
            return False, "No se puede anular una factura de crédito que ya tiene pagos registrados que cubren el total."

        # Revertir stock
        for detalle in venta.detalle_ventas:
            detalle.producto.stock += detalle.cantidad
            # Reactivar producto si estaba inactivo y ahora tiene stock
            if detalle.producto.stock > 0 and detalle.producto.estado != EstadoProducto.ACTIVO:
                detalle.producto.estado = EstadoProducto.ACTIVO 

        for p in venta.pagos:
            p.estado = "ANULADO"
            p.motivo_anulacion = "Factura anulada"

        venta.estado = EstadoVenta.ANULADA
        db.session.commit()
        return True, "Factura anulada correctamente"

    except Exception as e:
        db.session.rollback()
        return False, f"Error interno al anular la venta: {str(e)}"
