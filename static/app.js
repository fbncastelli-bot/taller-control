let placaSeleccionadaId = null;
let ordenSeleccionadaId = null;
let compSeleccionadoId = null;

document.addEventListener("DOMContentLoaded", () => {
    cargarOrdenes();
    cargarPlacas();
    cargarComponentes();
    cargarPublicaciones();
    cargarCaja();
    cargarFirmwares();
});

function cambiarVista(vista) {
    const vistas = ['ordenes', 'placas', 'stock', 'ventas', 'caja', 'firmwares'];
    vistas.forEach(v => {
        const sec = document.getElementById('vista' + v.charAt(0).toUpperCase() + v.slice(1));
        const btn = document.getElementById('btnTab' + v.charAt(0).toUpperCase() + v.slice(1));
        if (sec) sec.classList.add('hidden');
        if (btn) {
            btn.classList.remove('bg-cyan-600', 'text-white', 'border-t', 'border-x', 'border-cyan-400');
            btn.classList.add('text-slate-400');
        }
    });

    const targetSec = document.getElementById('vista' + vista.charAt(0).toUpperCase() + vista.slice(1));
    const targetBtn = document.getElementById('btnTab' + vista.charAt(0).toUpperCase() + vista.slice(1));
    if (targetSec) targetSec.classList.remove('hidden');
    if (targetBtn) {
        targetBtn.classList.add('bg-cyan-600', 'text-white', 'border-t', 'border-x', 'border-cyan-400');
        targetBtn.classList.remove('text-slate-400');
    }

    if (vista === 'placas') cargarPlacas();
    if (vista === 'ordenes') cargarOrdenes();
    if (vista === 'stock') cargarComponentes();
}

function procesarLogin(e) {
    e.preventDefault();
    const u = document.getElementById('loginUsuario').value;
    const p = document.getElementById('loginPassword').value;
    fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({usuario: u, password: p})
    })
    .then(r => r.json())
    .then(d => {
        if (d.status === 'ok') {
            document.getElementById('loginOverlay').classList.add('hidden');
        } else {
            const err = document.getElementById('loginError');
            err.innerText = d.mensaje || 'Error de credenciales';
            err.classList.remove('hidden');
        }
    });
}

function cerrarSesion() {
    document.getElementById('loginOverlay').classList.remove('hidden');
}

// --- ÓRDENES DE TRABAJO ---
function cargarOrdenes() {
    fetch('/api/ordenes')
    .then(r => r.json())
    .then(data => {
        const tbody = document.getElementById('tablaOrdenesBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        data.forEach(o => {
            const tr = document.createElement('tr');
            tr.className = 'border-b border-bordercolor hover:bg-slate-800 cursor-pointer';
            tr.onclick = () => {
                document.querySelectorAll('#tablaOrdenesBody tr').forEach(r => r.classList.remove('bg-slate-700'));
                tr.classList.add('bg-slate-700');
                ordenSeleccionadaId = o.id;
            };
            tr.innerHTML = `
                <td class="py-2 px-3 font-mono text-cyan-400">#${o.id}</td>
                <td class="py-2 px-3 font-semibold">${o.cliente}</td>
                <td class="py-2 px-3">${o.equipo}</td>
                <td class="py-2 px-3">${o.falla}</td>
                <td class="py-2 px-3 text-emerald-400">$${o.presupuesto}</td>
                <td class="py-2 px-3"><span class="bg-cyan-900/50 text-cyan-300 px-2 py-0.5 rounded text-[10px]">${o.estado}</span></td>
            `;
            tbody.appendChild(tr);
        });
    });
}

