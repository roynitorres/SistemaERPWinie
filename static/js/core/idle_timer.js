/**
 * ============================================================================
 * IDLE SESSION TIMEOUT - SEGURIDAD Y CONTROL DE INACTIVIDAD
 * ============================================================================
 * 
 * Monitorea la actividad del usuario en el navegador (ratón, teclado, scroll).
 * - Expiración total: 15 minutos (900s)
 * - Modal preventivo: a los 13 minutos (780s), dejando 2 minutos (120s) de cuenta atrás.
 * - Sincronización multi-pestaña en tiempo real vía localStorage.
 * - Ping periódico transparente al servidor para renovar la sesión activa.
 */

(function () {
    'use strict';

    // Constantes de tiempo (en segundos)
    const TIMEOUT_SECONDS = 900;       // 15 minutos totales
    const WARN_BEFORE_SECONDS = 120;   // 2 minutos de advertencia previa
    const WARN_AT_SECONDS = TIMEOUT_SECONDS - WARN_BEFORE_SECONDS; // 13 minutos (780s)
    const PING_INTERVAL_MS = 180 * 1000; // 3 minutos mínimo entre pings por actividad

    const STORAGE_KEY = 'winie_erp_last_activity';
    const PING_URL = '/ping-session';
    const LOGOUT_URL = '/logout?motivo=inactividad';

    // Elementos del DOM
    const modalEl = document.getElementById('modalInactividad');
    if (!modalEl) {
        // Si no existe el modal en la página (ej: página de login), no inicializar
        return;
    }

    const countdownDisplay = document.getElementById('idleCountdownDisplay');
    const countdownBox = document.getElementById('idleCountdownBox');
    const iconWrapper = document.getElementById('idleIconWrapper');
    const btnMantener = document.getElementById('btnMantenerSesion');

    let bsModal = null;
    let isModalVisible = false;
    let tickerInterval = null;
    let lastActivityTime = Date.now();
    let lastPingTime = Date.now();
    let throttleTimeout = null;

    // Inicializar Bootstrap Modal
    function obtenerModal() {
        if (!bsModal && window.bootstrap && window.bootstrap.Modal) {
            bsModal = window.bootstrap.Modal.getOrCreateInstance(modalEl, {
                backdrop: 'static',
                keyboard: false
            });
        }
        return bsModal;
    }

    // Formatear segundos a formato MM:SS
    function formatearTiempo(segundos) {
        const mins = Math.floor(segundos / 60);
        const secs = segundos % 60;
        const mm = mins < 10 ? '0' + mins : mins;
        const ss = secs < 10 ? '0' + secs : secs;
        return `${mm}:${ss}`;
    }

    // Renovar marca de tiempo de actividad local y sincronizar con otras pestañas
    function registrarActividad(forzarPing = false) {
        const ahora = Date.now();
        lastActivityTime = ahora;

        try {
            localStorage.setItem(STORAGE_KEY, ahora.toString());
        } catch (e) {
            // Manejo silencioso en caso de modo incógnito restrictivo
        }

        // Si el modal de advertencia estaba abierto y el usuario interactúa expresamente, cerrarlo
        if (isModalVisible && forzarPing) {
            ocultarModalAdvertencia();
        }

        // Si ha pasado suficiente tiempo desde el último ping, notificar al servidor
        if (forzarPing || (ahora - lastPingTime > PING_INTERVAL_MS)) {
            enviarPingServidor();
        }
    }

    // Ping asíncrono al servidor Flask para mantener la cookie y el backend actualizados
    function enviarPingServidor() {
        lastPingTime = Date.now();

        fetch(PING_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (response.status === 401) {
                // Si el backend ya caducó la sesión, redirigir
                window.location.href = LOGOUT_URL;
            }
            return response.json();
        })
        .then(data => {
            // Sesión renovada con éxito en el servidor
        })
        .catch(err => {
            console.warn('[IdleTimer] Error de conexión al sincronizar sesión:', err);
        });
    }

    // Mostrar modal con cuenta atrás
    function mostrarModalAdvertencia() {
        const modal = obtenerModal();
        if (modal && !isModalVisible) {
            isModalVisible = true;
            modal.show();
        }
    }

    // Ocultar modal y restaurar estilos estándar
    function ocultarModalAdvertencia() {
        const modal = obtenerModal();
        if (modal && isModalVisible) {
            isModalVisible = false;
            modal.hide();
        }
        if (countdownBox) countdownBox.classList.remove('is-urgent');
        if (iconWrapper) iconWrapper.classList.remove('is-urgent');
    }

    // Ciclo de evaluación de inactividad ejecutado cada 1 segundo
    function evaluarInactividad() {
        // Verificar si otra pestaña registró actividad más reciente
        try {
            const almacenada = localStorage.getItem(STORAGE_KEY);
            if (almacenada) {
                const ts = parseInt(almacenada, 10);
                if (ts > lastActivityTime) {
                    lastActivityTime = ts;
                }
            }
        } catch (e) {}

        const ahora = Date.now();
        const segundosInactivo = Math.floor((ahora - lastActivityTime) / 1000);

        if (segundosInactivo >= TIMEOUT_SECONDS) {
            // TIEMPO CUMPLIDO: Redirigir al logout
            if (tickerInterval) clearInterval(tickerInterval);
            window.location.href = LOGOUT_URL;
            return;
        }

        if (segundosInactivo >= WARN_AT_SECONDS) {
            // EN ZONA DE ADVERTENCIA: Mostrar modal y actualizar cuenta regresiva
            mostrarModalAdvertencia();

            const segundosRestantes = Math.max(0, TIMEOUT_SECONDS - segundosInactivo);
            if (countdownDisplay) {
                countdownDisplay.textContent = formatearTiempo(segundosRestantes);
            }

            // Aplicar estilo de urgencia si quedan 30 segundos o menos
            if (segundosRestantes <= 30) {
                if (countdownBox) countdownBox.classList.add('is-urgent');
                if (iconWrapper) iconWrapper.classList.add('is-urgent');
            } else {
                if (countdownBox) countdownBox.classList.remove('is-urgent');
                if (iconWrapper) iconWrapper.classList.remove('is-urgent');
            }
        } else {
            // Usuario activo o reactivado en otra pestaña
            if (isModalVisible) {
                ocultarModalAdvertencia();
            }
        }
    }

    // Escuchador de actividad con Throttling (máximo una llamada cada 3 segundos)
    function onUserInteraction() {
        if (isModalVisible) {
            // Cuando el modal de advertencia está abierto, no reseteamos con cualquier movimiento involuntario
            // del ratón; el usuario debe presionar "Seguir conectado"
            return;
        }

        if (!throttleTimeout) {
            registrarActividad(false);
            throttleTimeout = setTimeout(() => {
                throttleTimeout = null;
            }, 3000);
        }
    }

    // Registrar eventos globales de interacción humana
    const eventosInteraccion = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll'];
    eventosInteraccion.forEach(evento => {
        window.addEventListener(evento, onUserInteraction, { passive: true });
    });

    // Escuchar cambios en localStorage para sincronizar con otras pestañas
    window.addEventListener('storage', function (e) {
        if (e.key === STORAGE_KEY && e.newValue) {
            const ts = parseInt(e.newValue, 10);
            if (ts > lastActivityTime) {
                lastActivityTime = ts;
                if (isModalVisible) {
                    ocultarModalAdvertencia();
                }
            }
        }
    });

    // Botón "Seguir conectado"
    if (btnMantener) {
        btnMantener.addEventListener('click', function () {
            btnMantener.disabled = true;
            btnMantener.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Renovando...';

            enviarPingServidor();
            registrarActividad(true);

            setTimeout(() => {
                btnMantener.disabled = false;
                btnMantener.innerHTML = '<i class="bi bi-arrow-repeat me-1"></i> Seguir conectado';
                ocultarModalAdvertencia();
            }, 400);
        });
    }

    // Inicializar timestamp y arrancar ticker de 1 segundo
    registrarActividad(false);
    tickerInterval = setInterval(evaluarInactividad, 1000);

})();
