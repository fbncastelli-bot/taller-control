let otSeleccionadaId = null;
let repSeleccionadoId = null;
let ventaSeleccionadaId = null;
let movSeleccionadoId = null;

document.addEventListener("DOMContentLoaded", () => {
    cargarOrdenes();
    cargarRepuestos();
    cargarVentas();
    cargarFirmwares();
    cargarCaja();
});

function mostrarSeccion(sec) {
    const secciones = ['ordenes', 'placas', 'repuestos', 'ventas', 'caja', 'firmwares'];
    secciones.forEach(s => {
        const el = document.getElementById(`sec-${s}`);
        if (el) el.style.display = (s === sec) ? 'block' : 'none';
    });

    const links = document.querySelectorAll('.nav-link');
    links.forEach(link => link.classList.remove('active'));
    if (window.event && window.event.currentTarget) {
        window.event.currentTarget.classList.add('active');
    }
}

// 1. ÓRDENES DE TRABAJO
function cargarOrdenes() {
    fetch('/api/ordenes').then(r => r.json()).then(data => {
        let html = '';
        data.forEach(o => {
            html += `<tr onclick="seleccionarOT(${o.id}, '${o.equipo}', '${o.falla}', this)">
                <td>${o.id}</td>
                <td>${o.cliente}</td>
                <td>${o.equipo}</td>
                <td>${o.falla}</td>
                <td><span class="badge bg-info">${o.estado}</span></td>
                <td>$${o.presupuesto}</td>
            </tr>`;
        });
        document.getElementById('tabla-ordenes').innerHTML = html;
    });
}

function seleccionarOT(id, equipo, falla, fila) {
    otSeleccionadaId = id;
    document.querySelectorAll('#tabla-ordenes tr').forEach(r => r.classList.remove('table-active'));
    fila.classList.add('table-active');
    analizarFalla(equipo, falla);
}

function guardarOrden() {
    const cliente = document.getElementById('ot-cliente').value;
    const equipo = document.getElementById('ot-equipo').value;
    const falla = document.getElementById('ot-falla').value;
    const presupuesto = document.getElementById('ot-presupuesto').value;
    const estado = document.getElementById('ot-estado').value;

    fetch('/api/ordenes', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({cliente, equipo, falla, presupuesto, estado})
    }).then(() => {
        document.getElementById('ot-cliente').value = '';
        document.getElementById('ot-equipo').value = '';
        document.getElementById('ot-falla').value = '';
        document.getElementById('ot-presupuesto').value = '';
        cargarOrdenes();
    });
}

function eliminarOrdenSeleccionada() {
    if (!otSeleccionadaId) return alert("Seleccioná una orden de la lista.");
    if (confirm(`¿Eliminar la orden N° ${otSeleccionadaId}?`)) {
        fetch(`/api/ordenes/${otSeleccionadaId}`, { method: 'DELETE' }).then(() => {
            otSeleccionadaId = null;
            cargarOrdenes();
        });
    }
}

function filtrarTablaOT() {
    const q = document.getElementById('buscar-ot').value.toLowerCase();
    const filas = document.querySelectorAll('#tabla-ordenes tr');
    filas.forEach(f => {
        f.style.display = f.innerText.toLowerCase().includes(q) ? '' : 'none';
    });
}

function verFichaOT() {
    if (!otSeleccionadaId) return alert("Seleccioná una orden primero.");
    alert(`Generando Ficha e Informe Técnico para Orden N° ${otSeleccionadaId}...`);
}

function imprimirComprobante() {
    if (!otSeleccionadaId) return alert("Seleccioná una orden primero.");
    window.print();
}

function imprimirTicketTV() {
    if (!otSeleccionadaId) return alert("Seleccioná una orden primero.");
    alert(`Imprimiendo Etiqueta Adhesiva para Tapa de TV (Orden #${otSeleccionadaId})...`);
}

function analizarFalla(equipo, falla) {
    document.getElementById('box-diagnostico').innerHTML = `⏳ Analizando circuito y falla para ${equipo}...`;
    fetch('/api/analizar-falla', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({equipo, falla})
    }).then(r => r.json()).then(data => {
        document.getElementById('box-diagnostico').innerHTML = `<pre>${data.diagnostico || data.error}</pre>`;
    });
}

// 2. STOCK COMPONENTES
function cargarRepuestos() {
    fetch('/api/repuestos').then(r => r.json()).then(data => {
        let html = '';
        data.forEach(r => {
            html += `<tr onclick="seleccionarRepuesto(${r.id}, ${r.cantidad}, '${r.ubicacion}', '${r.nombre}', this)">
                <td>${r.id}</td>
                <td>${r.categoria}</td>
                <td>${r.nombre}</td>
                <td>${r.ubicacion}</td>
                <td><strong>${r.cantidad}</strong></td>
            </tr>`;
        });
        document.getElementById('tabla-repuestos').innerHTML = html;
    });
}

