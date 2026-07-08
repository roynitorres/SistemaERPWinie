from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from database import db
from models.usuario import Usuario
from models.rol import Rol
from models.cliente import Cliente
from utils.permisos import roles_required


usuarios_bp = Blueprint("usuarios", __name__)


@usuarios_bp.route("/usuarios", methods=["GET", "POST"])
@login_required
@roles_required("ADMIN")
def usuarios():
    roles = Rol.query.filter(Rol.estado == True, Rol.nombre != "CLIENTE").order_by(Rol.nombre.asc()).all()

    if request.method == "POST":
        usuario_id = request.form.get("usuario_id")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        rol_id = request.form.get("rol_id")
        cliente_id = None
        estado = True if request.form.get("estado") == "on" else False

        rol = Rol.query.get(rol_id)

        if not username:
            flash("Ingrese el nombre de usuario", "warning")
            return redirect(url_for("usuarios.usuarios"))

        if not rol:
            flash("Seleccione un rol válido", "warning")
            return redirect(url_for("usuarios.usuarios"))

        existe = Usuario.query.filter_by(username=username).first()

        if usuario_id:
            usuario = Usuario.query.get_or_404(usuario_id)

            if existe and existe.id != usuario.id:
                flash("Ya existe otro usuario con ese nombre", "warning")
                return redirect(url_for("usuarios.usuarios"))

            usuario.username = username
            usuario.rol_id = rol.id
            usuario.cliente_id = cliente_id
            usuario.estado = estado

            if password:
                usuario.set_password(password)

            flash("Usuario actualizado correctamente", "success")

        else:
            if existe:
                flash("Ya existe un usuario con ese nombre", "warning")
                return redirect(url_for("usuarios.usuarios"))

            if not password:
                flash("Ingrese una contraseña inicial", "warning")
                return redirect(url_for("usuarios.usuarios"))

            usuario = Usuario(
                username=username,
                rol_id=rol.id,
                cliente_id=cliente_id,
                estado=estado,
                debe_cambiar_password=(rol.nombre.upper() == "CLIENTE")
            )
            usuario.set_password(password)

            db.session.add(usuario)
            flash("Usuario creado correctamente", "success")

        db.session.commit()
        return redirect(url_for("usuarios.usuarios"))

    usuarios = Usuario.query.join(Rol).filter(Rol.nombre != "CLIENTE").order_by(Usuario.username.asc()).all()

    return render_template(
        "usuarios/usuarios.html",
        usuarios=usuarios,
        roles=roles
    )