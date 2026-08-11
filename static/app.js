let ordenesData = [];
let repuestosData = [];
let ventasData = [];
let cajaData = [];
let firmwaresData = [];

let otSeleccionada = null;
let repSeleccionado = null;
let vtaSeleccionada = null;
let cajaSeleccionado = null;

document.addEventListener('DOMContentLoaded', () => {
    cargarOrdenes();
    cargarRepuestos();
    cargarVentas();
    cargarCaja();
    cargarFirmwares();
});

function mostrarSeccion(sec) {
    document.querySelectorAll('[id^="sec-"]').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.nav-tabs-custom .nav-link').forEach(el => el.classList.remove('active'));

    const objetivo = document.getElementById(`sec-${sec}`);
    if (objetivo) objetivo.style.display = 'block';

    const link = Array.from(document.querySelectorAll('.nav-tabs-custom .nav-link')).find(el => el.getAttribute('onclick').includes(sec));
    if (link) link.classList.add('active');
}

// --- FUNCIÓN HELPER SUBIDA CLOUDINARY ---
async function subirFotoCloudinary(inputId) {
    const fileInput = document.getElementById(inputId);
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        return null;
    }

    const formData = new FormData();
    formData.append('archivo', fileInput.files[0]);

    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.error || 'Error subiendo la imagen');
        }

        const data = await res.json();
        return data.url;
    } catch (err) {
        console.error('Error al subir la foto a Cloudinary:', err);
        alert('Atención: No se pudo subir la foto. ' + err.message);
        return null;
    }
}

// --- 1. ÓRDENES DE TRABAJO ---
async function cargarOrdenes() {
    try {
        const res = await fetch('/api/ordenes');
        ordenesData = await res.json();
        renderTablaOrdenes(ordenesData);
    } catch (e) {
        console.error("Error cargando órdenes:", e);
    }
}

