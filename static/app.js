let ordenes = [];
let repuestos = [];
let ventas = [];
let cajaMovimientos = [];
let firmwares = [];

let otSeleccionadaId = null;
let repSeleccionadoId = null;
let vSeleccionadaId = null;
let cajaSeleccionadaId = null;

document.addEventListener('DOMContentLoaded', () => {
    cargarOrdenes();
    cargarRepuestos();
    cargarVentas();
    cargarCaja();
    cargarFirmwares();
});

function mostrarSeccion(sec) {
    const secciones = ['ordenes', 'placas', 'repuestos', 'ventas', 'caja', 'firmwares'];
    secciones.forEach(s => {
        const el = document.getElementById(`sec-${s}`);
        if (el) el.style.display = (s === sec) ? 'block' : 'none';
    });
    
    document.querySelectorAll('.nav-tabs-custom .nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('onclick') && link.getAttribute('onclick').includes(sec)) {
            link.classList.add('active');
        }
    });
}

// --- ÓRDENES ---
async function cargarOrdenes() {
    try {
        const res = await fetch('/api/ordenes');
        ordenes = await res.json();
        renderTablaOT(ordenes);
    } catch (e) { console.error('Error cargando ordenes:', e); }
}

function renderTablaOT(lista) {
    const tbody = document.getElementById('tabla-ordenes');
    if (!tbody) return;
    tbody.innerHTML = '';
    lista.forEach(o => {
        const tr = document.createElement('tr');
        if (otSeleccionadaId === o.id) tr.classList.add('table-primary');
        tr.onclick = () => seleccionarOT(o.id);
        tr.innerHTML = `
            <td>#${o.id}</td>
            <td>${o.cliente || ''}</td>
            <td>${o.telefono || ''}</td>
            <td>${o.equipo || ''}</td>
            <td>${o.falla || ''}</td>
            <td>${o.solucion || ''}</td>
            <td><span class="badge bg-info">${o.estado || 'Ingresado'}</span></td>
            <td>$${parseFloat(o.presupuesto || 0).toFixed(2)}</td>
        `;
        tbody.appendChild(tr);
    });
}

function seleccionarOT(id) {
    otSeleccionadaId = id;
    renderTablaOT(ordenes);
    const o = ordenes.find(x => x.id === id);
    if (o) {
        document.getElementById('box-diagnostico').innerHTML = `
            <strong>Análisis Técnico OT #${o.id} (${o.equipo}):</strong><br>
            Falla: ${o.falla || 'Sin detalle'}<br>
            <em>Consultando circuito en IA...</em>
        `;
        consultarIAOT(o.equipo, o.falla);
    }
}

async function consultarIAOT(equipo, falla) {
    try {
        const res = await fetch('/api/analizar-falla', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ equipo, falla })
        });
        const data = await res.json();
        if (data.diagnostico) {
            document.getElementById('box-diagnostico').innerText = data.diagnostico;
        }
    } catch (e) { console.error(e); }
}

