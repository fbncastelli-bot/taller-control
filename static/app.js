document.addEventListener("DOMContentLoaded", () => {
    cargarOrdenes();
    cargarRepuestos();
    cargarPlacas();
    cargarFirmwares();
});

function mostrarSeccion(sec) {
    ['ordenes', 'placas', 'backlight', 'repuestos', 'firmwares'].forEach(s => {
        document.getElementById(`sec-${s}`).style.display = (s === sec) ? 'block' : 'none';
    });
}

// ÓRDENES
function cargarOrdenes() {
    fetch('/api/ordenes')
        .then(r => r.json())
        .then(data => {
            let html = '';
            data.forEach(o => {
                html += `<tr>
                    <td>#${o.id}</td>
                    <td>${o.cliente}</td>
                    <td>${o.equipo}</td>
                    <td>${o.falla}</td>
                    <td>
                        <button onclick="analizarFalla('${o.equipo}', '${o.falla}')" class="btn btn-violeta btn-sm">🤖 Analizar Falla</button>
                    </td>
                </tr>`;
            });
            document.getElementById('tabla-ordenes').innerHTML = html;
        });
}

function analizarFalla(equipo, falla) {
    document.getElementById('box-diagnostico').innerHTML = `⏳ Consultando guía técnica para ${equipo}...`;
    fetch('/api/analizar-falla', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({equipo, falla})
    })
    .then(r => r.json())
    .then(data => {
        if(data.diagnostico) {
            document.getElementById('box-diagnostico').innerHTML = `<pre>${data.diagnostico}</pre>`;
        } else {
            document.getElementById('box-diagnostico').innerHTML = `<span class="text-danger">Error: ${data.error}</span>`;
        }
    });
}

function guardarOrden() {
    const cliente = document.getElementById('ot-cliente').value;
    const equipo = document.getElementById('ot-equipo').value;
    const falla = document.getElementById('ot-falla').value;

    fetch('/api/ordenes', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({cliente, equipo, falla})
    }).then(() => {
        document.getElementById('ot-cliente').value = '';
        document.getElementById('ot-equipo').value = '';
        document.getElementById('ot-falla').value = '';
        cargarOrdenes();
    });
}

// TEST POINTS
function buscarTestPoints() {
    const chasis = document.getElementById('input-chasis-tp').value;
    if(!chasis) return;
    document.getElementById('box-test-points').innerText = "⏳ Consultando puntos de prueba e IA...";
    
    fetch('/api/obtener-test-points', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({chasis})
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('box-test-points').innerText = data.test_points || data.error;
    });
}

// CALCULADORA BACKLIGHT
function calcularDriver() {
    const driver = document.getElementById('input-driver').value;
    if(!driver) return;
    
    fetch('/api/calcular-backlight', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({driver})
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('box-driver-resultado').innerText = `Driver: ${data.driver}\n\nProcedimiento:\n${data.procedimiento}`;
    });
}

// TABLAS AUXILIARES
function cargarRepuestos() {
    fetch('/api/repuestos').then(r => r.json()).then(data => {
        let html = '';
        data.forEach(r => { html += `<tr><td>${r.id}</td><td>${r.categoria}</td><td>${r.nombre}</td><td>${r.ubicacion}</td><td>${r.cantidad}</td></tr>`; });
        document.getElementById('tabla-repuestos').innerHTML = html;
    });
}

function cargarPlacas() {}
function cargarFirmwares() {
    fetch('/api/firmwares').then(r => r.json()).then(data => {
        let html = '';
        data.forEach(f => { html += `<tr><td>${f.chasis}</td><td>${f.modelo}</td><td>${f.memoria}</td><td><a href="${f.url_nube}" target="_blank" class="btn btn-outline-info btn-sm">Descargar</a></td></tr>`; });
        document.getElementById('tabla-firmwares').innerHTML = html;
    });
}
