# ==========================================================================
# SISTEMA ERP WINIE — SERVIDOR DE PRODUCCIÓN WSGI (run_production.py)
# Servidor multiproceso de alto rendimiento basado en Waitress
# ==========================================================================
import os
from waitress import serve
from app import app

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    threads = int(os.environ.get("THREADS", 8))

    print("=" * 65)
    print(" 🚀 INICIANDO SISTEMA ERP WINIE EN MODO PRODUCCIÓN (WSGI / WAITRESS)")
    print("=" * 65)
    print(f" 📍 Host Escuchando: http://{host}:{port}")
    print(f" 🌐 Acceso Local:    http://localhost:{port}")
    print(f" ⚡ Hilos de Red:    {threads} hilos concurrentes")
    print(f" 🔒 Seguridad:      Modo Debug Desactivado (FLASK_DEBUG=0)")
    print("=" * 65)
    print(" Presione Ctrl+C para detener el servidor de producción.")
    print("=" * 65)

    serve(app, host=host, port=port, threads=threads)