async function guardarOrden() {
    const data = {
        cliente: document.getElementById('ot-cliente').value,
        telefono: document.getElementById('ot-telefono').value,
        equipo: document.getElementById('ot-equipo').value,
        falla: document.getElementById('ot-falla').value,
        solucion: document.getElementById('ot-solucion').value,
        presupuesto: parseFloat(document.getElementById('ot-presupuesto').value) || 0,
        estado: document.getElementById('ot-estado').value
    };

    await fetch('/api/ordenes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    document.getElementById('ot-cliente').value = '';
    document.getElementById('ot-telefono').value = '';
    document.getElementById('ot-equipo').value = '';
    document.getElementById('ot-falla').value = '';
    document.getElementById('ot-solucion').value = '';
    document.getElementById('ot-presupuesto').value = '';
    cargarOrdenes();
}

function filtrarTablaOT() {
    const txt = document.getElementById('buscar-ot').value.toLowerCase();
    const filtradas = ordenes.filter(o => 
        (o.cliente && o.cliente.toLowerCase().includes(txt)) ||
        (o.telefono && o.telefono.toLowerCase().includes(txt)) ||
        (o.equipo && o.equipo.toLowerCase().includes(txt)) ||
        (o.id && o.id.toString().includes(txt))
    );
    renderTablaOT(filtradas);
}

function verFichaOT() {
    if (!otSeleccionadaId) return alert('Seleccioná una orden de la lista.');
    const o = ordenes.find(x => x.id === otSeleccionadaId);
    if (!o) return;

    const html = `
        <p><strong>N° Orden:</strong> #${o.id}</p>
        <p><strong>Cliente:</strong> ${o.cliente || ''}</p>
        <p><strong>Teléfono:</strong> ${o.telefono || ''}</p>
        <p><strong>Equipo:</strong> ${o.equipo || ''}</p>
        <p><strong>Falla Reportada:</strong> ${o.falla || ''}</p>
        <p><strong>Solución Aplicada:</strong> ${o.solucion || ''}</p>
        <p><strong>Estado:</strong> ${o.estado || ''}</p>
        <p><strong>Presupuesto:</strong> $${parseFloat(o.presupuesto || 0).toFixed(2)}</p>
    `;
    document.getElementById('contenido-ficha').innerHTML = html;
    document.getElementById('modal-ficha').style.display = 'block';
}

function cerrarFicha() {
    document.getElementById('modal-ficha').style.display = 'none';
}

function enviarWhatsApp() {
    if (!otSeleccionadaId) return alert('Seleccioná una orden.');
    const o = ordenes.find(x => x.id === otSeleccionadaId);
    if (!o || !o.telefono) return alert('La orden no tiene teléfono registrado.');
    
    const num = o.telefono.replace(/[^0-9]/g, '');
    const msg = `Hola ${o.cliente}, te contactamos del Taller por tu equipo ${o.equipo}. Estado: ${o.estado}. Presupuesto: $${o.presupuesto}`;
    window.open(`https://wa.me/549${num}?text=${encodeURIComponent(msg)}`, '_blank');
}

function enviarWhatsAppModal() {
    enviarWhatsApp();
}

function generarComprobanteImpresion() {
    if (!otSeleccionadaId) return alert('Seleccioná una orden.');
    const o = ordenes.find(x => x.id === otSeleccionadaId);
    if (!o) return;

    document.getElementById('imp-ot-num').innerText = `OT #${o.id}`;
    document.getElementById('imp-cliente').innerText = o.cliente || '---';
    document.getElementById('imp-telefono').innerText = o.telefono || '---';
    document.getElementById('imp-equipo').innerText = o.equipo || '---';
    document.getElementById('imp-falla').innerText = o.falla || '---';
    document.getElementById('imp-estado').innerText = o.estado || '---';
    document.getElementById('imp-presupuesto').innerText = parseFloat(o.presupuesto || 0).toFixed(2);
    document.getElementById('imp-fecha').innerText = `Fecha: ${new Date().toLocaleDateString('es-AR')}`;

    const qrContainer = document.getElementById('imp-qr-container');
    if (qrContainer) {
        qrContainer.innerHTML = '';
        const qrText = `OT:${o.id}|CLIENTE:${o.cliente}|EQUIPO:${o.equipo}|ESTADO:${o.estado}`;
        new QRCode(qrContainer, {
            text: qrText,
            width: 100,
            height: 100
        });
    }

    const area = document.getElementById('area-impresion');
    area.style.display = 'block';
    window.print();
    area.style.display = 'none';
}

function exportarOrdenesExcel() {
    window.location.href = '/api/exportar-ordenes';
}

async function eliminarOrdenSeleccionada() {
    if (!otSeleccionadaId) return alert('Seleccioná una orden para eliminar.');
    if (confirm(`¿Eliminar la orden #${otSeleccionadaId}?`)) {
        await fetch(`/api/ordenes/${otSeleccionadaId}`, { method: 'DELETE' });
        otSeleccionadaId = null;
        cargarOrdenes();
    }
}

// --- BANCO DE PLACAS Y IA ---
async function buscarFallasRecurrentes() {
    const chasis = document.getElementById('input-chasis-fallas').value;
    if (!chasis) return alert('Ingresá un chasis o modelo.');
    document.getElementById('box-test-points').innerText = 'Buscando fallas recurrentes...';
    try {
        const res = await fetch('/api/fallas-recurrentes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chasis })
        });
        const data = await res.json();
        document.getElementById('box-test-points').innerText = data.resultado || data.error || 'Sin datos';
    } catch (e) { console.error(e); }
}

