from models.producto import Producto
from models.enums import EstadoProducto
from database import db
from datetime import datetime

def crear_o_actualizar_producto(
    producto_id, codigo_producto, nombre, marca, estado, 
    categoria_id, proveedor_id, precio_compra, precio_venta, 
    cantidad_comprada, fecha_compra
):
    """
    Crea o actualiza un producto con las validaciones de negocio.
    Retorna un tuple: (éxito: bool, mensaje: str)
    """
    if not codigo_producto:
        return False, "El código del producto es obligatorio"
    if not nombre or len(nombre) < 3:
        return False, "El nombre del producto debe tener al menos 3 caracteres"
    if not marca:
        return False, "La marca es obligatoria"
    if not categoria_id:
        return False, "Debe seleccionar una categoría"
    if not proveedor_id:
        return False, "Debe seleccionar un proveedor"
    if not codigo_producto or not nombre or not marca or not categoria_id or not proveedor_id:
        return False, "Todos los campos obligatorios deben ser llenados"

    if cantidad_comprada <= 0:
        return False, "La cantidad comprada debe ser mayor a cero"
        
    if precio_compra <= 0:
        return False, "El precio de compra debe ser mayor a cero"
        
    if precio_venta <= 0:
        return False, "El precio de venta debe ser mayor a cero"

    # Lógica de Actualización
    if producto_id:
        producto = db.session.get(Producto, int(producto_id))
        if not producto:
            return False, "Producto no encontrado"

        producto.codigo_producto = codigo_producto
        producto.nombre = nombre
        producto.marca = marca
        producto.estado = estado
        producto.categoria_id = categoria_id
        producto.proveedor_id = proveedor_id
        producto.precio_compra = precio_compra
        producto.precio_venta = precio_venta
        
        # En una actualización simple, asumimos que el stock se mantiene o se recalcula
        # (Si se agrega nueva compra, debería haber módulo de compras aparte, 
        # pero aquí actualizamos cantidad_comprada directamente como pidió el diseño original)
        diferencia = cantidad_comprada - producto.cantidad_comprada
        producto.stock = producto.stock + diferencia
        producto.cantidad_comprada = cantidad_comprada
        producto.fecha_compra = fecha_compra
        
        try:
            db.session.commit()
            return True, "Producto actualizado correctamente"
        except Exception as e:
            db.session.rollback()
            return False, f"Error al actualizar el producto: {str(e)}"
            
    # Lógica de Creación
    else:
        producto_existente = Producto.query.filter_by(codigo_producto=codigo_producto, fecha_compra=fecha_compra).first()
        
        if producto_existente:
            # Acumular inventario para el mismo lote
            producto_existente.cantidad_comprada += cantidad_comprada
            producto_existente.stock += cantidad_comprada
            
            # Actualizar otros datos del lote
            producto_existente.nombre = nombre
            producto_existente.marca = marca
            producto_existente.estado = estado
            producto_existente.categoria_id = categoria_id
            producto_existente.proveedor_id = proveedor_id
            producto_existente.precio_compra = precio_compra
            producto_existente.precio_venta = precio_venta
            
            try:
                db.session.commit()
                return True, "El producto fue acumulado al registro de compra existente de esta fecha"
            except Exception as e:
                db.session.rollback()
                return False, f"Error al acumular el producto: {str(e)}"
        else:
            nuevo_producto = Producto(
                codigo_producto=codigo_producto,
                nombre=nombre,
                marca=marca,
                estado=estado,
                categoria_id=categoria_id,
                proveedor_id=proveedor_id,
                precio_compra=precio_compra,
                precio_venta=precio_venta,
                stock=cantidad_comprada,
                cantidad_comprada=cantidad_comprada,
                fecha_compra=fecha_compra
            )
            db.session.add(nuevo_producto)
            
            try:
                db.session.commit()
                return True, "Producto guardado correctamente"
            except Exception as e:
                db.session.rollback()
                return False, f"Error al guardar el producto: {str(e)}"

