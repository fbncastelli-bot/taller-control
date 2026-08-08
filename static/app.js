document.addEventListener('DOMContentLoaded', () => {
    cargarOrdenes();
    cargarRepuestos();
    cargarPlacas();
    cargarFirmwares();
});

// ÓRDENES DE TRABAJO
async function cargarOrdenes() {
    try {
        const res = await fetch('/api/ordenes');
        const ordenes = await res.json();
        const tbody = document.getElementById('tablaOrdenesBody');
        if (!tbody) return;
        tbody.innerHTML = '';

        ordenes.forEach(o => {
            tbody.innerHTML += `
                <tr class="hover:bg-slate-700/30 transition border-b border-slate-700/50">
                    <td class="p-4 font-mono text-blue-400">#${o.id}</td>
                    <td class="p-4 font-medium text-white">${o.cliente}</td>
                    <td class="p-4 text-slate-200">${o.equipo}</td>
                    <td class="p-4 text-slate-300">${o.falla}</td>
                    <td class="p-4 font-mono text-emerald-400">$${o.presupuesto}</td>
                    <td class="p-4 text-center">
                        <button onclick="analizarOT('${o.equipo}', '${o.falla}')" class="bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold py-1.5 px-3 rounded-lg border border-purple-400/30 transition">
                            🤖 Analizar Falla
                        </button>
                    </td>
                </tr>
            `;
        });
    } catch (e) {
        console.error('Error cargando órdenes:', e);
    }
}

async function guardarOrden(e) {
    e.preventDefault();
    const data = {
        cliente: document.getElementById('ot_cliente').value,
        equipo: document.getElementById('ot_equipo').value,
        falla: document.getElementById('ot_falla').value,
        presupuesto: document.getElementById('ot_presupuesto').value
    };

    const res = await fetch('/api/ordenes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (res.ok) {
        document.getElementById('formOrden').reset();
        cargarOrdenes();
    }
}

// STOCK COMPONENTES
async function cargarRepuestos() {
    try {
        const res = await fetch('/api/repuestos');
        const repuestos = await res.json();
        const tbody = document.getElementById('tablaRepuestosBody');
        if (!tbody) return;
        tbody.innerHTML = '';

        repuestos.forEach(r => {
            tbody.innerHTML += `
                <tr class="hover:bg-slate-700/30 transition border-b border-slate-700/50">
                    <td class="p-4 font-medium text-amber-400">${r.categoria}</td>
                    <td class="p-4 text-white font-mono">${r.nombre}</td>
                    <td class="p-4 text-slate-300">${r.ubicacion}</td>
                    <td class="p-4 font-bold text-emerald-400" id="cant-${r.id}">${r.cantidad}</td>
                    <td class="p-4 text-center">
                        <div class="inline-flex items-center gap-1">
                            <button onclick="modificarCantidad(${r.id}, -1)" class="bg-rose-600 hover:bg-rose-500 text-white font-bold w-7 h-7 rounded border border-rose-400/30 text-sm">-</button>
                            <button onclick="modificarCantidad(${r.id}, 1)" class="bg-emerald-600 hover:bg-emerald-500 text-white font-bold w-7 h-7 rounded border border-emerald-400/30 text-sm">+</button>
                        </div>
                    </td>
                    <td class="p-4 text-center">
                        <button onclick="buscarPDF('${r.nombre}')" class="bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold py-1 px-2.5 rounded border border-slate-500/30">
                            📄 PDF Datasheet
                        </button>
                    </td>
                </tr>
            `;
        });
    } catch (e) {
        console.error('Error cargando repuestos:', e);
    }
}

async function guardarRepuesto(e) {
    e.preventDefault();
    const data = {
        categoria: document.getElementById('rep_categoria').value,
        nombre: document.getElementById('rep_nombre').value,
        ubicacion: document.getElementById('rep_ubicacion').value,
        cantidad: parseInt(document.getElementById('rep_cantidad').value) || 1
    };

    const res = await fetch('/api/repuestos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (res.ok) {
        document.getElementById('formRepuesto').reset();
        cargarRepuestos();
    }
}

function modificarCantidad(id, delta) {
    const el = document.getElementById(`cant-${id}`);
    if (el) {
        let val = parseInt(el.innerText) || 0;
        val = Math.max(0, val + delta);
        el.innerText = val;
    }
}

// BANCO DE PLACAS
async function cargarPlacas() {
    try {
        const res = await fetch('/api/placas');
        const placas = await res.json();
        const tbody = document.getElementById('tablaPlacasBody');
        if (!tbody) return;
        tbody.innerHTML = '';

        placas.forEach(p => {
            tbody.innerHTML += `
                <tr class="hover:bg-slate-700/30 transition border-b border-slate-700/50">
                    <td class="p-4 font-medium text-blue-400">${p.tipo}</td>
                    <td class="p-4 text-white font-mono">${p.codigo}</td>
                    <td class="p-4 text-slate-300">${p.modelo}</td>
                    <td class="p-4 text-center">
                        <button onclick="buscarPDF('${p.codigo}')" class="bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold py-1 px-2.5 rounded border border-slate-500/30">
                            📄 Esquema PDF
                        </button>
                    </td>
                </tr>
            `;
        });
    } catch (e) {
        console.error('Error cargando placas:', e);
    }
}

async function guardarPlaca(e) {
    e.preventDefault();
    const data = {
        tipo: document.getElementById('placa_tipo').value,
        codigo: document.getElementById('placa_codigo').value,
        modelo: document.getElementById('placa_modelo').value
    };

    const res = await fetch('/api/placas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (res.ok) {
        document.getElementById('formPlaca').reset();
        cargarPlacas();
    }
}

// FIRMWARES
function cargarFirmwares() {
    const tbody = document.getElementById('tablaFirmwaresBody');
    if (!tbody) return;
    tbody.innerHTML = `
        <tr class="hover:bg-slate-700/30 transition border-b border-slate-700/50">
            <td class="p-4 text-white font-mono">MS33930.PB751</td>
            <td class="p-4 text-slate-300">Noblex 32LD870HI</td>
            <td class="p-4 font-medium text-amber-400">SPI Flash 25Q64</td>
            <td class="p-4 text-center">
                <button onclick="alert('Descargando archivo binario...')" class="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold py-1 px-3 rounded">
                    ⬇ Descargar BIN
                </button>
            </td>
        </tr>
    `;
}

// IA DIAGNÓSTICO DIRECTO
async function analizarOT(equipo, falla) {
    const panel = document.getElementById('panelResultadoIA');
    const texto = document.getElementById('textoResultadoIA');
    panel.classList.remove('hidden');
    texto.innerText = `Consultando diagnóstico técnico para ${equipo}...`;

    try {
        const res = await fetch('/api/analizar-falla', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ equipo, falla })
        });
        const data = await res.json();
        texto.innerText = data.diagnostico || data.error || "No se pudo obtener el diagnóstico.";
    } catch (e) {
        texto.innerText = "Error de conexión al procesar la falla.";
    }
}

// BUSCADOR PDF DATASHEET
function buscarPDF(query) {
    window.open(`https://www.google.com/search?q=${encodeURIComponent(query + ' datasheet pdf filetype:pdf')}`, '_blank');
}
