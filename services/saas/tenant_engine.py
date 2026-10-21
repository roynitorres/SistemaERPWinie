import os
from typing import Optional, Dict
from flask import g, has_app_context, current_app
from flask_sqlalchemy.session import Session as FSASession
from sqlalchemy import create_engine, Engine
from sqlalchemy.pool import NullPool

# Registro en memoria de motores de conexión por tenant
_TENANT_ENGINES: Dict[str, Engine] = {}


class TenantRoutingSession(FSASession):
    """
    Sesión personalizada de SQLAlchemy para Multi-Tenancy.
    Enruta dinámicamente las consultas hacia la base de datos correspondiente:
    - Modelos con __bind_key__ == 'master' -> master.db (Super Admin)
    - Resto de modelos operativos -> base de datos aislada del tenant activo en `g`
    - Fallback -> base de datos por defecto (database.db)
    """

    def get_bind(self, mapper=None, clause=None, bind=None, **kw):
        # 1. Rutas del Super Admin y catálogo maestro
        if mapper and getattr(mapper.class_, "__bind_key__", None) == "master":
            return super().get_bind(mapper=mapper, clause=clause, bind=bind, **kw)

        # 2. Rutas operativas de un tenant específico
        if has_app_context() and hasattr(g, "tenant_engine") and g.tenant_engine is not None:
            return g.tenant_engine

        # 3. Fallback predeterminado (desarrollo base)
        return super().get_bind(mapper=mapper, clause=clause, bind=bind, **kw)


def get_tenant_db_path(slug: str) -> str:
    """Devuelve la ruta absoluta al archivo SQLite del tenant."""
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    return os.path.join(base_dir, "instance", "tenants", f"{slug}.db")


def get_tenant_engine(slug: str) -> Engine:
    """
    Obtiene o inicializa el motor de conexión para un tenant específico.
    Utiliza NullPool para SQLite para evitar bloqueos de archivos en Windows.
    """
    if slug in _TENANT_ENGINES:
        return _TENANT_ENGINES[slug]

    db_path = get_tenant_db_path(slug)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    db_uri = f"sqlite:///{db_path}"
    engine = create_engine(
        db_uri,
        poolclass=NullPool,
        connect_args={"check_same_thread": False}
    )

    _TENANT_ENGINES[slug] = engine
    return engine


def dispose_tenant_engine(slug: str) -> None:
    """Libera y cierra la conexión del motor de un tenant si existe."""
    if slug in _TENANT_ENGINES:
        engine = _TENANT_ENGINES.pop(slug)
        engine.dispose()
