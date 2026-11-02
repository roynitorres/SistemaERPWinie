from app import app
from database import db
from models.rol import Rol
from models.usuario import Usuario
from models.categoria import Categoria
from models.enums import EstadoCategoria

with app.app_context():
    # Asegurar que todas las tablas existan
    db.create_all()

    # ==============================================
    # 1. CREAR / ACTUALIZAR ROLES BASE
    # ==============================================
    roles_base = [
        {
            "nombre": "ADMIN",
            "descripcion": "Administrador del sistema",
            "descuento_maximo": 100
        },
        {
            "nombre": "VENDEDOR",
            "descripcion": "Usuario de ventas con permisos limitados",
            "descuento_maximo": 5
        },
        {
            "nombre": "CLIENTE",
            "descripcion": "Acceso al portal del cliente",
            "descuento_maximo": 0
        }
    ]

    for item in roles_base:
        rol = Rol.query.filter_by(nombre=item["nombre"]).first()
        if not rol:
            rol = Rol(
                nombre=item["nombre"],
                descripcion=item["descripcion"],
                descuento_maximo=item["descuento_maximo"]
            )
            db.session.add(rol)
            print(f"Rol {item['nombre']} creado")
        else:
            rol.descripcion = item["descripcion"]
            rol.descuento_maximo = item["descuento_maximo"]
            print(f"Rol {item['nombre']} actualizado")

    db.session.commit()

    rol_admin = Rol.query.filter_by(nombre="ADMIN").first()

    # ==============================================
    # 2. CREAR / RESTABLECER USUARIOS ADMINISTRADORES
    # ==============================================
    # Habilitamos tanto ADMINISTRADOR como admin con la clave admin123
    usuarios_admin = [
        {"username": "ADMINISTRADOR", "nombre": "Winie Laurissa Garcia Sandoval"},
        {"username": "admin", "nombre": "Administrador Principal"}
    ]

    for u in usuarios_admin:
        usr = Usuario.query.filter_by(username=u["username"]).first()
        if not usr:
            usr = Usuario(
                username=u["username"],
                rol_id=rol_admin.id,
                nombre_completo=u["nombre"],
                estado=True
            )
            usr.set_password("admin123")
            db.session.add(usr)
            print(f"Usuario {u['username']} creado (Password: admin123)")
        else:
            usr.rol_id = rol_admin.id
            usr.estado = True
            usr.set_password("admin123")
            print(f"Usuario {u['username']} actualizado y contrasena restablecida a: admin123")

    db.session.commit()

    # ==============================================
    # 3. CREAR CATEGORIA BASE (SI ESTA VACIA)
    # ==============================================
    if Categoria.query.count() == 0:
        cat_general = Categoria(
            codigo="CAT-001",
            nombre="GENERAL",
            descripcion="Categoria general de productos",
            estado=EstadoCategoria.ACTIVO
        )
        db.session.add(cat_general)
        db.session.commit()
        print("Categoria base 'GENERAL' creada")

    print("\n" + "="*50)
    print("BASE DE DATOS INICIALIZADA CON EXITO")
    print("Credenciales de acceso:")
    print("  - Usuario:    ADMINISTRADOR (o admin)")
    print("  - Contrasena: admin123")
    print("="*50 + "\n")
