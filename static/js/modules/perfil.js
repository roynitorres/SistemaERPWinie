/* ==========================================================================
   SISTEMA ERP WINIE — MÓDULO DE PERFIL (static/js/modules/perfil.js)
   Protección de campos solo lectura, avatar y cambio de credenciales
   ========================================================================== */

(function (window, document) {
    'use strict';

    window.ERP = window.ERP || {};

    window.ERP.Perfil = {
        modoEdicionActivo: false,

        /**
         * Alterna el modo solo lectura / edición para los datos personales
         */
        toggleEdicionPerfil: function (activar) {
            this.modoEdicionActivo = activar;

            var campos = document.querySelectorAll('.field-perfil');
            var alertEl = document.getElementById('alertModoedicion');
            var txtModo = document.getElementById('txtModoEdicion');
            var btnHabilitar = document.getElementById('btnHabilitarEdicion');
            var btnGuardar = document.getElementById('btnGuardarPerfil');

            campos.forEach(function (f) {
                f.disabled = !activar;
            });

            if (activar) {
                if (alertEl) {
                    alertEl.className = 'alert alert-warning d-flex align-items-center gap-2 mb-4';
                    alertEl.style.background = 'rgba(255,183,77,0.1)';
                    alertEl.style.borderColor = 'rgba(255,183,77,0.3)';
                    alertEl.style.color = '#ffb74d';
                }
                if (txtModo) txtModo.textContent = 'Modo Edición Activo. Puedes modificar tu información personal y presionar "Guardar Cambios".';
                if (btnHabilitar) btnHabilitar.style.display = 'none';
                if (btnGuardar) btnGuardar.style.display = 'inline-flex';
            } else {
                if (alertEl) {
                    alertEl.className = 'alert alert-info d-flex align-items-center gap-2 mb-4';
                    alertEl.style.background = 'rgba(0,176,255,0.08)';
                    alertEl.style.borderColor = 'rgba(0,176,255,0.2)';
                    alertEl.style.color = '#00b0ff';
                }
                if (txtModo) txtModo.textContent = 'Los campos están protegidos en modo solo lectura. Haz clic en "Habilitar Edición" para cambiarlos.';
                if (btnHabilitar) btnHabilitar.style.display = 'inline-flex';
                if (btnGuardar) btnGuardar.style.display = 'none';
            }
        },

        /**
         * Pestañas del Perfil (Información de Perfil vs Cambio de Contraseña)
         */
        initTabs: function () {
            var self = this;
            var btnPerfil = document.getElementById('btn-tab-perfil');
            var btnSeguridad = document.getElementById('btn-tab-seguridad');

            var panelPerfil = document.getElementById('panel-tab-perfil');
            var panelSeguridad = document.getElementById('panel-tab-seguridad');

            if (!btnPerfil || !btnSeguridad) return;

            btnPerfil.addEventListener('click', function () {
                btnPerfil.classList.add('active');
                btnSeguridad.classList.remove('active');
                if (panelPerfil) panelPerfil.classList.remove('d-none');
                if (panelSeguridad) panelSeguridad.classList.add('d-none');
            });

            btnSeguridad.addEventListener('click', function () {
                btnSeguridad.classList.add('active');
                btnPerfil.classList.remove('active');
                if (panelSeguridad) panelSeguridad.classList.remove('d-none');
                if (panelPerfil) panelPerfil.classList.add('d-none');
            });
        },

        /**
         * Previsualización y validación automática de Foto de Perfil
         */
        initFotoPerfil: function () {
            var inputFoto = document.getElementById('foto_perfil');
            if (!inputFoto) return;

            inputFoto.addEventListener('change', function () {
                if (!this.files || !this.files[0]) return;
                var file = this.files[0];
                var maxMB = 5;
                var allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];

                if (!allowedTypes.includes(file.type.toLowerCase())) {
                    alert('⚠️ Formato de archivo no válido.\nPor favor selecciona una imagen PNG, JPG, JPEG o WEBP.');
                    this.value = '';
                    return;
                }

                if (file.size > maxMB * 1024 * 1024) {
                    alert('⚠️ La imagen seleccionada pesa ' + (file.size / (1024 * 1024)).toFixed(2) + ' MB.\nEl límite máximo permitido es de ' + maxMB + ' MB.');
                    this.value = '';
                    return;
                }

                var reader = new FileReader();
                reader.onload = function (e) {
                    var container = document.getElementById('avatarContainer');
                    if (container) {
                        container.innerHTML = '<img src="' + e.target.result + '" id="imgPreview" alt="Foto de Perfil" style="width: 100%; height: 100%; object-fit: cover;">';
                    }
                };
                reader.readAsDataURL(file);

                var formFoto = document.getElementById('formFotoPerfil');
                if (formFoto) formFoto.submit();
            });
        },

        /**
         * Confirmación de guardado de perfil
         */
        initFormInfoPerfil: function () {
            var self = this;
            var btnHabilitar = document.getElementById('btnHabilitarEdicion');
            var btnConfirmarGuardado = document.getElementById('btnConfirmarGuardadoModal');

            if (btnHabilitar) {
                btnHabilitar.addEventListener('click', function () {
                    self.toggleEdicionPerfil(true);
                });
            }

            var formInfo = document.getElementById('formInfoPerfil');
            if (formInfo) {
                formInfo.addEventListener('submit', function (e) {
                    e.preventDefault();

                    var uInput = document.getElementById('inputUsername');
                    var eInput = document.getElementById('inputEmail');
                    var nInput = document.getElementById('inputNombreCompleto');
                    var tInput = document.getElementById('inputTelefono');
                    var gSelect = document.getElementById('inputGenero');
                    var dInput = document.getElementById('inputDireccion');

                    var errU = document.getElementById('err-username');
                    var errE = document.getElementById('err-email');
                    var errN = document.getElementById('err-nombre');
                    var errT = document.getElementById('err-telefono');
                    var errG = document.getElementById('err-genero');
                    var errD = document.getElementById('err-direccion');

                    var valido = true;

                    [uInput, eInput, nInput, tInput, gSelect, dInput].forEach(function (el) {
                        if (el) el.classList.remove('is-invalid-apex');
                    });
                    [errU, errE, errN, errT, errG, errD].forEach(function (el) {
                        if (el) el.style.display = 'none';
                    });

                    if (!uInput || !uInput.value.trim()) {
                        window.ERP.Validators.setError(uInput, errU);
                        valido = false;
                    }

                    var emailVal = eInput ? eInput.value.trim() : '';
                    if (!emailVal || !emailVal.includes('@') || !emailVal.includes('.')) {
                        window.ERP.Validators.setError(eInput, errE);
                        valido = false;
                    }

                    if (!nInput || !nInput.value.trim()) {
                        window.ERP.Validators.setError(nInput, errN);
                        valido = false;
                    }

                    if (!tInput || !tInput.value.trim()) {
                        window.ERP.Validators.setError(tInput, errT);
                        valido = false;
                    }

                    if (!gSelect || !gSelect.value.trim()) {
                        window.ERP.Validators.setError(gSelect, errG);
                        valido = false;
                    }

                    if (!dInput || !dInput.value.trim()) {
                        window.ERP.Validators.setError(dInput, errD);
                        valido = false;
                    }

                    if (!valido) return false;

                    var modalEl = document.getElementById('modalAdvertenciaPerfil');
                    if (modalEl && window.bootstrap) {
                        var modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                        modal.show();
                    }
                });
            }

            if (btnConfirmarGuardado) {
                btnConfirmarGuardado.addEventListener('click', function () {
                    if (formInfo) formInfo.submit();
                });
            }
        },

        /**
         * Validar Formulario de Cambio de Contraseña en Perfil
         */
        initFormCambioPass: function () {
            var formPass = document.getElementById('formCambiarPassword');
            if (!formPass) return;

            formPass.addEventListener('submit', function (e) {
                var pAct = document.getElementById('inputPassActual');
                var pNue = document.getElementById('inputPassNueva');
                var pCon = document.getElementById('inputPassConfirm');

                var errAct = document.getElementById('err-pass-actual');
                var errNue = document.getElementById('err-pass-nueva');
                var errCon = document.getElementById('err-pass-confirm');

                var valido = window.ERP.Validators.validatePasswordForm(pAct, pNue, pCon, errAct, errNue, errCon);

                if (!valido) {
                    e.preventDefault();
                    return false;
                }
                return true;
            });
        },

        init: function () {
            this.initTabs();
            this.initFotoPerfil();
            this.initFormInfoPerfil();
            this.initFormCambioPass();
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        window.ERP.Perfil.init();
    });

})(window, document);