function buscarEnPlataforma(plat) {
    const chasis = document.getElementById('input-chasis-fallas').value;
    if (!chasis) return alert('Ingresá un chasis.');
    let url = '';
    if (plat === 'youtube') url = `https://www.youtube.com/results?search_query=${encodeURIComponent('falla ' + chasis)}`;
    if (plat === 'telegram') url = `https://t.me/s/electronica?q=${encodeURIComponent(chasis)}`;
    if (plat === 'google') url = `https://www.google.com/search?q=${encodeURIComponent('falla ' + chasis + ' reparacion tv')}`;
    window.open(url, '_blank');
}

async function buscarTestPoints() {
    const chasis = document.getElementById('input-chasis-tp').value;
    if (!chasis) return alert('Ingresá un chasis.');
    document.getElementById('box-test-points').innerText = 'Consultando Test Points...';
    try {
        const res = await fetch('/api/fallas-recurrentes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chasis })
        });
        const data = await res.json();
        document.getElementById('box-test-points').innerText = data.resultado || data.error || 'Sin datos';
    } catch (e) { console.error(e); }
}

async function procesarEsquematicoPDF() {
    const chasis = document.getElementById('pdf-chasis-nombre').value;
    const fileInput = document.getElementById('pdf-archivo');
    if (!chasis || !fileInput.files[0]) return alert('Ingresá el chasis y adjuntá el archivo PDF.');

    const formData = new FormData();
    formData.append('chasis', chasis);
    formData.append('archivo', fileInput.files[0]);

    document.getElementById('box-test-points').innerText = 'Analizando PDF con IA...';
    try {
        const res = await fetch('/api/analizar-esquematico-pdf', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        document.getElementById('box-test-points').innerText = data.resultado || data.error || 'Sin resultado';
    } catch (e) { console.error(e); }
}

async function preguntarSobreEsquema() {
    const chasis = document.getElementById('pdf-chasis-nombre').value || document.getElementById('input-chasis-tp').value;
    const pregunta = document.getElementById('input-pregunta-esquema').value;
    const contexto = document.getElementById('box-test-points').innerText;

    if (!pregunta) return alert('Ingresá tu pregunta.');

    document.getElementById('box-respuesta-esquema').innerText = 'Consultando...';
    try {
        const res = await fetch('/api/preguntar-esquematico', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chasis, pregunta, contexto })
        });
        const data = await res.json();
        document.getElementById('box-respuesta-esquema').innerText = data.respuesta || data.error || 'Sin respuesta';
    } catch (e) { console.error(e); }
}

// --- REPUESTOS ---
async function cargarRepuestos() {
    try {
        const res = await fetch('/api/repuestos');
        repuestos = await res.json();
        renderTablaRepuestos(repuestos);
    } catch (e) { console.error(e); }
}

function renderTablaRepuestos(lista) {
    const tbody = document.getElementById('tabla-repuestos');
    if (!tbody) return;
    tbody.innerHTML = '';
    lista.forEach(r => {
        const tr = document.createElement('tr');
        if (repSeleccionadoId === r.id) tr.classList.add('table-success');
        tr.onclick = () => { repSeleccionadoId = r.id; renderTablaRepuestos(repuestos); };
        tr.innerHTML = `
            <td>#${r.id}</td>
            <td>${r.categoria || ''}</td>
            <td><strong>${r.nombre || ''}</strong></td>
            <td>${r.ubicacion || ''}</td>
            <td><span class="badge bg-success fs-6">${r.cantidad || 0}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

async function guardarRepuesto() {
    const data = {
        categoria: document.getElementById('rep-cat').value,
        nombre: document.getElementById('rep-nombre').value,
        ubicacion: document.getElementById('rep-ubicacion').value,
        cantidad: parseInt(document.getElementById('rep-cant').value) || 1
    };

    await fetch('/api/repuestos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    document.getElementById('rep-nombre').value = '';
    document.getElementById('rep-ubicacion').value = '';
    document.getElementById('rep-cant').value = '1';
    cargarRepuestos();
}

function filtrarComp() {
    const txt = document.getElementById('buscar-comp').value.toLowerCase();
    const filtrados = repuestos.filter(r => 
        (r.nombre && r.nombre.toLowerCase().includes(txt)) ||
        (r.categoria && r.categoria.toLowerCase().includes(txt)) ||
        (r.ubicacion && r.ubicacion.toLowerCase().includes(txt))
    );
    renderTablaRepuestos(filtrados);
}

async function modificarStock(delta) {
    if (!repSeleccionadoId) return alert('Seleccioná un componente.');
    const r = repuestos.find(x => x.id === repSeleccionadoId);
    if (!r) return;
    const nuevaCant = Math.max(0, (r.cantidad || 0) + delta);
    await fetch(`/api/repuestos/${repSeleccionadoId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cantidad: nuevaCant })
    });
    cargarRepuestos();
}

