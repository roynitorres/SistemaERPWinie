from app import app

# Importamos base datos
from database import db

# Importamos modelos
from models.rol import Rol
from models.usuario import Usuario

with app.app_context():

        # ==============================================
    # CREAR / ACTUALIZAR ROLES BASE
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
    # CREAR USUARIO ADMIN
    # ==============================================

    # Buscar usuario admin
    usuario_admin = Usuario.query.filter_by(
        username="admin"
    ).first()

    # Si no existe lo creamos
    if not usuario_admin:
        usuario_admin = Usuario(
            username="admin",
            rol_id=rol_admin.id
        )

    
        usuario_admin.set_password("admin123")
        db.session.add(usuario_admin)
        db.session.commit()
        print("Usuario admin creado")
    else:
        print("Usuario admin ya existe")
    print("SEED COMPLETADO")