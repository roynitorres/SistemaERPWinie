import enum


class EstadoTenant(str, enum.Enum):
    ACTIVO = "ACTIVO"
    SUSPENDIDO = "SUSPENDIDO"
    EN_PRUEBA = "EN_PRUEBA"
    CANCELADO = "CANCELADO"


class PlanSaaS(str, enum.Enum):
    BASICO = "BASICO"
    ESTANDAR = "ESTANDAR"
    PRO = "PRO"
