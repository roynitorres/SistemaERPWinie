import enum

class EstadoCliente(enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"

class EstadoProveedor(enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"

class EstadoCategoria(enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"

class EstadoProducto(enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"

class EstadoVenta(enum.Enum):
    ACTIVA = "ACTIVA"
    ANULADA = "ANULADA"

class TipoVenta(enum.Enum):
    CONTADO = "CONTADO"
    CREDITO = "CREDITO"