function renderTablaOrdenes(lista) {
    const tbody = document.getElementById('tabla-ordenes');
    if (!tbody) return;
    tbody.innerHTML = '';
    lista.forEach(o => {
        const tr = document.createElement('tr');
        if (otSeleccionada && otSeleccionada.id === o.id) tr.classList.add('table-active');
        tr.onclick = () => seleccionarOrden(o, tr);
        tr.innerHTML = `
            <td>OT-${o.id}</td>
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

function seleccionarOrden(o, tr) {
    otSeleccionada = o;
    document.querySelectorAll('#tabla-ordenes tr').forEach(r => r.classList.remove('table-active'));
    tr.classList.add('table-active');
    analizarCircuitoIA(o);
}

async function guardarOrden() {
    const cliente = document.getElementById('ot-cliente').value.trim();
    const telefono = document.getElementById('ot-telefono').value.trim();
    const equipo = document.getElementById('ot-equipo').value.trim();
    const estado = document.getElementById('ot-estado').value;
    let falla = document.getElementById('ot-falla').value.trim();
    const solucion = document.getElementById('ot-solucion').value.trim();
    const presupuesto = document.getElementById('ot-presupuesto').value;

    if (!cliente || !equipo) {
        alert("Por favor completá al menos el Cliente y el Equipo.");
        return;
    }

    // Procesa la foto en Cloudinary si se seleccionó un archivo
    const urlFoto = await subirFotoCloudinary('ot-foto');
    if (urlFoto) {
        falla += ` | Foto Adjunta: ${urlFoto}`;
    }

    await fetch('/api/ordenes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cliente, telefono, equipo, falla, solucion, presupuesto, estado })
    });

    document.getElementById('ot-cliente').value = '';
    document.getElementById('ot-telefono').value = '';
    document.getElementById('ot-equipo').value = '';
    document.getElementById('ot-falla').value = '';
    document.getElementById('ot-solucion').value = '';
    document.getElementById('ot-presupuesto').value = '';
    const fotoInput = document.getElementById('ot-foto');
    if (fotoInput) fotoInput.value = '';

    cargarOrdenes();
}

function filtrarTablaOT() {
    const q = document.getElementById('buscar-ot').value.toLowerCase();
    const filtradas = ordenesData.filter(o => 
        (o.cliente && o.cliente.toLowerCase().includes(q)) ||
        (o.telefono && o.telefono.toLowerCase().includes(q)) ||
        (o.equipo && o.equipo.toLowerCase().includes(q)) ||
        (o.id && o.id.toString().includes(q))
    );
    renderTablaOrdenes(filtradas);
}

function verFichaOT() {
    if (!otSeleccionada) { alert("Seleccioná una orden de la lista primero."); return; }
    const modal = document.getElementById('modal-ficha');
    const cont = document.getElementById('contenido-ficha');
    cont.innerHTML = `
        <p><strong>ORDEN N°:</strong> OT-${otSeleccionada.id}</p>
        <p><strong>CLIENTE:</strong> ${otSeleccionada.cliente || 'S/D'} | <strong>TELÉFONO:</strong> ${otSeleccionada.telefono || 'S/D'}</p>
        <p><strong>EQUIPO / MODELO:</strong> ${otSeleccionada.equipo || 'S/D'}</p>
        <p><strong>FALLA REPORTADA:</strong> ${otSeleccionada.falla || 'S/D'}</p>
        <p><strong>TRABAJO / SOLUCIÓN:</strong> ${otSeleccionada.solucion || 'Pendiente'}</p>
        <p><strong>ESTADO:</strong> ${otSeleccionada.estado || 'Ingresado'}</p>
        <p><strong>PRESUPUESTO ESTIMADO:</strong> $${parseFloat(otSeleccionada.presupuesto || 0).toFixed(2)}</p>
    `;
    modal.style.display = 'block';
}

function cerrarFicha() {
    document.getElementById('modal-ficha').style.display = 'none';
}

function enviarWhatsApp() {
    if (!otSeleccionada || !otSeleccionada.telefono) { alert("Seleccioná una orden con teléfono válido."); return; }
    const num = otSeleccionada.telefono.replace(/[^0-9]/g, '');
    const msg = encodeURIComponent(`Hola ${otSeleccionada.cliente}, te contactamos de Servicio Técnico por tu equipo ${otSeleccionada.equipo} (OT-${otSeleccionada.id}). Estado actual: ${otSeleccionada.estado}. Presupuesto: $${otSeleccionada.presupuesto}`);
    window.open(`https://wa.me/${num}?text=${msg}`, '_blank');
}

function enviarWhatsAppModal() { enviarWhatsApp(); }

function generarComprobanteImpresion() {
    if (!otSeleccionada) { alert("Seleccioná una orden primero."); return; }
    document.getElementById('imp-ot-num').innerText = `OT #${otSeleccionada.id}`;
    document.getElementById('imp-fecha').innerText = `Fecha: ${new Date().toLocaleDateString('es-AR')}`;
    document.getElementById('imp-cliente').innerText = otSeleccionada.cliente || '---';
    document.getElementById('imp-telefono').innerText = otSeleccionada.telefono || '---';
    document.getElementById('imp-equipo').innerText = otSeleccionada.equipo || '---';
    document.getElementById('imp-falla').innerText = otSeleccionada.falla || '---';
    document.getElementById('imp-estado').innerText = otSeleccionada.estado || '---';
    document.getElementById('imp-presupuesto').innerText = parseFloat(otSeleccionada.presupuesto || 0).toFixed(2);
    
    document.getElementById('imp-qr').src = `https://api.qrserver.com/v1/create-qr-code/?size=100x100&data=OT-${otSeleccionada.id}`;
    
    const area = document.getElementById('area-impresion');
    area.style.display = 'block';
    window.print();
    area.style.display = 'none';
}

function generarEtiquetaTapaQR() {
    if (!otSeleccionada) { alert("Seleccioná una orden primero."); return; }
    document.getElementById('lbl-qr-ot').innerText = `OT-${otSeleccionada.id}`;
    document.getElementById('lbl-qr-cliente').innerText = otSeleccionada.cliente || '---';
    document.getElementById('lbl-qr-equipo').innerText = otSeleccionada.equipo || '---';

    const urlConsulta = `${window.location.origin}/consulta?ot=${otSeleccionada.id}`;
    document.getElementById('lbl-qr-img').src = `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(urlConsulta)}`;

    const area = document.getElementById('area-impresion-qr-tapa');
    area.style.display = 'block';
    window.print();
    area.style.display = 'none';
}

async function eliminarOrdenSeleccionada() {
    if (!otSeleccionada) { alert("Seleccioná una orden primero."); return; }
    if (confirm(`¿Eliminar definitivamente la OT-${otSeleccionada.id}?`)) {
        await fetch(`/api/ordenes/${otSeleccionada.id}`, { method: 'DELETE' });
        otSeleccionada = null;
        cargarOrdenes();
    }
}

async function analizarCircuitoIA(o) {
    const box = document.getElementById('box-diagnostico');
    box.innerText = "Analizando falla con IA...";
    try {
        const res = await fetch('/api/analizar-falla', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ equipo: o.equipo, falla: o.falla })
        });
        const data = await res.json();
        box.innerText = data.diagnostico || data.error || "Sin resultado.";
    } catch (e) {
        box.innerText = "Error al consultar el diagnóstico.";
    }
}

