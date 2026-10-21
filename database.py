from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from services.saas.tenant_engine import TenantRoutingSession

db = SQLAlchemy(session_options={"class_": TenantRoutingSession})

migrate = Migrate()