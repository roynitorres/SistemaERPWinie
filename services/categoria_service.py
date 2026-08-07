from models.categoria import Categoria
from models.enums import EstadoCategoria
from database import db

def generar_siguiente_codigo_categoria():
    ultima_categoria = Categoria.query.order_by(Categoria.id.desc()).first()
    next_id = 1 if not ultima_categoria else (ultima_categoria.id + 1)
    return f"C{next_id:03d}"

def crear_o_actualizar_categoria(categoria_id, codigo, nombre, descripcion, estado):
    """
    Crea o actualiza una categoría.
    Retorna un tuple: (éxito: bool, mensaje: str)
    """
    if not nombre or len(nombre) < 3:
        return False, "El nombre de la categoría debe tener al menos 3 caracteres"

    # Verificar nombre único
    categoria_existente = Categoria.query.filter_by(nombre=nombre).first()
    if categoria_existente and (not categoria_id or categoria_existente.id != int(categoria_id)):
        return False, "Ya existe una categoría con ese nombre"

    # Lógica de Actualización
    if categoria_id:
        categoria = db.session.get(Categoria, int(categoria_id))
        if not categoria:
            return False, "Categoría no encontrada"

        if not codigo or codigo == "None":
            codigo = generar_siguiente_codigo_categoria()

        # Validar desactivación (bloquear si tiene productos registrados bajo ella)
        if estado == EstadoCategoria.INACTIVO and categoria.estado != EstadoCategoria.INACTIVO:
            if categoria.productos:
                return False, "No se puede desactivar la categoría porque tiene productos asociados"

        categoria.codigo = codigo
        categoria.nombre = nombre
        categoria.descripcion = descripcion
        categoria.estado = estado
        
        try:
            db.session.commit()
            return True, "Categoría actualizada correctamente"
        except Exception as e:
            db.session.rollback()
            return False, f"Error al actualizar la categoría: {str(e)}"
            
    # Lógica de Creación
    else:
        nueva_categoria = Categoria(
            codigo=codigo,
            nombre=nombre,
            descripcion=descripcion,
            estado=estado
        )
        db.session.add(nueva_categoria)
        
        try:
            db.session.commit()
            return True, "Categoría guardada correctamente"
        except Exception as e:
            db.session.rollback()
            return False, f"Error al guardar la categoría: {str(e)}"
