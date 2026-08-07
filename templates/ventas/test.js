
    // Logica de Pestañas
    function cambiarTab(tabName) {
        document.getElementById('tabCliente').classList.remove('active');
        document.getElementById('tabDetalle').classList.remove('active');
        document.getElementById('btnTabCliente').classList.remove('active');
        document.getElementById('btnTabDetalle').classList.remove('active');
        
        if (tabName === 'cliente') {
            document.getElementById('tabCliente').classList.add('active');
            document.getElementById('btnTabCliente').classList.add('active');
        } else {
            document.getElementById('tabDetalle').classList.add('active');
            document.getElementById('btnTabDetalle').classList.add('active');
        }
    }

    function abrirModal(id) {
        document.getElementById(id).classList.add("is-open");
    }

    function cerrarModal(id) {
        document.getElementById(id).classList.remove("is-open");
    }

    function mostrarMensaje(tipo, mensaje) {
        const container = document.querySelector(".flash-container") || document.body;
        const div = document.createElement("div");

        div.className = `flash-message flash-${tipo}`;
        div.innerText = mensaje;

        container.appendChild(div);

        setTimeout(() => {
            div.remove();
        }, 5000);
    }

    let detalleVenta = [];
    let productoSeleccionado = null;

    const empresaInfo = {
        razon_social: "{{ empresa.razon_social if empresa else '' }}",
        ruc: "{{ empresa.ruc if empresa else '' }}",
        direccion: "{{ empresa.direccion if empresa else '' }}",
        ciudad: "{{ empresa.ciudad if empresa else '' }}",
        telefono: "{{ empresa.telefono if empresa else '' }}",
        email: "{{ empresa.email if empresa else '' }}",
        sitio_web: "{{ empresa.sitio_web if empresa else '' }}",
        serie_factura: "{{ empresa.serie_factura if empresa else 'F001' }}",
        correlativo: "{{ empresa.correlativo if empresa else '00034' }}",
        iva: Number("{{ empresa.iva if empresa else 15 }}")
    };
    const IVA_RATE = empresaInfo.iva / 100;
    const DESCUENTO_MAXIMO_USUARIO = Number("{{ descuento_maximo }}");

    const tbody = document.getElementById("detalleVentaBody");
    const tbodyBusqueda = document.getElementById("tbodyBusquedaProductos");
    const buscarProducto = document.getElementById("buscarProducto");

    const btnLimpiarVenta = document.getElementById("btnLimpiarVenta");
    const btnGuardar = document.getElementById("btnGuardar");
    const btnConfirmarGuardar = document.getElementById("btnConfirmarGuardar");

    const tipoVentaSelect = document.getElementById("tipo_venta");
    const fechaLimite = document.getElementById("fecha_limite");

    // Lógica para el Combobox del Cliente (Datalist)
    const inputClienteNombre = document.getElementById("cliente_nombre");
    const inputClienteId = document.getElementById("cliente_id");
    const datalistClientes = document.getElementById("clientesList");
    let clienteSeleccionado = { nombre: "", direccion: "-", telefono: "-" };

    function checkClienteSelection() {
        const val = inputClienteNombre.value.trim();
        const options = Array.from(datalistClientes.options);
        
        // Buscar coincidencia exacta (ignorando espacios extra y mayúsculas/minúsculas)
        const selectedOption = options.find(opt => opt.value.trim().toLowerCase() === val.toLowerCase());

        if (selectedOption) {
            inputClienteId.value = selectedOption.dataset.id;
            clienteSeleccionado = {
                nombre: selectedOption.value,
                direccion: "-",
                telefono: selectedOption.dataset.telefono || "-"
            };
        } else {
            inputClienteId.value = "";
            clienteSeleccionado = { nombre: val, direccion: "-", telefono: "-" };
        }
    }

    inputClienteNombre.addEventListener("input", checkClienteSelection);
    inputClienteNombre.addEventListener("change", checkClienteSelection);

    function actualizarFechaLimite() {
        if (tipoVentaSelect.value === "CREDITO") {
            fechaLimite.disabled = false;
        } else {
            fechaLimite.disabled = true;
            fechaLimite.value = "";
        }
    }

    tipoVentaSelect.addEventListener("change", actualizarFechaLimite);
    actualizarFechaLimite();

    // Nueva función para actualizar el resumen visual del header
    // Removed actualizarResumen since we no longer have a summary panel on tab 2

    buscarProducto.addEventListener("input", async function () {
        const texto = this.value.trim();

        if (texto.length < 1) {
            tbodyBusqueda.innerHTML = "";
            return;
        }

        await buscarProductos(texto);
    });

    const btnAgregarDetalle = document.getElementById("btnAgregarDetalle");
    async function buscarProductos(textoBusqueda) {
        tbodyBusqueda.innerHTML = `
            <tr class="data-table__row">
                <td colspan="4" class="data-table__cell data-table__cell--center">
                </td>
            </tr>
        `;

        try {
            const respuesta = await fetch(`/buscar-productos?busqueda=${encodeURIComponent(textoBusqueda)}`);
            const productos = await respuesta.json();

            tbodyBusqueda.innerHTML = "";

            if (productos.length === 0) {
                tbodyBusqueda.innerHTML = `
                    <tr class="data-table__row">
                        <td colspan="4" class="data-table__cell data-table__cell--center" style="color: var(--color-danger);">
                            No se encontraron productos
                        </td>
                    </tr>
                `;
                return;
            }

            productos.forEach(producto => {
                // Escapar comillas en JSON
                const prodJson = JSON.stringify(producto).replace(/'/g, "&#39;").replace(/"/g, "&quot;");
                tbodyBusqueda.innerHTML += `
                    <tr class="data-table__row">
                        <td class="data-table__cell data-table__cell--center">
                            <input type="checkbox" class="producto-checkbox" value="${prodJson}">
                        </td>
                        <td class="data-table__cell">${producto.codigo}</td>
                        <td class="data-table__cell">${producto.nombre}</td>
                        <td class="data-table__cell">${producto.marca || '-'}</td>
                        <td class="data-table__cell data-table__cell--right">C$ ${producto.precio.toFixed(2)}</td>
                        <td class="data-table__cell data-table__cell--center">${producto.stock}</td>
                    </tr>
                `;
            });

        } catch (error) {
            console.error(error);

            tbodyBusqueda.innerHTML = `
                <tr class="data-table__row">
                    <td colspan="4" class="data-table__cell data-table__cell--center" style="color: var(--color-danger);">
                        Error al buscar productos
                    </td>
                </tr>
            `;
        }
    }

    function toggleAllProducts(checkbox) {
        const checkboxes = document.querySelectorAll('.producto-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = checkbox.checked;
        });
    }

    document.getElementById("btnAgregarDetalleMultiple").addEventListener("click", function () {
        const checkboxes = document.querySelectorAll('.producto-checkbox:checked');
        
        if (checkboxes.length === 0) {
            mostrarMensaje("warning", "Seleccione al menos un producto");
            return;
        }

        let agregados = 0;
        let erroresStock = 0;
        let repetidos = 0;

        checkboxes.forEach(cb => {
            const producto = JSON.parse(cb.value);

            if (producto.stock <= 0) {
                erroresStock++;
                return;
            }

            const existe = detalleVenta.find(p => p.producto_id === producto.id);
            if (existe) {
                repetidos++;
                return;
            }

            detalleVenta.push({
                producto_id: producto.id,
                codigo: producto.codigo,
                nombre: producto.nombre,
                precio: producto.precio,
                descuento_monto: 0,
                cantidad: 1,
                stock: producto.stock,
                subtotal: producto.precio
            });
            agregados++;
        });

        if (agregados > 0) {
            renderizarTabla();
            mostrarMensaje("success", `${agregados} producto(s) agregado(s) correctamente`);
        }
        
        if (erroresStock > 0 || repetidos > 0) {
            let msg = [];
            if (erroresStock > 0) msg.push(`${erroresStock} sin stock`);
            if (repetidos > 0) msg.push(`${repetidos} ya estaban en la lista`);
            mostrarMensaje("warning", "No se agregaron: " + msg.join(", "));
        }

        cerrarModal("modalProductos");
        limpiarModalProducto();
    });

    document.getElementById("btnLimpiarModal").addEventListener("click", limpiarModalProducto);

    function limpiarModalProducto() {
        document.getElementById("buscarProducto").value = "";
        document.getElementById("tbodyBusquedaProductos").innerHTML = "";
        const checkAll = document.getElementById("selectAllProducts");
        if (checkAll) checkAll.checked = false;
    }

    function renderizarTabla() {
        tbody.innerHTML = "";

        let subtotalGeneral = 0;

        if (detalleVenta.length === 0) {
            tbody.innerHTML = `
                <tr class="data-table__row">
                    <td colspan="7" class="data-table__cell data-table__cell--center" style="padding: var(--spacing-xl); color: var(--color-text-muted);">
                        <i class="bi bi-box-seam d-block mb-2" style="font-size: 2rem;"></i>
                        Sin productos agregados
                    </td>
                </tr>
            `;

            actualizarTotales(0);
            return;
        }

        detalleVenta.forEach((producto, index) => {
            subtotalGeneral += producto.subtotal;

            tbody.innerHTML += `
                <tr class="data-table__row">
                    <td class="data-table__cell">${producto.codigo}</td>
                    <td class="data-table__cell">${producto.nombre}</td>
                    <td class="data-table__cell data-table__cell--center">
                        <div class="cantidad-control">
                            <button type="button" onclick="disminuirCantidad(${index})">-</button>
                            <span>${producto.cantidad}</span>
                            <button type="button" onclick="aumentarCantidad(${index})">+</button>
                        </div>
                    </td>
                    <td class="data-table__cell data-table__cell--right">C$ ${producto.precio.toFixed(2)}</td>
                    <td class="data-table__cell data-table__cell--center">
                        <input type="number" class="form-input text-end" style="width: 80px;" 
                        value="${producto.descuento_monto}" min="0" 
                        onchange="actualizarLinea(${index}, 'descuento_monto', this.value)">
                    </td>
                    <td class="data-table__cell data-table__cell--right" style="font-weight: var(--font-weight-bold);">C$ ${producto.subtotal.toFixed(2)}</td>
                    <td class="data-table__cell data-table__cell--actions">
                        <button type="button" class="btn btn--outline btn--small" onclick="eliminarProducto(${index})" style="color: var(--color-danger); border-color: var(--color-danger);">
                            <i class="bi bi-x-lg"></i>
                        </button>
                    </td>
                </tr>
            `;
        });

        actualizarTotales(subtotalGeneral);
    }

    function actualizarTotales(subtotal) {
        const iva = subtotal * IVA_RATE;
        const total = subtotal + iva;

        document.getElementById("subtotalVenta").textContent = "C$ " + subtotal.toFixed(2);
        document.getElementById("ivaVenta").textContent = "C$ " + iva.toFixed(2);
        document.getElementById("totalVenta").textContent = "C$ " + total.toFixed(2);
    }

    function actualizarLinea(index, campo, valor) {
        const p = detalleVenta[index];
        const val = parseFloat(valor) || 0;
        
        if (campo === 'descuento_monto') {
            const bruto = p.cantidad * p.precio;
            const descuentoMonto = Math.min(val, bruto); 
            p.descuento_monto = descuentoMonto;
            p.subtotal = bruto - descuentoMonto;
        }
        renderizarTabla();
    }

    function recalcularItem(producto) {
        const bruto = producto.cantidad * producto.precio;
        const descuentoMonto = parseFloat(producto.descuento_monto) || 0;
        producto.subtotal = Math.max(bruto - descuentoMonto, 0);
    }

    function eliminarProducto(index) {
        detalleVenta.splice(index, 1);
        renderizarTabla();
    }

    function aumentarCantidad(index) {
        const producto = detalleVenta[index];

        if (producto.cantidad >= producto.stock) {
            mostrarMensaje("danger", "No hay stock disponible");
            return;
        }

        producto.cantidad++;
        recalcularItem(producto);
        renderizarTabla();
    }

    function disminuirCantidad(index) {
        const producto = detalleVenta[index];

        if (producto.cantidad <= 1) {
            return;
        }

        producto.cantidad--;
        recalcularItem(producto);
        renderizarTabla();
    }

    btnLimpiarVenta.addEventListener("click", function () {
        detalleVenta = [];
        document.getElementById("formVenta").reset();
        actualizarFechaLimite();
        renderizarTabla();
    });

    btnGuardar.addEventListener("click", function () {
        const clienteId = document.getElementById("cliente_id").value;
        const tipoVenta = document.getElementById("tipo_venta").value;
        const fechaVenta = document.getElementById("fecha_venta").value;
        const fechaLimiteCredito = document.getElementById("fecha_limite").value;
        
        if (!clienteId) {
            cambiarTab('cliente');
            mostrarMensaje("warning", "Seleccione un cliente para la venta");
            return;
        }

        if (!fechaVenta) {
            cambiarTab('cliente');
            mostrarMensaje("warning", "Seleccione la fecha de venta");
            return;
        }

        if (tipoVenta === "CREDITO" && !fechaLimiteCredito) {
            cambiarTab('cliente');
            mostrarMensaje("warning", "Seleccione la fecha límite del crédito");
            return;
        }

        if (detalleVenta.length === 0) {
            mostrarMensaje("warning", "Debe agregar productos a la venta");
            return;
        }

        // Poblar datos del modal
        const clienteNombre = document.getElementById("cliente_nombre").value;
        const numFactura = document.getElementById("numero_factura").value;
        const total = document.getElementById("totalVenta").textContent;

        document.getElementById("confirmCliente").textContent = clienteNombre;
        document.getElementById("confirmTipoVenta").textContent = tipoVenta;
        document.getElementById("confirmNumFactura").textContent = numFactura;
        document.getElementById("confirmTotal").textContent = total;

        abrirModal("modalConfirmarVenta");
    });

    btnConfirmarGuardar.addEventListener("click", guardarVentaFinal);

    async function guardarVentaFinal() {
        const clienteId = document.getElementById("cliente_id").value;
        const tipoVenta = document.getElementById("tipo_venta").value;
        const fechaVenta = document.getElementById("fecha_venta").value;
        const fechaLimiteCredito = document.getElementById("fecha_limite").value;
        const observaciones = document.getElementById("observaciones").value;

        // Las validaciones ahora ocurren al presionar el botón "Guardar" principal antes del modal

        btnConfirmarGuardar.disabled = true;
        btnConfirmarGuardar.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Procesando...`;

        const datos = {
            cliente_id: clienteId,
            tipo_venta: tipoVenta,
            fecha_venta: fechaVenta,
            fecha_limite_credito: fechaLimiteCredito,
            observaciones: observaciones,
            productos: detalleVenta
        };

        try {
            const respuesta = await fetch("/guardar-venta", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(datos)
            });

            const resultado = await respuesta.json();

            if (!resultado.success) {
                mostrarMensaje("danger", resultado.message);
                btnConfirmarGuardar.disabled = false;
                btnConfirmarGuardar.innerHTML = `<i class="bi bi-check-lg"></i> Confirmar y Guardar`;
                return;
            }

            window.open(`/factura/${resultado.venta_id}`, "_blank");
            location.reload();

        } catch (error) {
            console.error(error);
            mostrarMensaje("danger", "Error al emitir el comprobante");

            btnConfirmarGuardar.disabled = false;
            btnConfirmarGuardar.innerHTML = `<i class="bi bi-check-lg"></i> Confirmar y Guardar`;
        }
    }

    renderizarTabla();
