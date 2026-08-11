// CÓDIGO v4.2 BASE - COPIÁ DESDE ACÁ
let ordenesData = [];
let repuestosData = [];
let ventasData = [];
let cajaData = [];
let firmwaresData = [];

document.addEventListener('DOMContentLoaded', () => {
    cargarOrdenes();
    cargarRepuestos();
    cargarVentas();
    cargarCaja();
    cargarFirmwares();
});

function mostrarSeccion(seccionId) {
    document.querySelectorAll('.seccion-contenido').forEach(el => el.classList.add('d-none'));
    document.getElementById(seccionId).classList.remove('d-none');
}

async function cargarOrdenes() {
    const res = await fetch('/api/ordenes');
    ordenesData = await res.json();
    const tbody = document.getElementById('tabla-ordenes');
    tbody.innerHTML = '';
    ordenesData.forEach(ot => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>#${ot.id}</td><td>${ot.fecha}</td><td>${ot.cliente}</td><td>${ot.equipo}</td><td>${ot.estado}</td><td>${ot.ubicacion}</td><td><button onclick="editarOT(${ot.id})">Editar</button></td>`;
        tbody.appendChild(tr);
    });
}
// FIN DEL CÓDIGO - Dale a "Commit changes"
