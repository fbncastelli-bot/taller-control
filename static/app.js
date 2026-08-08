let ordenSeleccionadaId = null;
let ordenesCache = [];

function cargarOrdenes() {
    fetch('/api/ordenes')
    .then(r => r.json())
    .then(data => {
        ordenesCache = data;
        const tbody = document.getElementById('tablaOrdenesBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        data.forEach(o => {
            const tr = document.createElement('tr');
            tr.onclick = () => {
                document.querySelectorAll('#tablaOrdenesBody tr').forEach(row => row.classList.remove('bg-blue-100'));
                tr.classList.add('bg-blue-100');
                ordenSeleccionadaId = o.id;
            };
            tr.innerHTML = `<td>#${o.id}</td><td>${o.cliente}</td><td>${o.equipo}</td><td>${o.falla}</td><td>$${o.presupuesto}</td><td>${o.estado}</td>`;
            tbody.appendChild(tr);
        });
    });
}

function analizarFallaIA() {
    if (!ordenSeleccionadaId) {
        alert('Por favor, selecciona una orden de la lista primero.');
        return;
    }
    const ord = ordenesCache.find(o => o.id === ordenSeleccionadaId);
    if (!ord) return;

    const btn = document.getElementById('btnAnalizarIA');
    if (btn) btn.innerText = '⏳ Analizando...';

    fetch('/api/ia/diagnostico', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ equipo: ord.equipo, falla: ord.falla })
    })
    .then(r => r.json())
    .then(d => {
        if (btn) btn.innerText = '🤖 Analizar Falla con IA';
        if (d.status === 'ok') {
            alert("--- DIAGNÓSTICO TÉCNICO IA ---\n\n" + d.respuesta);
        } else {
            alert('Error en diagnóstico: ' + d.mensaje);
        }
    })
    .catch(err => {
        if (btn) btn.innerText = '🤖 Analizar Falla con IA';
        alert('Error al conectar con la API.');
    });
}

document.addEventListener('DOMContentLoaded', () => {
    cargarOrdenes();
});