async function cambiarCantidadModal() {
    if (!repSeleccionadoId) return alert('Seleccioná un componente.');
    const c = prompt('Ingresá la nueva cantidad total:');
    if (c !== null && !isNaN(parseInt(c))) {
        await fetch(`/api/repuestos/${repSeleccionadoId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cantidad: parseInt(c) })
        });
        cargarRepuestos();
    }
}

async function cambiarUbicacionModal() {
    if (!repSeleccionadoId) return alert('Seleccioná un componente.');
    const u = prompt('Ingresá la nueva gaveta/ubicación:');
    if (u) {
        await fetch(`/api/repuestos/${repSeleccionadoId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ubicacion: u })
        });
        cargarRepuestos();
    }
}

function buscarDatasheet() {
    if (!repSeleccionadoId) return alert('Seleccioná un componente.');
    const r = repuestos.find(x => x.id === repSeleccionadoId);
    if (r) {
        window.open(`https://www.google.com/search?q=${encodeURIComponent(r.nombre + ' datasheet pdf')}`, '_blank');
    }
}

function imprimirEtiqueta() {
    if (!repSeleccionadoId) return alert('Seleccioná un componente.');
    const r = repuestos.find(x => x.id === repSeleccionadoId);
    if (r) {
        alert(`Imprimiendo etiqueta para: ${r.nombre} - Ubicación: ${r.ubicacion}`);
    }
}

// --- VENTAS ---
async function cargarVentas() {
    try {
        const res = await fetch('/api/ventas');
        ventas = await res.json();
        renderTablaVentas(ventas);
    } catch (e) { console.error(e); }
}