function seleccionarRepuesto(id, cant, ub, nombre, fila) {
    repSeleccionadoId = id;
    window.repCantActual = cant;
    window.repUbActual = ub;
    window.repNombreActual = nombre;
    document.querySelectorAll('#tabla-repuestos tr').forEach(r => r.classList.remove('table-active'));
    fila.classList.add('table-active');
}

function guardarRepuesto() {
    const categoria = document.getElementById('rep-cat').value;
    const nombre = document.getElementById('rep-nombre').value;
    const ubicacion = document.getElementById('rep-ubicacion').value;
    const cantidad = document.getElementById('rep-cant').value;

    fetch('/api/repuestos', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({categoria, nombre, ubicacion, cantidad})
    }).then(() => {
        document.getElementById('rep-nombre').value = '';
        document.getElementById('rep-ubicacion').value = '';
        cargarRepuestos();
    });
}

function modificarStock(delta) {
    if (!repSeleccionadoId) return alert("Seleccioná un componente.");
    const nuevaCant = Math.max(0, window.repCantActual + delta);
    fetch(`/api/repuestos/${repSeleccionadoId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({cantidad: nuevaCant})
    }).then(() => cargarRepuestos());
}

function cambiarCantidadModal() {
    if (!repSeleccionadoId) return alert("Seleccioná un componente.");
    const c = prompt("Nueva cantidad:", window.repCantActual);
    if (c !== null) {
        fetch(`/api/repuestos/${repSeleccionadoId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({cantidad: parseInt(c)})
        }).then(() => cargarRepuestos());
    }
}

function cambiarUbicacionModal() {
    if (!repSeleccionadoId) return alert("Seleccioná un componente.");
    const u = prompt("Nueva ubicación/gaveta:", window.repUbActual);
    if (u) {
        fetch(`/api/repuestos/${repSeleccionadoId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ubicacion: u})
        }).then(() => cargarRepuestos());
    }
}

function buscarDatasheet() {
    if (!window.repNombreActual) return alert("Seleccioná un componente.");
    window.open(`https://www.google.com/search?q=${window.repNombreActual}+datasheet+pdf`, '_blank');
}

function imprimirEtiqueta() {
    if (!repSeleccionadoId) return alert("Seleccioná un componente.");
    alert(`Imprimiendo etiqueta para gaveta: ${window.repNombreActual} (Ubicación: ${window.repUbActual})`);
}

function filtrarComp() {
    const q = document.getElementById('buscar-comp').value.toLowerCase();
    document.querySelectorAll('#tabla-repuestos tr').forEach(f => {
        f.style.display = f.innerText.toLowerCase().includes(q) ? '' : 'none';
    });
}

// 3. VENTAS Y USADOS
function cargarVentas() {
    fetch('/api/ventas').then(r => r.json()).then(data => {
        let html = '';
        data.forEach(v => {
            html += `<tr onclick="seleccionarVenta(${v.id}, this)">
                <td>${v.id}</td>
                <td>${v.producto}</td>
                <td>$${v.precio.toLocaleString()}</td>
                <td><span class="badge bg-success">${v.estado}</span></td>
            </tr>`;
        });
        document.getElementById('tabla-ventas').innerHTML = html;
    });
}

function seleccionarVenta(id, fila) {
    ventaSeleccionadaId = id;
    document.querySelectorAll('#tabla-ventas tr').forEach(r => r.classList.remove('table-active'));
    fila.classList.add('table-active');
}

function guardarVenta() {
    const producto = document.getElementById('v-producto').value;
    const precio = document.getElementById('v-precio').value;
    const estado = document.getElementById('v-estado').value;

    fetch('/api/ventas', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({producto, precio, estado})
    }).then(() => {
        document.getElementById('v-producto').value = '';
        document.getElementById('v-precio').value = '';
        cargarVentas();
    });
}

function eliminarVentaSeleccionada() {
    if (!ventaSeleccionadaId) return alert("Seleccioná un registro.");
    fetch(`/api/ventas/${ventaSeleccionadaId}`, { method: 'DELETE' }).then(() => {
        ventaSeleccionadaId = null;
        cargarVentas();
    });
}

function consultarML() {
    const prod = document.getElementById('v-producto').value;
    if (!prod) return alert("Ingresá el nombre del producto o chasis.");
    window.open(`https://listado.mercadolibre.com.ar/${prod}`, '_blank');
}

// 4. BANCO DE PLACAS Y ESQUEMÁTICOS
function buscarTestPoints() {
    const chasis = document.getElementById('input-chasis-tp').value;
    if(!chasis) return;
    document.getElementById('box-test-points').innerText = "⏳ Consultando puntos de prueba...";
    fetch('/api/obtener-test-points', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({chasis})
    }).then(r => r.json()).then(data => {
        document.getElementById('box-test-points').innerText = data.test_points || data.error;
    });
}