// --- 2. BANCO DE PLACAS Y FALLAS ---
async function buscarFallasRecurrentes() {
    const chasis = document.getElementById('input-chasis-fallas').value.trim();
    if (!chasis) { alert("Ingresá un chasis o modelo."); return; }
    const box = document.getElementById('box-test-points');
    box.innerText = "Consultando base de fallas...";
    const res = await fetch('/api/obtener-test-points', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chasis })
    });
    const data = await res.json();
    box.innerText = data.test_points || data.error || "Sin registros.";
}

function buscarEnPlataforma(plat) {
    const chasis = document.getElementById('input-chasis-fallas').value.trim();
    if (!chasis) { alert("Ingresá un chasis o modelo."); return; }
    if (plat === 'youtube') window.open(`https://www.youtube.com/results?search_query=${encodeURIComponent(chasis + ' falla reparacion')}`, '_blank');
    if (plat === 'telegram') window.open(`https://t.me/s/${encodeURIComponent(chasis)}`, '_blank');
    if (plat === 'google') window.open(`https://www.google.com/search?q=${encodeURIComponent(chasis + ' falla solucion tv')}`, '_blank');
}

function buscarTestPoints() {
    const chasis = document.getElementById('input-chasis-tp').value.trim();
    if (chasis) {
        document.getElementById('input-chasis-fallas').value = chasis;
        buscarFallasRecurrentes();
    }
}

async function procesarEsquematicoPDF() {
    const chasis = document.getElementById('pdf-chasis-nombre').value.trim();
    const fileInput = document.getElementById('pdf-archivo');
    if (!fileInput.files.length) { alert("Seleccioná un archivo PDF."); return; }

    const box = document.getElementById('box-test-points');
    box.innerText = "Procesando y analizando PDF...";

    const formData = new FormData();
    formData.append('chasis', chasis);
    formData.append('archivo', fileInput.files[0]);

    const res = await fetch('/api/analizar-esquematico-pdf', { method: 'POST', body: formData });
    const data = await res.json();
    box.innerText = data.resultado || data.error || "Error analizando PDF.";
}

async function preguntarSobreEsquema() {
    const pregunta = document.getElementById('input-pregunta-esquema').value.trim();
    const contexto = document.getElementById('box-test-points').innerText;
    const chasis = document.getElementById('input-chasis-fallas').value.trim();
    if (!pregunta) return;

    const box = document.getElementById('box-respuesta-esquema');
    box.innerText = "Consultando...";

    const res = await fetch('/api/preguntar-esquematico', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chasis, pregunta, contexto })
    });
    const data = await res.json();
    box.innerText = data.respuesta || data.error || "Sin respuesta.";
}

// --- 3. STOCK COMPONENTES ---
async function cargarRepuestos() {
    const res = await fetch('/api/repuestos');
    repuestosData = await res.json();
    renderTablaRepuestos(repuestosData);
}

function renderTablaRepuestos(lista) {
    const tbody = document.getElementById('tabla-repuestos');
    if (!tbody) return;
    tbody.innerHTML = '';
    lista.forEach(r => {
        const tr = document.createElement('tr');
        if (repSeleccionado && repSeleccionado.id === r.id) tr.classList.add('table-active');
        tr.onclick = () => {
            repSeleccionado = r;
            document.querySelectorAll('#tabla-repuestos tr').forEach(row => row.classList.remove('table-active'));
            tr.classList.add('table-active');
        };
        tr.innerHTML = `
            <td>REP-${r.id}</td>
            <td>${r.categoria || ''}</td>
            <td>${r.nombre || ''}</td>
            <td>${r.ubicacion || 'S/D'}</td>
            <td><span class="badge bg-${r.cantidad > 0 ? 'success' : 'danger'}">${r.cantidad}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

async function guardarRepuesto() {
    const categoria = document.getElementById('rep-cat').value;
    const nombre = document.getElementById('rep-nombre').value.trim();
    const ubicacion = document.getElementById('rep-ubicacion').value.trim();
    const cantidad = document.getElementById('rep-cant').value;

    if (!nombre) { alert("Ingresá el código o nombre del componente."); return; }

    await fetch('/api/repuestos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ categoria, nombre, ubicacion, cantidad, precio: 0 })
    });

    document.getElementById('rep-nombre').value = '';
    document.getElementById('rep-ubicacion').value = '';
    cargarRepuestos();
}

function filtrarComp() {
    const q = document.getElementById('buscar-comp').value.toLowerCase();
    const filtrados = repuestosData.filter(r => 
        (r.nombre && r.nombre.toLowerCase().includes(q)) ||
        (r.categoria && r.categoria.toLowerCase().includes(q)) ||
        (r.ubicacion && r.ubicacion.toLowerCase().includes(q))
    );
    renderTablaRepuestos(filtrados);
}

async function modificarStock(delta) {
    if (!repSeleccionado) { alert("Seleccioná un componente primero."); return; }
    const nuevaCant = parseInt(repSeleccionado.cantidad || 0) + delta;
    if (nuevaCant < 0) return;
    await fetch(`/api/repuestos/${repSeleccionado.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cantidad: nuevaCant })
    });
    cargarRepuestos();
}