function guardarOrdenDirecta(e) {
    e.preventDefault();
    const payload = {
        cliente: document.getElementById('ordCliente').value,
        equipo: document.getElementById('ordEquipo').value,
        falla: document.getElementById('ordFalla').value,
        presupuesto: parseFloat(document.getElementById('ordPresupuesto').value || 0),
        estado: document.getElementById('ordEstado').value
    };
    fetch('/api/ordenes', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(d => {
        if (d.status === 'ok') {
            document.getElementById('ordCliente').value = '';
            document.getElementById('ordEquipo').value = '';
            document.getElementById('ordFalla').value = '';
            document.getElementById('ordPresupuesto').value = '';
            cargarOrdenes();
        }
    });
}

function verFichaInforme() {
    if (!ordenSeleccionadaId) return alert('Seleccione una orden primero.');
    alert('Ficha Técnica de Orden #' + ordenSeleccionadaId);
}

function imprimirComprobanteCliente() {
    if (!ordenSeleccionadaId) return alert('Seleccione una orden primero.');
    window.open('/imprimir/comprobante/' + ordenSeleccionadaId, '_blank');
}

function imprimirTicketTapa() {
    if (!ordenSeleccionadaId) return alert('Seleccione una orden primero.');
    window.open('/imprimir/ticket/' + ordenSeleccionadaId, '_blank');
}

function filtrarOrdenes() {
    const q = document.getElementById('buscarOrdenInput').value.toLowerCase();
    document.querySelectorAll('#tablaOrdenesBody tr').forEach(r => {
        r.style.display = r.innerText.toLowerCase().includes(q) ? '' : 'none';
    });
}

// --- BANCO DE PLACAS ---
function cargarPlacas() {
    fetch('/api/placas')
    .then(r => r.json())
    .then(data => {
        const tbody = document.getElementById('tablaPlacasBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        data.forEach(p => {
            const tr = document.createElement('tr');
            tr.className = 'border-b border-bordercolor hover:bg-slate-800 cursor-pointer';
            tr.onclick = () => {
                document.querySelectorAll('#tablaPlacasBody tr').forEach(r => r.classList.remove('bg-slate-700'));
                tr.classList.add('bg-slate-700');
                placaSeleccionadaId = p.id;
            };
            tr.innerHTML = `
                <td class="py-2 px-3 font-mono text-cyan-400">#${p.id}</td>
                <td class="py-2 px-3 font-semibold text-amber-300">${p.tipo}</td>
                <td class="py-2 px-3 font-mono font-bold">${p.codigo}</td>
                <td class="py-2 px-3">${p.modelo_tv || '-'}</td>
                <td class="py-2 px-3">${p.ubicacion || '-'}</td>
                <td class="py-2 px-3"><span class="bg-emerald-900/50 text-emerald-300 px-2 py-0.5 rounded text-[10px]">${p.estado}</span></td>
                <td class="py-2 px-3 font-bold text-center">${p.cantidad}</td>
            `;
            tbody.appendChild(tr);
        });
    });
}

function guardarPlacaDirecta(e) {
    e.preventDefault();
    const payload = {
        tipo: document.getElementById('placaTipo').value,
        codigo: document.getElementById('placaCodigo').value,
        modelo_tv: document.getElementById('placaModeloTV').value,
        ubicacion: document.getElementById('placaUbicacion').value,
        estado: document.getElementById('placaEstado').value,
        cantidad: parseInt(document.getElementById('placaCantidad').value || 1)
    };
    fetch('/api/placas', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(d => {
        if (d.status === 'ok') {
            document.getElementById('placaCodigo').value = '';
            document.getElementById('placaModeloTV').value = '';
            document.getElementById('placaUbicacion').value = '';
            document.getElementById('placaCantidad').value = '1';
            cargarPlacas();
        }
    });
}

function sumarPlacaSeleccionada() {
    if (!placaSeleccionadaId) return alert('Seleccione una placa de la lista.');
    fetch(`/api/placas/${placaSeleccionadaId}/stock`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({cambio: 1})
    }).then(() => cargarPlacas());
}

function restarPlacaSeleccionada() {
    if (!placaSeleccionadaId) return alert('Seleccione una placa de la lista.');
    fetch(`/api/placas/${placaSeleccionadaId}/stock`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({cambio: -1})
    }).then(() => cargarPlacas());
}

