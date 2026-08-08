// Cargar datos al iniciar
document.addEventListener('DOMContentLoaded', () => {
    cargarOrdenes();
    cargarRepuestos();
    cargarPlacas();
});

// ÓRDENES DE TRABAJO
async function cargarOrdenes() {
    try {
        const res = await fetch('/api/ordenes');
        const ordenes = await res.json();
        const tbody = document.getElementById('tablaOrdenesBody');
        tbody.innerHTML = '';

        ordenes.forEach(o => {
            tbody.innerHTML += `
                <tr class="hover:bg-slate-700/30 transition">
                    <td class="p-4 font-mono text-blue-400">#${o.id}</td>
                    <td class="p-4 font-medium text-white">${o.cliente}</td>
                    <td class="p-4">${o.equipo}</td>
                    <td class="p-4 text-slate-300">${o.falla}</td>
                    <td class="p-4 font-mono text-emerald-400">$${o.presupuesto}</td>
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

// REPUESTOS / STOCK
async function cargarRepuestos() {
    try {
        const res = await fetch('/api/repuestos');
        const repuestos = await res.json();
        const tbody = document.getElementById('tablaRepuestosBody');
        if (!tbody) return;
        tbody.innerHTML = '';

        repuestos.forEach(r => {
            tbody.innerHTML += `
                <tr class="hover:bg-slate-700/30 transition">
                    <td class="p-4 font-medium text-amber-400">${r.categoria}</td>
                    <td class="p-4 text-white font-mono">${r.nombre}</td>
                    <td class="p-4 text-slate-300">${r.ubicacion}</td>
                    <td class="p-4 font-bold text-emerald-400">${r.cantidad}</td>
                    <td class="p-4">--</td>
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
        cantidad: document.getElementById('rep_cantidad').value
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

// PLACAS
async function cargarPlacas() {
    try {
        const res = await fetch('/api/placas');
        const placas = await res.json();
        const tbody = document.getElementById('tablaPlacasBody');
        if (!tbody) return;
        tbody.innerHTML = '';

        placas.forEach(p => {
            tbody.innerHTML += `
                <tr class="hover:bg-slate-700/30 transition">
                    <td class="p-4 font-medium text-blue-400">${p.tipo}</td>
                    <td class="p-4 text-white font-mono">${p.codigo}</td>
                    <td class="p-4 text-slate-300">${p.modelo}</td>
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

// ANALIZADOR IA
async function analizarFallaIA() {
    const equipo = prompt("Ingrese el modelo/equipo a consultar:", "Samsung UN40J5200");
    if (!equipo) return;
    const falla = prompt("Ingrese la falla técnica:", "Sin imagen / Con audio");
    if (!falla) return;

    alert("Analizando falla con Gemini IA... Aguarde un momento.");

    try {
        const res = await fetch('/api/analizar-falla', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ equipo, falla })
        });
        const data = await res.json();

        if (data.diagnostico) {
            alert("DIAGNÓSTICO IA:\n\n" + data.diagnostico);
        } else {
            alert("Error: " + (data.error || "No se pudo obtener respuesta"));
        }
    } catch (e) {
        alert("Error de conexión al consultar IA.");
    }
}
