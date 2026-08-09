document.addEventListener("DOMContentLoaded", () => {
    cargarOrdenes();
    cargarRepuestos();
    cargarFirmwares();
    cargarCaja();
});

function mostrarSeccion(sec) {
    ['ordenes', 'repuestos', 'placas', 'backlight', 'firmwares', 'caja'].forEach(s => {
        document.getElementById(`sec-${s}`).style.display = (s === sec) ? 'block' : 'none';
    });
}

// 1. ÓRDENES DE TRABAJO
function cargarOrdenes() {
    fetch('/api/ordenes').then(r => r.json()).then(data => {
        let html = '';
        data.forEach(o => {
            html += `<tr>
                <td>#${o.id}</td>
                <td>${o.cliente}</td>
                <td>${o.equipo}</td>
                <td>${o.falla}</td>
                <td>$${o.presupuesto}</td>
                <td><span class="badge bg-info">${o.estado || 'En Taller'}</span></td>
                <td><button onclick="analizarFalla('${o.equipo}', '${o.falla}')" class="btn btn-violeta btn-sm">🤖 Analizar Falla</button></td>
            </tr>`;
        });
        document.getElementById('tabla-ordenes').innerHTML = html;
    });
}

function guardarOrden() {
    const cliente = document.getElementById('ot-cliente').value;
    const equipo = document.getElementById('ot-equipo').value;
    const falla = document.getElementById('ot-falla').value;
    const presupuesto = document.getElementById('ot-presupuesto').value;

    fetch('/api/ordenes', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({cliente, equipo, falla, presupuesto})
    }).then(() => {
        document.getElementById('ot-cliente').value = '';
        document.getElementById('ot-equipo').value = '';
        document.getElementById('ot-falla').value = '';
        document.getElementById('ot-presupuesto').value = '';
        cargarOrdenes();
    });
}

function analizarFalla(equipo, falla) {
    document.getElementById('box-diagnostico').innerHTML = `⏳ Analizando falla para ${equipo}...`;
    fetch('/api/analizar-falla', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({equipo, falla})
    }).then(r => r.json()).then(data => {
        document.getElementById('box-diagnostico').innerHTML = `<pre>${data.diagnostico || data.error}</pre>`;
    });
}

// 2. STOCK REPUESTOS & DATASHEETS
function cargarRepuestos() {
    fetch('/api/repuestos').then(r => r.json()).then(data => {
        let html = '';
        data.forEach(r => {
            html += `<tr>
                <td>${r.id}</td>
                <td><span class="badge bg-secondary">${r.categoria}</span></td>
                <td><strong>${r.nombre}</strong></td>
                <td>${r.ubicacion}</td>
                <td><span class="badge bg-primary fs-6">${r.cantidad}</span></td>
                <td>$${r.precio || 0}</td>
                <td>
                    <button onclick="modificarStock(${r.id}, 1)" class="btn btn-success btn-sm font-weight-bold">+</button>
                    <button onclick="modificarStock(${r.id}, -1)" class="btn btn-danger btn-sm font-weight-bold">-</button>
                    <button onclick="consultarDSDirecto('${r.nombre}')" class="btn btn-outline-info btn-sm">📄 Datasheet</button>
                </td>
            </tr>`;
        });
        document.getElementById('tabla-repuestos').innerHTML = html;
    });
}

function modificarStock(id, delta) {
    fetch(`/api/repuestos/${id}/stock`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({delta})
    }).then(() => cargarRepuestos());
}

function guardarRepuesto() {
    const categoria = document.getElementById('rep-cat').value;
    const nombre = document.getElementById('rep-nombre').value;
    const ubicacion = document.getElementById('rep-ubicacion').value;
    const cantidad = document.getElementById('rep-cant').value;
    const precio = document.getElementById('rep-precio').value;

    fetch('/api/repuestos', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({categoria, nombre, ubicacion, cantidad, precio})
    }).then(() => {
        document.getElementById('rep-cat').value = '';
        document.getElementById('rep-nombre').value = '';
        document.getElementById('rep-ubicacion').value = '';
        document.getElementById('rep-cant').value = '';
        document.getElementById('rep-precio').value = '';
        cargarRepuestos();
    });
}

function buscarDatasheet() {
    const comp = document.getElementById('input-ds-componente').value;
    if(!comp) return;
    consultarDSDirecto(comp);
}