function procesarEsquematicoPDF() {
    const chasis = document.getElementById('pdf-chasis-nombre').value;
    const fileInput = document.getElementById('pdf-archivo');
    if (!chasis || fileInput.files.length === 0) return alert("Ingresá el código del chasis y seleccioná un archivo PDF.");

    const formData = new FormData();
    formData.append('chasis', chasis);
    formData.append('archivo', fileInput.files[0]);

    document.getElementById('box-test-points').innerText = "⏳ Subiendo archivo PDF y procesando plano con IA...";

    fetch('/api/analizar-esquematico-pdf', { method: 'POST', body: formData })
    .then(r => r.json()).then(data => {
        document.getElementById('box-test-points').innerText = data.resultado || data.error;
    });
}

function preguntarSobreEsquema() {
    const chasis = document.getElementById('pdf-chasis-nombre').value || document.getElementById('input-chasis-tp').value;
    const pregunta = document.getElementById('input-pregunta-esquema').value;
    const contextoActual = document.getElementById('box-test-points').innerText;
    if (!pregunta) return alert("Escribí una pregunta técnica.");

    document.getElementById('box-respuesta-esquema').innerText = "⏳ Analizando circuito para responder...";

    fetch('/api/preguntar-esquematico', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ chasis, pregunta, contexto: contextoActual })
    }).then(r => r.json()).then(data => {
        document.getElementById('box-respuesta-esquema').innerText = data.respuesta || data.error;
    });
}

// 5. CAJA Y FINANZAS
function cargarCaja() {
    fetch('/api/caja').then(r => r.json()).then(data => {
        document.getElementById('caja-ingresos').innerText = `$${data.ingresos.toLocaleString('es-AR', {minimumFractionDigits: 2})}`;
        document.getElementById('caja-egresos').innerText = `$${data.egresos.toLocaleString('es-AR', {minimumFractionDigits: 2})}`;
        document.getElementById('caja-balance').innerText = `$${data.balance.toLocaleString('es-AR', {minimumFractionDigits: 2})}`;

        let html = '';
        data.movimientos.forEach(m => {
            const colorClass = m.tipo === 'Ingreso' ? 'text-success' : 'text-danger';
            html += `<tr onclick="seleccionarMovimientoCaja(${m.id}, this)">
                <td>${m.id}</td>
                <td>${m.fecha}</td>
                <td>${m.tipo}</td>
                <td>${m.concepto}</td>
                <td class="${colorClass}">$${m.monto.toLocaleString('es-AR', {minimumFractionDigits: 2})}</td>
            </tr>`;
        });
        document.getElementById('tabla-caja').innerHTML = html;
    });
}

function seleccionarMovimientoCaja(id, fila) {
    movSeleccionadoId = id;
    document.querySelectorAll('#tabla-caja tr').forEach(r => r.classList.remove('table-active'));
    fila.classList.add('table-active');
}

function guardarMovimientoCaja() {
    const tipo = document.getElementById('caja-tipo').value;
    const concepto = document.getElementById('caja-concepto').value;
    const monto = document.getElementById('caja-monto').value;

    if (!concepto || !monto) {
        alert("Completá el concepto y el monto.");
        return;
    }

    fetch('/api/caja', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({tipo, concepto, monto})
    }).then(() => {
        document.getElementById('caja-concepto').value = '';
        document.getElementById('caja-monto').value = '';
        cargarCaja();
    });
}

function eliminarMovimientoSeleccionado() {
    if (!movSeleccionadoId) return alert("Seleccioná un movimiento de la lista.");
    if (confirm(`¿Eliminar el movimiento N° ${movSeleccionadoId}?`)) {
        fetch(`/api/caja/${movSeleccionadoId}`, { method: 'DELETE' }).then(() => {
            movSeleccionadoId = null;
            cargarCaja();
        });
    }
}

function filtrarCaja() {
    const q = document.getElementById('buscar-caja').value.toLowerCase();
    document.querySelectorAll('#tabla-caja tr').forEach(f => {
        f.style.display = f.innerText.toLowerCase().includes(q) ? '' : 'none';
    });
}

// 6. FIRMWARES
function cargarFirmwares() {
    fetch('/api/firmwares').then(r => r.json()).then(data => {
        let html = '';
        data.forEach(f => {
            html += `<tr><td>${f.chasis}</td><td>${f.modelo}</td><td>${f.memoria}</td><td><a href="${f.url_nube}" target="_blank" class="btn btn-outline-info btn-sm">Descargar</a></td></tr>`;
        });
        document.getElementById('tabla-firmwares').innerHTML = html;
    });
}
