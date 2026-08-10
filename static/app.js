document.addEventListener('DOMContentLoaded', () => {
    cargarOrdenes();
    cargarRepuestos();
    cargarVentas();
    cargarCaja();
    cargarPlacas();
    cargarFirmwares();

    // FORMULARIO ÓRDENES
    const formOrden = document.getElementById('form-orden');
    if (formOrden) {
        formOrden.addEventListener('submit', async (e) => {
            e.preventDefault();
            const cliente = document.getElementById('ot-cliente').value;
            const telefono = document.getElementById('ot-telefono').value;
            const equipo = document.getElementById('ot-equipo').value;
            const falla = document.getElementById('ot-falla').value;
            const solucion = document.getElementById('ot-solucion').value;
            const presupuesto = document.getElementById('ot-presupuesto').value;
            const estado = document.getElementById('ot-estado').value;

            await fetch('/api/ordenes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cliente, telefono, equipo, falla, solucion, presupuesto, estado })
            });

            formOrden.reset();
            cargarOrdenes();
        });
    }

    // FORMULARIO REPUESTOS
    const formRepuesto = document.getElementById('form-repuesto');
    if (formRepuesto) {
        formRepuesto.addEventListener('submit', async (e) => {
            e.preventDefault();
            const categoria = document.getElementById('rep-categoria').value;
            const nombre = document.getElementById('rep-nombre').value;
            const ubicacion = document.getElementById('rep-ubicacion').value;
            const cantidad = document.getElementById('rep-cantidad').value;
            const precio = document.getElementById('rep-precio').value;

            await fetch('/api/repuestos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ categoria, nombre, ubicacion, cantidad, precio })
            });

            formRepuesto.reset();
            cargarRepuestos();
        });
    }

    // FORMULARIO VENTAS
    const formVenta = document.getElementById('form-venta');
    if (formVenta) {
        formVenta.addEventListener('submit', async (e) => {
            e.preventDefault();
            const producto = document.getElementById('vta-producto').value;
            const precio = document.getElementById('vta-precio').value;

            await fetch('/api/ventas', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ producto, precio })
            });

            formVenta.reset();
            cargarVentas();
        });
    }

    // FORMULARIO CAJA
    const formCaja = document.getElementById('form-caja');
    if (formCaja) {
        formCaja.addEventListener('submit', async (e) => {
            e.preventDefault();
            const tipo = document.getElementById('caja-tipo').value;
            const concepto = document.getElementById('caja-concepto').value;
            const monto = document.getElementById('caja-monto').value;

            await fetch('/api/caja', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tipo, concepto, monto })
            });

            formCaja.reset();
            cargarCaja();
        });
    }

    // FORMULARIO BUSCAR TEST POINTS / TENSIONES
    const formTestPoints = document.getElementById('form-test-points');
    if (formTestPoints) {
        formTestPoints.addEventListener('submit', async (e) => {
            e.preventDefault();
            const chasis = document.getElementById('tp-chasis').value;
            const resDiv = document.getElementById('resultado-test-points');
            resDiv.innerHTML = '<div class="spinner-border text-info" role="status"></div> Analizando chasis...';

            const res = await fetch('/api/obtener-test-points', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chasis })
            });
            const data = await res.json();
            if (data.test_points) {
                resDiv.innerHTML = `<pre class="bg-dark text-light p-3 rounded" style="white-space: pre-wrap;">${data.test_points}</pre>`;
            } else {
                resDiv.innerHTML = `<div class="alert alert-danger">${data.error || 'No se obtuvieron datos'}</div>`;
            }
        });
    }

    // FORMULARIO SUBIR DIAGRAMA PDF
    const formPdf = document.getElementById('form-pdf-esquematico');
    if (formPdf) {
        formPdf.addEventListener('submit', async (e) => {
            e.preventDefault();
            const chasis = document.getElementById('pdf-chasis').value;
            const fileInput = document.getElementById('pdf-file');
            const resDiv = document.getElementById('resultado-pdf');

            if (!fileInput.files.length) return;

            resDiv.innerHTML = '<div class="spinner-border text-info" role="status"></div> Procesando PDF esquemático...';

            const formData = new FormData();
            formData.append('chasis', chasis);
            formData.append('archivo', fileInput.files[0]);

            const res = await fetch('/api/analizar-esquematico-pdf', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.resultado) {
                resDiv.innerHTML = `<pre class="bg-dark text-light p-3 rounded" style="white-space: pre-wrap;">${data.resultado}</pre>`;
            } else {
                resDiv.innerHTML = `<div class="alert alert-danger">${data.error || 'Error al procesar PDF'}</div>`;
            }
        });
    }

    // CALCULAR CORRIENTE LED / BACKLIGHT
    const formBacklight = document.getElementById('form-backlight');
    if (formBacklight) {
        formBacklight.addEventListener('submit', async (e) => {
            e.preventDefault();
            const driver = document.getElementById('driver-ic').value;
            const resDiv = document.getElementById('resultado-backlight');

            const res = await fetch('/api/calcular-backlight', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ driver })
            });
            const data = await res.json();
            resDiv.innerHTML = `<div class="alert alert-info"><strong>Driver ${data.driver}:</strong> ${data.procedimiento}</div>`;
        });
    }
});