function consultarDSDirecto(comp) {
    mostrarSeccion('repuestos');
    document.getElementById('input-ds-componente').value = comp;
    document.getElementById('box-datasheet-resultado').innerText = `⏳ Buscando Datasheet y reemplazos para ${comp}...`;
    fetch('/api/consultar-datasheet', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({componente: comp})
    }).then(r => r.json()).then(data => {
        document.getElementById('box-datasheet-resultado').innerText = data.datasheet || data.error;
    });
}

// 3. TEST POINTS & ESQUEMÁTICOS
function buscarTestPoints() {
    const chasis = document.getElementById('input-chasis-tp').value;
    if(!chasis) return;
    document.getElementById('box-test-points').innerText = "⏳ Consultando puntos de prueba...";
    fetch('/api/obtener-test-points', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({chasis})
    }).then(r => r.json()).then(data => {
        document.getElementById('box-test-points').innerText = data.test_points || data.error;
    });
}

function procesarEsquematicoTexto() {
    const chasis = document.getElementById('pdf-chasis-nombre').value;
    const texto_esquema = document.getElementById('pdf-texto-esquema').value;
    if(!chasis || !texto_esquema) return alert("Completá chasis y texto del esquema");

    document.getElementById('box-test-points').innerText = "⏳ Procesando esquema...";
    fetch('/api/analizar-esquematico', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({chasis, texto_esquema})
    }).then(r => r.json()).then(data => {
        document.getElementById('box-test-points').innerText = data.resultado || data.error;
    });
}

// 4. CALCULADORA BACKLIGHT
function calcularDriver() {
    const driver = document.getElementById('input-driver').value;
    if(!driver) return;
    fetch('/api/calcular-backlight', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({driver})
    }).then(r => r.json()).then(data => {
        document.getElementById('box-driver-resultado').innerText = `Driver: ${data.driver}\n\nProcedimiento:\n${data.procedimiento}`;
    });
}

// 5. FIRMWARES
function cargarFirmwares() {
    fetch('/api/firmwares').then(r => r.json()).then(data => {
        let html = '';
        data.forEach(f => {
            html += `<tr><td>${f.chasis}</td><td>${f.modelo}</td><td>${f.memoria}</td><td><a href="${f.url_nube}" target="_blank" class="btn btn-outline-info btn-sm">Descargar</a></td></tr>`;
        });
        document.getElementById('tabla-firmwares').innerHTML = html;
    });
}

function guardarFirmware() {
    const chasis = document.getElementById('fw-chasis').value;
    const modelo = document.getElementById('fw-modelo').value;
    const memoria = document.getElementById('fw-memoria').value;
    const url_nube = document.getElementById('fw-url').value;

    fetch('/api/firmwares', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({chasis, modelo, memoria, url_nube})
    }).then(() => {
        document.getElementById('fw-chasis').value = '';
        document.getElementById('fw-modelo').value = '';
        document.getElementById('fw-memoria').value = '';
        document.getElementById('fw-url').value = '';
        cargarFirmwares();
    });
}

// 6. CAJA & BALANCES
function cargarCaja() {
    fetch('/api/caja').then(r => r.json()).then(data => {
        document.getElementById('caja-ingresos').innerText = `$${data.ingresos}`;
        document.getElementById('caja-egresos').innerText = `$${data.egresos}`;
        document.getElementById('caja-balance').innerText = `$${data.balance}`;

        let html = '';
        data.movimientos.forEach(m => {
            const color = m.tipo === 'Ingreso' ? 'text-success' : 'text-danger';
            html += `<tr><td>${m.fecha}</td><td><span class="badge ${m.tipo === 'Ingreso' ? 'bg-success' : 'bg-danger'}">${m.tipo}</span></td><td>${m.concepto}</td><td class="${color}">$${m.monto}</td></tr>`;
        });
        document.getElementById('tabla-caja').innerHTML = html;
    });
}

function guardarMovimientoCaja() {
    const tipo = document.getElementById('caja-tipo').value;
    const concepto = document.getElementById('caja-concepto').value;
    const monto = document.getElementById('caja-monto').value;

    fetch('/api/caja', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({tipo, concepto, monto, fecha: new Date().toISOString().split('T')[0]})
    }).then(() => {
        document.getElementById('caja-concepto').value = '';
        document.getElementById('caja-monto').value = '';
        cargarCaja();
    });
}