async function cambiarCantidadModal() {
    if (!repSeleccionado) { alert("Seleccioná un componente primero."); return; }
    const c = prompt("Nueva cantidad:", repSeleccionado.cantidad);
    if (c !== null) {
        await fetch(`/api/repuestos/${repSeleccionado.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cantidad: parseInt(c) })
        });
        cargarRepuestos();
    }
}

async function cambiarUbicacionModal() {
    if (!repSeleccionado) { alert("Seleccioná un componente primero."); return; }
    const u = prompt("Nueva ubicación / gaveta:", repSeleccionado.ubicacion);
    if (u !== null) {
        await fetch(`/api/repuestos/${repSeleccionado.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ubicacion: u })
        });
        cargarRepuestos();
    }
}

function buscarDatasheet() {
    if (!repSeleccionado) { alert("Seleccioná un componente de la lista."); return; }
    window.open(`https://www.google.com/search?q=${encodeURIComponent(repSeleccionado.nombre + ' datasheet pdf')}`, '_blank');
}

function imprimirEtiqueta() {
    if (!repSeleccionado) { alert("Seleccioná un componente primero."); return; }
    const area = document.getElementById('area-impresion');
    area.innerHTML = `
        <div style="border: 2px solid #000; padding: 10px; width: 220px; text-align: center; font-family: sans-serif;">
            <h5 style="margin:0;">LAB-CONTROL</h5>
            <p style="font-weight:bold; font-size:16px; margin:5px 0;">${repSeleccionado.nombre}</p>
            <p style="font-size:12px; margin:0;">Ubicación: ${repSeleccionado.ubicacion || 'S/D'}</p>
        </div>
    `;
    area.style.display = 'block';
    window.print();
    area.style.display = 'none';
}

// --- 4. VENTAS Y USADOS ---
async function cargarVentas() {
    const res = await fetch('/api/ventas');
    ventasData = await res.json();
    renderTablaVentas(ventasData);
}

