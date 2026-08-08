document.addEventListener('DOMContentLoaded', () => {
    cargarOrdenes();
    cargarRepuestos();
    cargarPlacas();
});

async function cargarOrdenes() {
    const res = await fetch('/api/ordenes');
    const data = await res.json();
    const tbody = document.getElementById('tablaOrdenesBody');
    tbody.innerHTML = '';
    data.forEach(o => {
        tbody.innerHTML += `
            <tr class="border-b border-slate-700">
                <td class="p-3 text-blue-400 font-mono">#${o.id}</td>
                <td class="p-3">${o.cliente}</td>
                <td class="p-3">${o.equipo}</td>
                <td class="p-3">${o.falla}</td>
                <td class="p-3">$${o.presupuesto}</td>
                <td class="p-3">
                    <button onclick="analizarOT('${o.equipo}', '${o.falla}')" class="bg-purple-600 px-3 py-1 rounded text-xs">Analizar</button>
                </td>
            </tr>`;
    });
}

async function guardarOrden(e) {
    e.preventDefault();
    const data = {
        cliente: document.getElementById('ot_cliente').value,
        equipo: document.getElementById('ot_equipo').value,
        falla: document.getElementById('ot_falla').value,
        presupuesto: document.getElementById('ot_presupuesto').value
    };
    await fetch('/api/ordenes', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) });
    document.getElementById('formOrden').reset();
    cargarOrdenes();
}

async function analizarOT(equipo, falla) {
    const panel = document.getElementById('panelResultadoIA');
    const texto = document.getElementById('textoResultadoIA');
    panel.classList.remove('hidden');
    texto.innerText = "Analizando con IA...";
    
    const res = await fetch('/api/analizar-falla', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ equipo, falla })
    });
    const data = await res.json();
    texto.innerText = data.diagnostico || data.error;
}

// (Repetir estructuras similares para cargarRepuestos/Placas si es necesario)
