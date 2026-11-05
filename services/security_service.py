import os
import time
import threading
from datetime import datetime, UTC
from sqlalchemy import inspect, text

# ==========================================================
# PARÁMETROS GLOBALES DE SEGURIDAD
# ==========================================================

# Intentos fallidos permitidos antes de bloquear la cuenta
MAX_INTENTOS_LOGIN = 5

# Tiempo de bloqueo de la cuenta en minutos tras exceder el límite
MINUTOS_BLOQUEO_CUENTA = 15

# Máximo de intentos permitidos por IP por ventana de tiempo (60s) contra ataques automatizados
MAX_INTENTOS_POR_MINUTO_IP = 10
VENTANA_RATE_LIMIT_IP_SEGUNDOS = 60

# Tiempo máximo de inactividad antes de cerrar sesión (15 minutos)
SESSION_IDLE_TIMEOUT_SECONDS = 900

# Tiempo previo para advertencia en modal frontend (2 minutos = 120 segundos)
SESSION_WARN_BEFORE_SECONDS = 120


# ==========================================================
# RATE LIMITER EN MEMORIA POR IP (THREAD-SAFE)
# ==========================================================

class IPRateLimiter:
    """
    Limitador de velocidad de peticiones por IP en memoria.
    Previene inundaciones por fuerza bruta rápida desde un mismo origen.
    """
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.ip_records = {}  # ip: [timestamp1, timestamp2, ...]
        self.lock = threading.Lock()

    def _limpiar_antiguos(self, now: float):
        """Elimina registros fuera de la ventana activa para evitar consumo de memoria."""
        cutoff = now - self.window_seconds
        keys_to_delete = []
        for ip, timestamps in self.ip_records.items():
            valid_ts = [ts for ts in timestamps if ts > cutoff]
            if valid_ts:
                self.ip_records[ip] = valid_ts
            else:
                keys_to_delete.append(ip)
        for ip in keys_to_delete:
            del self.ip_records[ip]

    def esta_bloqueada(self, ip: str) -> bool:
        """Determina si la IP ha excedido el límite de solicitudes por ventana."""
        if not ip:
            return False
        now = time.time()
        with self.lock:
            self._limpiar_antiguos(now)
            timestamps = self.ip_records.get(ip, [])
            return len(timestamps) >= self.max_requests

    def registrar_intento(self, ip: str):
        """Registra un intento de petición desde la IP."""
        if not ip:
            return
        now = time.time()
        with self.lock:
            self._limpiar_antiguos(now)
            if ip not in self.ip_records:
                self.ip_records[ip] = []
            self.ip_records[ip].append(now)

    def limpiar_ip(self, ip: str):
        """Limpia el historial de una IP tras un login exitoso."""
        if not ip:
            return
        with self.lock:
            if ip in self.ip_records:
                del self.ip_records[ip]


# Instancia singleton del limitador de IP
ip_limiter = IPRateLimiter(
    max_requests=MAX_INTENTOS_POR_MINUTO_IP,
    window_seconds=VENTANA_RATE_LIMIT_IP_SEGUNDOS
)


# ==========================================================
# MIGRACIÓN SEGURA DE COLUMNAS DE SEGURIDAD (SQLITE RESILIENTE)
# ==========================================================

def migrar_columnas_seguridad(engine):
    """
    Verifica y añade las columnas 'intentos_fallidos' y 'bloqueado_hasta'
    a la tabla 'usuarios' si no existen, evitando errores 'no such column' en SQLite.
    """
    try:
        inspector = inspect(engine)
        if "usuarios" not in inspector.get_table_names():
            return

        columnas = [col["name"] for col in inspector.get_columns("usuarios")]

        with engine.connect() as conn:
            if "intentos_fallidos" not in columnas:
                conn.execute(text("ALTER TABLE usuarios ADD COLUMN intentos_fallidos INTEGER DEFAULT 0"))
            if "bloqueado_hasta" not in columnas:
                conn.execute(text("ALTER TABLE usuarios ADD COLUMN bloqueado_hasta TIMESTAMP"))
            conn.commit()
    except Exception as e:
        print(f"Nota de migración columnas seguridad: {e}")


def migrar_todas_las_bases_seguridad(base_dir=None):
    """
    Aplica la migración de seguridad en la base principal y en todos los
    tenants existentes en instance/tenants/.
    """
    from database import db
    try:
        # 1. Base de datos principal
        migrar_columnas_seguridad(db.engine)

        # 2. Tenants en instance/tenants
        if not base_dir:
            base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        
        tenants_dir = os.path.join(base_dir, "instance", "tenants")
        if os.path.exists(tenants_dir):
            from sqlalchemy import create_engine
            for archivo in os.listdir(tenants_dir):
                if archivo.endswith(".db"):
                    db_path = os.path.join(tenants_dir, archivo)
                    t_engine = create_engine(f"sqlite:///{db_path}")
                    migrar_columnas_seguridad(t_engine)
                    t_engine.dispose()
    except Exception as e:
        print(f"Nota en migración de tenants para seguridad: {e}")
