import os
import time
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from database import db
from models.usuario import Usuario
from validators.common_validators import validar_email

perfil_bp = Blueprint('perfil', __name__, url_prefix='/perfil')

@perfil_bp.route('/', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    if request.method == 'POST':
        action = request.form.get('action')

        # ==========================================
        # ACCIÓN 1: ACTUALIZACIÓN INDEPENDIENTE DE FOTO
        # ==========================================
        if action == 'actualizar_foto':
            foto = request.files.get('foto_perfil')
            if not foto or foto.filename == '':
                flash('Por favor selecciona una imagen para subir.', 'warning')
                return redirect(url_for('perfil.editar_perfil', tab='perfil'))

            ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
            filename_raw = secure_filename(foto.filename)
            ext = filename_raw.rsplit('.', 1)[1].lower() if '.' in filename_raw else ''
            
            if ext not in ALLOWED_EXTENSIONS:
                flash('Formato de imagen no permitido. Usa imágenes PNG, JPG, JPEG o WEBP.', 'danger')
                return redirect(url_for('perfil.editar_perfil', tab='perfil'))

            # Verificar límite de 5 MB
            foto.seek(0, os.SEEK_END)
            file_length = foto.tell()
            foto.seek(0)
            if file_length > 5 * 1024 * 1024:
                flash('La imagen seleccionada supera el límite máximo de 5 MB.', 'danger')
                return redirect(url_for('perfil.editar_perfil', tab='perfil'))

            filename = f"{int(time.time())}_{filename_raw}"
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'perfiles')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            foto.save(filepath)

            if current_user.foto_perfil:
                old_filepath = os.path.join(upload_dir, current_user.foto_perfil)
                if os.path.exists(old_filepath):
                    try:
                        os.remove(old_filepath)
                    except Exception:
                        pass
            current_user.foto_perfil = filename
            db.session.commit()
            flash('Foto de perfil actualizada con éxito.', 'success')
            return redirect(url_for('perfil.editar_perfil', tab='perfil'))

        # ==========================================
        # ACCIÓN 2: CAMBIO DE CONTRASEÑA
        # ==========================================
        elif action == 'cambiar_password':
            password_actual    = request.form.get('password_actual', '').strip()
            nueva_password     = request.form.get('nueva_password', '').strip()
            confirmar_password = request.form.get('confirmar_password', '').strip()

            if not password_actual or not nueva_password or not confirmar_password:
                flash('Debes completar todos los campos para cambiar tu contraseña.', 'danger')
                return redirect(url_for('perfil.editar_perfil', tab='seguridad'))

            if not current_user.check_password(password_actual):
                flash('La contraseña actual ingresada es incorrecta.', 'danger')
                return redirect(url_for('perfil.editar_perfil', tab='seguridad'))

            if len(nueva_password) < 6:
                flash('La nueva contraseña debe tener al menos 6 caracteres.', 'danger')
                return redirect(url_for('perfil.editar_perfil', tab='seguridad'))

            if nueva_password != confirmar_password:
                flash('La confirmación de la nueva contraseña no coincide.', 'danger')
                return redirect(url_for('perfil.editar_perfil', tab='seguridad'))

            # Cifrar y actualizar nueva contraseña
            current_user.set_password(nueva_password)
            db.session.commit()
            flash('¡Contraseña actualizada con éxito!', 'success')
            return redirect(url_for('perfil.editar_perfil', tab='seguridad'))

        # ==========================================
        # ACCIÓN 3: ACTUALIZAR INFORMACIÓN DE PERFIL
        # ==========================================
        else:
            username        = request.form.get('username', '').strip()
            nombre_completo = request.form.get('nombre_completo', '').strip()
            email           = request.form.get('email', '').strip().lower()
            direccion       = request.form.get('direccion', '').strip()
            genero          = request.form.get('genero', '').strip()
            telefono        = request.form.get('telefono', '').strip()

            # Validar que todos los campos de perfil sean obligatorios
            if not username or not nombre_completo or not email or not telefono or not genero or not direccion:
                flash('Todos los campos del perfil (Nombre de Usuario, Nombre Completo, Correo, Teléfono, Género y Dirección) son obligatorios.', 'danger')
                return redirect(url_for('perfil.editar_perfil', tab='perfil'))

            # Validar formato con Validador Común (common_validators.py)
            es_valido, msg_err = validar_email(email)
            if not es_valido:
                flash(msg_err, 'danger')
                return redirect(url_for('perfil.editar_perfil', tab='perfil'))

            # Validar Unicidad de Nombre de Usuario
            if username and username != current_user.username:
                usuario_existente = Usuario.query.filter(Usuario.username == username, Usuario.id != current_user.id).first()
                if usuario_existente:
                    flash(f'El nombre de usuario "{username}" ya está registrado por otra cuenta.', 'danger')
                    return redirect(url_for('perfil.editar_perfil', tab='perfil'))
                current_user.username = username

            # Validar Unicidad de Correo Electrónico
            if email and email != (current_user.email or ''):
                email_existente = Usuario.query.filter(Usuario.email == email, Usuario.id != current_user.id).first()
                if email_existente:
                    flash(f'El correo electrónico "{email}" ya está registrado por otra cuenta.', 'danger')
                    return redirect(url_for('perfil.editar_perfil', tab='perfil'))
                current_user.email = email

            # Actualizar Datos Personales
            current_user.nombre_completo = nombre_completo
            current_user.email           = email
            current_user.direccion       = direccion
            current_user.genero          = genero if genero in ['Masculino', 'Femenino'] else None
            current_user.telefono        = telefono

            db.session.commit()
            flash('Información de perfil actualizada con éxito.', 'success')
            return redirect(url_for('perfil.editar_perfil', tab='perfil'))

    active_tab = request.args.get('tab', 'perfil')
    return render_template('perfil/perfil.html', active_tab=active_tab)
