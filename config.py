import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-fallback-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

    # Base de Datos Central (SaaS Master DB)
    MASTER_DATABASE_URI = os.environ.get("MASTER_DATABASE_URI", "sqlite:///master.db")
    SQLALCHEMY_BINDS = {
        "master": MASTER_DATABASE_URI
    }

    # Dominio Base del SaaS para resolución dinámica de subdominios
    SAAS_BASE_DOMAIN = os.environ.get("SAAS_BASE_DOMAIN", "localhost:5000")