// FUNCIONES DE CARGA DE TABLAS
async function cargarOrdenes() {
    const res = await fetch('/api/ordenes');
    const ordenes = await res.json();
    const tbody = document.getElementById('tabla-ordenes');
    if (!tbody) return;
    tbody.innerHTML = '';
    ordenes.forEach(o => {
        tbody.innerHTML += `
            <tr>
                <td>OT-${o.id}</td>
                <td>${o.cliente || ''}</td>
                <td>${o.telefono || ''}</td>
                <td>${o.equipo || ''}</td>
                <td>${o.falla || ''}</td>
                <td>$${o.presupuesto || 0}</td>
                <td><span class="badge bg-${o.estado === 'Entregado' ? 'success' : 'warning'}">${o.estado || 'Ingresado'}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-danger" onclick="eliminarOrden(${o.id})">🗑️</button>
                </td>
            </tr>
        `;
    });
}

async function cargarRepuestos() {
    const res = await fetch('/api/repuestos');
    const repuestos = await res.json();
    const tbody = document.getElementById('tabla-repuestos');
    if (!tbody) return;
    tbody.innerHTML = '';
    repuestos.forEach(r => {
        tbody.innerHTML += `
            <tr>
                <td>${r.categoria || ''}</td>
                <td>${r.nombre || ''}</td>
                <td>${r.ubicacion || ''}</td>
                <td>
                    <button class="btn btn-sm btn-outline-secondary py-0" onclick="cambiarStock(${r.id}, ${r.cantidad - 1})">-</button>
                    ${r.cantidad}
                    <button class="btn btn-sm btn-outline-secondary py-0" onclick="cambiarStock(${r.id}, ${r.cantidad + 1})">+</button>
                </td>
                <td>$${r.precio || 0}</td>
            </tr>
        `;
    });
}

async function cargarVentas() {
    const res = await fetch('/api/ventas');
    const ventas = await res.json();
    const tbody = document.getElementById('tabla-ventas');
    if (!tbody) return;
    tbody.innerHTML = '';
    ventas.forEach(v => {
        tbody.innerHTML += `
            <tr>
                <td>VTA-${v.id}</td>
                <td>${v.producto || ''}</td>
                <td>$${v.precio || 0}</td>
                <td><span class="badge bg-info">${v.estado || 'En Venta'}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-danger" onclick="eliminarVenta(${v.id})">🗑️</button>
                </td>
            </tr>
        `;
    });
}

async function cargarCaja() {
    const res = await fetch('/api/caja');
    const data = await res.json();
    const tbody = document.getElementById('tabla-caja');
    if (!tbody) return;
    tbody.innerHTML = '';
    (data.movimientos || []).forEach(m => {
        tbody.innerHTML += `
            <tr>
                <td>${m.fecha || ''}</td>
                <td><span class="badge bg-${m.tipo === 'Ingreso' ? 'success' : 'danger'}">${m.tipo}</span></td>
                <td>${m.concepto || ''}</td>
                <td>$${m.monto || 0}</td>
                <td>
                    <button class="btn btn-sm btn-outline-danger" onclick="eliminarMovimiento(${m.id})">🗑️</button>
                </td>
            </tr>
        `;
    });

    const elIng = document.getElementById('caja-total-ingresos');
    const elEgr = document.getElementById('caja-total-egresos');
    const elBal = document.getElementById('caja-balance');

    if (elIng) elIng.innerText = `$${data.ingresos || 0}`;
    if (elEgr) elEgr.innerText = `$${data.egresos || 0}`;
    if (elBal) elBal.innerText = `$${data.balance || 0}`;
}

async function cargarPlacas() {
    const res = await fetch('/api/placas');
    const placas = await res.json();
    const tbody = document.getElementById('tabla-placas');
    if (!tbody) return;
    tbody.innerHTML = '';
    placas.forEach(p => {
        tbody.innerHTML += `
            <tr>
                <td>${p.tipo || ''}</td>
                <td>${p.codigo || ''}</td>
                <td>${p.modelo || ''}</td>
            </tr>
        `;
    });
}

async function cargarFirmwares() {
    const res = await fetch('/api/firmwares');
    const firmwares = await res.json();
    const tbody = document.getElementById('tabla-firmwares');
    if (!tbody) return;
    tbody.innerHTML = '';
    firmwares.forEach(f => {
        tbody.innerHTML += `
            <tr>
                <td>${f.chasis || ''}</td>
                <td>${f.modelo || ''}</td>
                <td>${f.memoria || ''}</td>
                <td><a href="${f.url_nube}" target="_blank" class="btn btn-sm btn-outline-info">Descargar</a></td>
            </tr>
        `;
    });
}

// OPERACIONES DE EDICION Y BORRADO
async function eliminarOrden(id) {
    if (confirm('¿Eliminar orden de trabajo?')) {
        await fetch(`/api/ordenes/${id}`, { method: 'DELETE' });
        cargarOrdenes();
    }
}

async function eliminarVenta(id) {
    if (confirm('¿Eliminar publicación de venta?')) {
        await fetch(`/api/ventas/${id}`, { method: 'DELETE' });
        cargarVentas();
    }
}

async function eliminarMovimiento(id) {
    if (confirm('¿Eliminar registro de caja?')) {
        await fetch(`/api/caja/${id}`, { method: 'DELETE' });
        cargarCaja();
    }
}

async function cambiarStock(id, nuevaCantidad) {
    if (nuevaCantidad < 0) return;
    await fetch(`/api/repuestos/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cantidad: nuevaCantidad })
    });
    cargarRepuestos();
}