function renderTablaVentas(lista) {
    const tbody = document.getElementById('tabla-ventas');
    if (!tbody) return;
    tbody.innerHTML = '';
    lista.forEach(v => {
        const tr = document.createElement('tr');
        if (vSeleccionadaId === v.id) tr.classList.add('table-warning');
        tr.onclick = () => { vSeleccionadaId = v.id; renderTablaVentas(ventas); };
        tr.innerHTML = `
            <td>#${v.id}</td>
            <td>${v.producto || ''}</td>
            <td>$${parseFloat(v.precio || 0).toFixed(2)}</td>
            <td><span class="badge bg-warning text-dark">${v.estado || 'En Venta'}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

async function guardarVenta() {
    const data = {
        producto: document.getElementById('v-producto').value,
        precio: parseFloat(document.getElementById('v-precio').value) || 0,
        estado: document.getElementById('v-estado').value
    };

    await fetch('/api/ventas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    document.getElementById('v-producto').value = '';
    document.getElementById('v-precio').value = '';
    cargarVentas();
}

function consultarML() {
    const p = document.getElementById('v-producto').value;
    if (!p) return alert('Ingresá el nombre del producto.');
    window.open(`https://listado.mercadolibre.com.ar/${encodeURIComponent(p)}`, '_blank');
}

async function eliminarVentaSeleccionada() {
    if (!vSeleccionadaId) return alert('Seleccioná un registro.');
    if (confirm('¿Eliminar esta publicación?')) {
        await fetch(`/api/ventas/${vSeleccionadaId}`, { method: 'DELETE' });
        vSeleccionadaId = null;
        cargarVentas();
    }
}

// --- CAJA ---
async function cargarCaja() {
    try {
        const res = await fetch('/api/caja');
        const data = await res.json();
        cajaMovimientos = data.movimientos || [];
        
        document.getElementById('caja-ingresos').innerText = `$${parseFloat(data.ingresos || 0).toFixed(2)}`;
        document.getElementById('caja-egresos').innerText = `$${parseFloat(data.egresos || 0).toFixed(2)}`;
        document.getElementById('caja-balance').innerText = `$${parseFloat(data.balance || 0).toFixed(2)}`;

        renderTablaCaja(cajaMovimientos);
    } catch (e) { console.error(e); }
}

function renderTablaCaja(lista) {
    const tbody = document.getElementById('tabla-caja');
    if (!tbody) return;
    tbody.innerHTML = '';
    lista.forEach(m => {
        const tr = document.createElement('tr');
        if (cajaSeleccionadaId === m.id) tr.classList.add('table-info');
        tr.onclick = () => { cajaSeleccionadaId = m.id; renderTablaCaja(cajaMovimientos); };
        tr.innerHTML = `
            <td>#${m.id}</td>
            <td>${m.fecha || ''}</td>
            <td><span class="badge ${m.tipo === 'Ingreso' ? 'bg-success' : 'bg-danger'}">${m.tipo}</span></td>
            <td>${m.concepto || ''}</td>
            <td>$${parseFloat(m.monto || 0).toFixed(2)}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function guardarMovimientoCaja() {
    const data = {
        tipo: document.getElementById('caja-tipo').value,
        concepto: document.getElementById('caja-concepto').value,
        monto: parseFloat(document.getElementById('caja-monto').value) || 0
    };

    await fetch('/api/caja', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    document.getElementById('caja-concepto').value = '';
    document.getElementById('caja-monto').value = '';
    cargarCaja();
}

function filtrarCaja() {
    const txt = document.getElementById('buscar-caja').value.toLowerCase();
    const filtrados = cajaMovimientos.filter(m => 
        (m.concepto && m.concepto.toLowerCase().includes(txt)) ||
        (m.tipo && m.tipo.toLowerCase().includes(txt)) ||
        (m.fecha && m.fecha.toLowerCase().includes(txt))
    );
    renderTablaCaja(filtrados);
}

async function eliminarMovimientoSeleccionado() {
    if (!cajaSeleccionadaId) return alert('Seleccioná un movimiento.');
    if (confirm('¿Eliminar este movimiento de caja?')) {
        await fetch(`/api/caja/${cajaSeleccionadaId}`, { method: 'DELETE' });
        cajaSeleccionadaId = null;
        cargarCaja();
    }
}

// --- FIRMWARES ---
async function cargarFirmwares() {
    try {
        const res = await fetch('/api/firmwares');
        firmwares = await res.json();
        renderTablaFirmwares(firmwares);
    } catch (e) { console.error(e); }
}

function renderTablaFirmwares(lista) {
    const tbody = document.getElementById('tabla-firmwares');
    if (!tbody) return;
    tbody.innerHTML = '';
    lista.forEach(f => {
        tbody.innerHTML += `
            <tr>
                <td><strong>${f.chasis}</strong></td>
                <td>${f.modelo || ''}</td>
                <td>${f.memoria || ''}</td>
                <td><a href="${f.url_nube}" target="_blank" class="btn btn-sm btn-info text-white">Descargar</a></td>
            </tr>
        `;
    });
}

function filtrarFirmwares() {
    const txt = document.getElementById('fw-buscar').value.toLowerCase();
    const filtrados = firmwares.filter(f => 
        (f.chasis && f.chasis.toLowerCase().includes(txt)) ||
        (f.modelo && f.modelo.toLowerCase().includes(txt))
    );
    renderTablaFirmwares(filtrados);
}

function pedirFirmwareWhatsApp() {
    const txt = document.getElementById('fw-buscar').value;
    if (!txt) return alert('Ingresá el chasis o modelo.');
    window.open(`https://wa.me/5491112345678?text=${encodeURIComponent('Hola, necesito el firmware para el chasis/modelo: ' + txt)}`, '_blank');
}