function renderTablaVentas(lista) {
    const tbody = document.getElementById('tabla-ventas');
    if (!tbody) return;
    tbody.innerHTML = '';
    lista.forEach(v => {
        const tr = document.createElement('tr');
        if (vtaSeleccionada && vtaSeleccionada.id === v.id) tr.classList.add('table-active');
        tr.onclick = () => {
            vtaSeleccionada = v;
            document.querySelectorAll('#tabla-ventas tr').forEach(row => row.classList.remove('table-active'));
            tr.classList.add('table-active');
        };
        tr.innerHTML = `
            <td>VTA-${v.id}</td>
            <td>${v.producto || ''}</td>
            <td>$${parseFloat(v.precio || 0).toFixed(2)}</td>
            <td><span class="badge bg-info">${v.estado || 'En Venta'}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

async function guardarVenta() {
    const producto = document.getElementById('v-producto').value.trim();
    const precio = document.getElementById('v-precio').value;
    const estado = document.getElementById('v-estado').value;

    if (!producto) { alert("Ingresá la descripción del producto."); return; }

    await fetch('/api/ventas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ producto, precio, estado })
    });

    document.getElementById('v-producto').value = '';
    document.getElementById('v-precio').value = '';
    cargarVentas();
}

function consultarML() {
    const prod = document.getElementById('v-producto').value.trim() || (vtaSeleccionada ? vtaSeleccionada.producto : '');
    if (!prod) { alert("Ingresá un producto para buscar en MercadoLibre."); return; }
    window.open(`https://listado.mercadolibre.com.ar/${encodeURIComponent(prod)}`, '_blank');
}

async function eliminarVentaSeleccionada() {
    if (!vtaSeleccionada) { alert("Seleccioná un registro primero."); return; }
    if (confirm("¿Eliminar publicación?")) {
        await fetch(`/api/ventas/${vtaSeleccionada.id}`, { method: 'DELETE' });
        vtaSeleccionada = null;
        cargarVentas();
    }
}

// --- 5. CAJA Y FINANZAS ---
async function cargarCaja() {
    const res = await fetch('/api/caja');
    const data = await res.json();
    cajaData = data.movimientos || [];
    renderTablaCaja(cajaData);

    document.getElementById('caja-ingresos').innerText = `$${parseFloat(data.ingresos || 0).toFixed(2)}`;
    document.getElementById('caja-egresos').innerText = `$${parseFloat(data.egresos || 0).toFixed(2)}`;
    document.getElementById('caja-balance').innerText = `$${parseFloat(data.balance || 0).toFixed(2)}`;
}

function renderTablaCaja(lista) {
    const tbody = document.getElementById('tabla-caja');
    if (!tbody) return;
    tbody.innerHTML = '';
    lista.forEach(m => {
        const tr = document.createElement('tr');
        if (cajaSeleccionado && cajaSeleccionado.id === m.id) tr.classList.add('table-active');
        tr.onclick = () => {
            cajaSeleccionado = m;
            document.querySelectorAll('#tabla-caja tr').forEach(row => row.classList.remove('table-active'));
            tr.classList.add('table-active');
        };
        tr.innerHTML = `
            <td>MOV-${m.id}</td>
            <td>${m.fecha || ''}</td>
            <td><span class="badge bg-${m.tipo === 'Ingreso' ? 'success' : 'danger'}">${m.tipo}</span></td>
            <td>${m.concepto || ''}</td>
            <td>$${parseFloat(m.monto || 0).toFixed(2)}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function guardarMovimientoCaja() {
    const tipo = document.getElementById('caja-tipo').value;
    const concepto = document.getElementById('caja-concepto').value.trim();
    const monto = document.getElementById('caja-monto').value;

    if (!concepto || !monto) { alert("Completá el concepto y el monto."); return; }

    await fetch('/api/caja', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tipo, concepto, monto })
    });

    document.getElementById('caja-concepto').value = '';
    document.getElementById('caja-monto').value = '';
    cargarCaja();
}

function filtrarCaja() {
    const q = document.getElementById('buscar-caja').value.toLowerCase();
    const filtrados = cajaData.filter(m => 
        (m.concepto && m.concepto.toLowerCase().includes(q)) ||
        (m.tipo && m.tipo.toLowerCase().includes(q)) ||
        (m.fecha && m.fecha.toLowerCase().includes(q))
    );
    renderTablaCaja(filtrados);
}

async function eliminarMovimientoSeleccionado() {
    if (!cajaSeleccionado) { alert("Seleccioná un movimiento de caja primero."); return; }
    if (confirm("¿Eliminar registro de caja?")) {
        await fetch(`/api/caja/${cajaSeleccionado.id}`, { method: 'DELETE' });
        cajaSeleccionado = null;
        cargarCaja();
    }
}

// --- 6. FIRMWARES NUBE ---
async function cargarFirmwares() {
    const res = await fetch('/api/firmwares');
    firmwaresData = await res.json();
    renderTablaFirmwares(firmwaresData);
}

function renderTablaFirmwares(lista) {
    const tbody = document.getElementById('tabla-firmwares');
    if (!tbody) return;
    tbody.innerHTML = '';
    lista.forEach(f => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${f.chasis || ''}</td>
            <td>${f.modelo || ''}</td>
            <td>${f.memoria || ''}</td>
            <td><a href="${f.url_nube}" target="_blank" class="btn btn-sm btn-outline-info">Descargar Dump / FW</a></td>
        `;
        tbody.appendChild(tr);
    });
}

function filtrarFirmwares() {
    const q = document.getElementById('fw-buscar').value.toLowerCase();
    const filtrados = firmwaresData.filter(f => 
        (f.chasis && f.chasis.toLowerCase().includes(q)) ||
        (f.modelo && f.modelo.toLowerCase().includes(q))
    );
    renderTablaFirmwares(filtrados);
}

function pedirFirmwareWhatsApp() {
    const q = document.getElementById('fw-buscar').value.trim();
    const msg = encodeURIComponent(`Hola, necesito solicitar el firmware / dump para el chasis/modelo: ${q || 'S/D'}`);
    window.open(`https://wa.me/5491164992829?text=${msg}`, '_blank');
}
