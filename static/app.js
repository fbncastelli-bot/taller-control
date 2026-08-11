// LAB-CONTROL PRO v4.2 - Código Base Completo Original

let ordenesData = [];
let repuestosData = [];
let ventasData = [];
let cajaData = [];
let firmwaresData = [];

let otSeleccionada = null;
let repSeleccionado = null;
let ventaSeleccionada = null;
let cajaSeleccionado = null;

document.addEventListener('DOMContentLoaded', () => {
    cargarOrdenes();
    cargarRepuestos();
    cargarVentas();
    cargarCaja();
    cargarFirmwares();
});

// Navegación de pestañas
function mostrarSeccion(seccionId) {
    document.querySelectorAll('.seccion-contenido').forEach(el => el.classList.add('d-none'));
    const seccion = document.getElementById(seccionId);
    if (seccion) seccion.classList.remove('d-none');
    
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    const navBtn = document.getElementById(`btn-nav-${seccionId}`);
    if (navBtn) navBtn.classList.add('active');
}

// Cargar Órdenes de Trabajo
async function cargarOrdenes() {
    try {
        const res = await fetch('/api/ordenes');
        ordenesData = await res.json();
        renderTablaOrdenes();
    } catch (err) {
        console.error('Error al cargar OTs:', err);
    }
}

function renderTablaOrdenes() {
    const tbody = document.getElementById('tabla-ordenes');
    if (!tbody) return;
    tbody.innerHTML = '';

    ordenesData.forEach(ot => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="fw-bold">#${ot.id}</td>
            <td>${ot.fecha || ''}</td>
            <td>${ot.cliente || ''}<br><small class="text-muted">${ot.telefono || ''}</small></td>
            <td>${ot.equipo || ''} ${ot.marca || ''} ${ot.modelo || ''}</td>
            <td><span class="badge bg-${getBadgeEstado(ot.estado)}">${ot.estado || 'Ingresado'}</span></td>
            <td><span class="badge bg-outline-dark border text-dark">${ot.ubicacion || 'Taller'}</span></td>
            <td class="text-center">
                <button class="btn btn-sm btn-outline-primary me-1" onclick="editarOT(${ot.id})"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-success" onclick="enviarWhatsApp(${ot.id})"><i class="bi bi-whatsapp"></i></button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Cargar Banco de Placas y Repuestos
async function cargarRepuestos() {
    try {
        const res = await fetch('/api/repuestos');
        repuestosData = await res.json();
        renderTablaRepuestos();
    } catch (err) {
        console.error('Error al cargar repuestos:', err);
    }
}

function renderTablaRepuestos() {
    const tbody = document.getElementById('tabla-repuestos');
    if (!tbody) return;
    tbody.innerHTML = '';

    repuestosData.forEach(rep => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="fw-bold">${rep.codigo || ''}</td>
            <td>${rep.descripcion || ''}</td>
            <td><span class="badge bg-secondary">${rep.chasis || 'Gral'}</span></td>
            <td>$${rep.precio_venta || 0}</td>
            <td>${rep.stock || 0} hs</td>
            <td class="text-center">
                <button class="btn btn-sm btn-outline-primary" onclick="editarRepuesto(${rep.id})"><i class="bi bi-pencil"></i></button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Cargar Ventas
async function cargarVentas() {
    try {
        const res = await fetch('/api/ventas');
        ventasData = await res.json();
    } catch (err) {
        console.error('Error al cargar ventas:', err);
    }
}

// Cargar Caja Diario
async function cargarCaja() {
    try {
        const res = await fetch('/api/caja');
        cajaData = await res.json();
        renderTablaCaja();
    } catch (err) {
        console.error('Error al cargar caja:', err);
    }
}

function renderTablaCaja() {
    const tbody = document.getElementById('tabla-caja');
    if (!tbody) return;
    tbody.innerHTML = '';

    let total = 0;
    cajaData.forEach(c => {
        total += Number(c.monto || 0);
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${c.fecha || ''}</td>
            <td>${c.concepto || ''}</td>
            <td class="${Number(c.monto) >= 0 ? 'text-success' : 'text-danger'} fw-bold">$${c.monto || 0}</td>
            <td><span class="badge bg-light text-dark border">${c.metodo || 'Efectivo'}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// Cargar Firmwares
async function cargarFirmwares() {
    try {
        const res = await fetch('/api/firmwares');
        firmwaresData = await res.json();
        renderTablaFirmwares();
    } catch (err) {
        console.error('Error al cargar firmwares:', err);
    }
}

function renderTablaFirmwares() {
    const tbody = document.getElementById('tabla-firmwares');
    if (!tbody) return;
    tbody.innerHTML = '';

    firmwaresData.forEach(f => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="fw-bold">${f.marca || ''} ${f.modelo || ''}</td>
            <td>${f.chasis_panel || ''}</td>
            <td><span class="badge bg-info text-dark">${f.tipo || 'BIN/NAND'}</span></td>
            <td>${f.peso || 'N/A'}</td>
            <td class="text-center">
                <a href="${f.url_download || '#'}" class="btn btn-sm btn-dark" target="_blank"><i class="bi bi-download"></i> Descargar</a>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Auxiliares
function getBadgeEstado(estado) {
    switch (estado) {
        case 'Ingresado': return 'secondary';
        case 'En Revisión': return 'warning text-dark';
        case 'Presupuestado': return 'info text-dark';
        case 'Aprobado': return 'primary';
        case 'Reparado': return 'success';
        case 'Entregado': return 'dark';
        default: return 'secondary';
    }
}

function enviarWhatsApp(idOT) {
    const ot = ordenesData.find(o => o.id === idOT);
    if (!ot || !ot.telefono) return alert('No hay teléfono de WhatsApp registrado para esta orden.');
    
    const num = ot.telefono.replace(/[^0-9]/g, '');
    const msg = `Hola ${ot.cliente}, te contactamos de LAB-CONTROL PRO sobre tu orden #${ot.id} (${ot.equipo} ${ot.modelo}). Estado actual: ${ot.estado}.`;
    window.open(`https://wa.me/${num}?text=${encodeURIComponent(msg)}`, '_blank');
}