function eliminarPlacaSeleccionada() {
    if (!placaSeleccionadaId) return alert('Seleccione una placa de la lista.');
    if (!confirm('¿Desea eliminar la placa seleccionada?')) return;
    fetch(`/api/placas/${placaSeleccionadaId}`, {
        method: 'DELETE'
    }).then(() => {
        placaSeleccionadaId = null;
        cargarPlacas();
    });
}

function imprimirEtiquetaPlaca() {
    if (!placaSeleccionadaId) return alert('Seleccione una placa de la lista.');
    alert('Etiqueta para Placa #' + placaSeleccionadaId);
}

function filtrarPlacas() {
    const q = document.getElementById('buscarPlacaInput').value.toLowerCase();
    document.querySelectorAll('#tablaPlacasBody tr').forEach(r => {
        r.style.display = r.innerText.toLowerCase().includes(q) ? '' : 'none';
    });
}

// --- STOCK COMPONENTES ---
function cargarComponentes() {
    fetch('/api/repuestos')
    .then(r => r.json())
    .then(data => {
        const tbody = document.getElementById('tablaStockBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        data.forEach(c => {
            const tr = document.createElement('tr');
            tr.className = 'border-b border-bordercolor hover:bg-slate-800 cursor-pointer';
            tr.onclick = () => {
                document.querySelectorAll('#tablaStockBody tr').forEach(r => r.classList.remove('bg-slate-700'));
                tr.classList.add('bg-slate-700');
                compSeleccionadoId = c.id;
            };
            tr.innerHTML = `
                <td class="py-2 px-3 font-mono text-cyan-400">#${c.id}</td>
                <td class="py-2 px-3">${c.categoria || '-'}</td>
                <td class="py-2 px-3 font-mono font-bold">${c.nombre}</td>
                <td class="py-2 px-3">${c.ubicacion || '-'}</td>
                <td class="py-2 px-3 font-bold text-center">${c.cantidad}</td>
            `;
            tbody.appendChild(tr);
        });
    });
}

function guardarComponenteDirecto(e) {
    e.preventDefault();
    const payload = {
        categoria: document.getElementById('compCategoria').value,
        nombre: document.getElementById('compCodigo').value,
        ubicacion: document.getElementById('compUbicacion').value,
        cantidad: parseInt(document.getElementById('compCantidad').value || 1)
    };
    fetch('/api/repuestos', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(d => {
        if (d.status === 'ok') {
            document.getElementById('compCodigo').value = '';
            document.getElementById('compUbicacion').value = '';
            document.getElementById('compCantidad').value = '1';
            cargarComponentes();
        }
    });
}

function sumarStockSeleccionado() {
    if (!compSeleccionadoId) return alert('Seleccione un componente.');
    fetch(`/api/repuestos/${compSeleccionadoId}/stock`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({cambio: 1})
    }).then(() => cargarComponentes());
}

function restarStockSeleccionado() {
    if (!compSeleccionadoId) return alert('Seleccione un componente.');
    fetch(`/api/repuestos/${compSeleccionadoId}/stock`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({cambio: -1})
    }).then(() => cargarComponentes());
}

function buscarDatasheetSeleccionado() {
    if (!compSeleccionadoId) return alert('Seleccione un componente.');
    window.open('https://www.alldatasheet.com', '_blank');
}

function imprimirEtiquetaComponente() {
    if (!compSeleccionadoId) return alert('Seleccione un componente.');
    alert('Etiqueta Componente #' + compSeleccionadoId);
}

function filtrarComponentes() {
    const q = document.getElementById('buscarCompInput').value.toLowerCase();
    document.querySelectorAll('#tablaStockBody tr').forEach(r => {
        r.style.display = r.innerText.toLowerCase().includes(q) ? '' : 'none';
    });
}

