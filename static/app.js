document.addEventListener("DOMContentLoaded", () => {
    cargarOrdenes();
    cargarRepuestos();
    cargarFirmwares();
    cargarCaja();
});

function mostrarSeccion(sec) {
    const secciones = ['ordenes', 'repuestos', 'placas', 'backlight', 'firmwares', 'caja'];
    secciones.forEach(s => {
        const el = document.getElementById(`sec-${s}`);
        if (el) {
            el.style.display = (s === sec) ? 'block' : 'none';
        }
    });

    // Actualizar clase activa en el menú lateral
    const links = document.querySelectorAll('.nav-link');
    links.forEach(link => link.classList.remove('active'));
    
    // Activar la pestaña según el evento
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    }
}

// 1. ÓRDENES DE TRABAJO
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
                    <td>$${o.presupuesto}</td>
                    <td><span class="badge bg-info">${o.estado || 'En Taller'}</span></td>
                    <td><button onclick="analizarFalla('${o.equipo}', '${o.falla}')" class="btn btn-violeta btn-sm">🤖 Analizar Falla</button></td>
                </tr>`;
            });
            const tabla = document.getElementById('tabla-ordenes');
            if (tabla) tabla.innerHTML = html;
        })
        .catch(err => console.error("Error al cargar ordenes:", err));
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

// 2. STOCK REPUESTOS
function cargarRepuestos() {
    fetch('/api/repuestos')
        .then(r => r.json())
        .then(data => {
            let html = '';
            data.forEach(r => {
                html += `<tr><td>${r.id}</td><td>${r.categoria}</td><td>${r.nombre}</td><td>${r.ubicacion}</td><td>${r.cantidad}</td><td>$${r.precio || 0}</td></tr>`;
            });
            const tabla = document.getElementById('tabla-repuestos');
            if (tabla) tabla.innerHTML = html;
        })
        .catch(err => console.error("Error al cargar repuestos:", err));
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

// 3. TEST POINTS & SUBIR ESQUEMÁTICO PDF
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

function procesarEsquematicoPDF() {
    const chasis = document.getElementById('pdf-chasis-nombre').value;
    const fileInput = document.getElementById('pdf-archivo');
    
    if (!chasis || fileInput.files.length === 0) {
        alert("Ingresá el código del chasis y seleccioná un archivo PDF.");
        return;
    }

    const formData = new FormData();
    formData.append('chasis', chasis);
    formData.append('archivo', fileInput.files[0]);

    document.getElementById('box-test-points').innerText = "⏳ Subiendo archivo PDF y procesando plano con IA...";

    fetch('/api/analizar-esquematico-pdf', {
        method: 'POST',
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('box-test-points').innerText = data.resultado || data.error;
    })
    .catch(err => {
        document.getElementById('box-test-points').innerText = "Error al procesar el archivo PDF: " + err;
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
    fetch('/api/firmwares')
        .then(r => r.json())
        .then(data => {
            let html = '';
            data.forEach(f => {
                html += `<tr><td>${f.chasis}</td><td>${f.modelo}</td><td>${f.memoria}</td><td><a href="${f.url_nube}" target="_blank" class="btn btn-outline-info btn-sm">Descargar</a></td></tr>`;
            });
            const tabla = document.getElementById('tabla-firmwares');
            if (tabla) tabla.innerHTML = html;
        })
        .catch(err => console.error("Error al cargar firmwares:", err));
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
    fetch('/api/caja')
        .then(r => r.json())
        .then(data => {
            const ing = document.getElementById('caja-ingresos');
            const egr = document.getElementById('caja-egresos');
            const bal = document.getElementById('caja-balance');
            
            if (ing) ing.innerText = `$${data.ingresos}`;
            if (egr) egr.innerText = `$${data.egresos}`;
            if (bal) bal.innerText = `$${data.balance}`;

            let html = '';
            data.movimientos.forEach(m => {
                const color = m.tipo === 'Ingreso' ? 'text-success' : 'text-danger';
                html += `<tr><td>${m.fecha}</td><td><span class="badge ${m.tipo === 'Ingreso' ? 'bg-success' : 'bg-danger'}">${m.tipo}</span></td><td>${m.concepto}</td><td class="${color}">$${m.monto}</td></tr>`;
            });
            const tabla = document.getElementById('tabla-caja');
            if (tabla) tabla.innerHTML = html;
        })
        .catch(err => console.error("Error al cargar caja:", err));
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
