import os
import time
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from database import db
from models.usuario import Usuario

perfil_bp = Blueprint('perfil', __name__, url_prefix='/perfil')

@perfil_bp.route('/', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre_completo = request.form.get('nombre_completo')
        direccion = request.form.get('direccion')
        genero = request.form.get('genero')
        telefono = request.form.get('telefono')
        
        # Obtener archivo de foto de perfil
        foto = request.files.get('foto_perfil')
        
        if foto and foto.filename != '':
            # Validar y asegurar el nombre de archivo
            filename = secure_filename(foto.filename)
            # Agregar timestamp para evitar duplicados
            filename = f"{int(time.time())}_{filename}"
            
            # Asegurar que el directorio exista
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'perfiles')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Guardar la foto
            filepath = os.path.join(upload_dir, filename)
            foto.save(filepath)
            
            # Borrar foto anterior si existe
            if current_user.foto_perfil:
                old_filepath = os.path.join(upload_dir, current_user.foto_perfil)
                if os.path.exists(old_filepath):
                    try:
                        os.remove(old_filepath)
                    except Exception:
                        pass
                        
            # Actualizar el campo en BD
            current_user.foto_perfil = filename
        
        # Actualizar resto de campos
        current_user.nombre_completo = nombre_completo
        current_user.direccion = direccion
        current_user.genero = genero
        current_user.telefono = telefono
        
        # Cambio de contraseña opcional
        nueva_password = request.form.get('nueva_password')
        if nueva_password and len(nueva_password.strip()) >= 6:
            current_user.set_password(nueva_password)
            
        db.session.commit()
        flash('Perfil actualizado con éxito', 'success')
        return redirect(url_for('perfil.editar_perfil'))

    return render_template('perfil/perfil.html')