// --- VENTAS ---
function cargarPublicaciones() {
    fetch('/api/publicaciones')
    .then(r => r.json())
    .then(data => {
        const tbody = document.getElementById('tablaVentasBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        data.forEach(v => {
            const tr = document.createElement('tr');
            tr.className = 'border-b border-bordercolor hover:bg-slate-800';
            tr.innerHTML = `
                <td class="py-2 px-3 font-mono text-cyan-400">#${v.id}</td>
                <td class="py-2 px-3 font-semibold">${v.producto}</td>
                <td class="py-2 px-3 font-bold text-emerald-400">$${v.precio}</td>
            `;
            tbody.appendChild(tr);
        });
    });
}

function guardarPublicacion(e) {
    e.preventDefault();
    const payload = {
        producto: document.getElementById('ventProducto').value,
        precio: parseFloat(document.getElementById('ventPrecio').value || 0),
        estado: document.getElementById('ventEstado').value
    };
    fetch('/api/publicaciones', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(d => {
        if (d.status === 'ok') {
            document.getElementById('ventProducto').value = '';
            document.getElementById('ventPrecio').value = '';
            cargarPublicaciones();
        }
    });
}

function consultarMercadoLibre() {
    window.open('https://www.mercadolibre.com.ar', '_blank');
}

// --- CAJA ---
function cargarCaja() {
    fetch('/api/caja')
    .then(r => r.json())
    .then(data => {
        const tbody = document.getElementById('tablaCajaBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        let ing = 0, egr = 0;
        data.forEach(c => {
            if (c.tipo === 'Ingreso') ing += c.monto;
            else egr += c.monto;

            const tr = document.createElement('tr');
            tr.className = 'border-b border-bordercolor hover:bg-slate-800';
            tr.innerHTML = `
                <td class="py-2 px-3 font-mono text-cyan-400">#${c.id}</td>
                <td class="py-2 px-3 text-slate-400">${c.fecha}</td>
                <td class="py-2 px-3 font-bold ${c.tipo === 'Ingreso' ? 'text-emerald-400' : 'text-rose-400'}">${c.tipo}</td>
                <td class="py-2 px-3">${c.concepto}</td>
                <td class="py-2 px-3 font-bold">$${c.monto}</td>
            `;
            tbody.appendChild(tr);
        });
        document.getElementById('lblIngresos').innerText = '$' + ing.toFixed(2);
        document.getElementById('lblEgresos').innerText = '$' + egr.toFixed(2);
    });
}

function registrarMovimientoCaja(e) {
    e.preventDefault();
    const payload = {
        tipo: document.getElementById('cajaTipo').value,
        concepto: document.getElementById('cajaConcepto').value,
        monto: parseFloat(document.getElementById('cajaMonto').value || 0),
        fecha: new Date().toLocaleString()
    };
    fetch('/api/caja', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(d => {
        if (d.status === 'ok') {
            document.getElementById('cajaConcepto').value = '';
            document.getElementById('cajaMonto').value = '';
            cargarCaja();
        }
    });
}

// --- FIRMWARES ---
function cargarFirmwares() {
    fetch('/api/firmwares')
    .then(r => r.json())
    .then(data => {
        const tbody = document.getElementById('tablaFirmwaresBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        data.forEach(f => {
            const tr = document.createElement('tr');
            tr.className = 'border-b border-bordercolor hover:bg-slate-800';
            tr.innerHTML = `
                <td class="py-2 px-3 font-mono text-cyan-400">#${f.id}</td>
                <td class="py-2 px-3 font-mono font-bold">${f.chasis}</td>
                <td class="py-2 px-3">${f.modelo}</td>
                <td class="py-2 px-3">${f.memoria || '-'}</td>
                <td class="py-2 px-3">${f.tamano || '-'}</td>
            `;
            tbody.appendChild(tr);
        });
    });
}

function descargarFirmwareSeleccionado() {
    alert('Seleccione un firmware de la lista.');
}

function filtrarFirmwares() {
    const q = document.getElementById('buscarFirmwareInput').value.toLowerCase();
    document.querySelectorAll('#tablaFirmwaresBody tr').forEach(r => {
        r.style.display = r.innerText.toLowerCase().includes(q) ? '' : 'none';
    });
}
