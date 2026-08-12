document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    cargarOrdenes();
    cargarPlacas();
    cargarFirmwares();
    cargarRepuestos();
    cargarVentas();
    cargarCaja();
}

window.cambiarPestana = function(pestanaId) {
    const pestañas = document.querySelectorAll('.tab-content');
    pestañas.forEach(p => p.style.display = 'none');
    
    const activa = document.getElementById(pestanaId);
    if (activa) {
        activa.style.display = 'block';
    }

    const botones = document.querySelectorAll('.tab-button');
    botones.forEach(b => b.classList.remove('active'));
    
    const botonActivo = document.querySelector(`[onclick="cambiarPestana('${pestanaId}')"]`);
    if (botonActivo) {
        botonActivo.classList.add('active');
    }
};

window.cerrarSesion = function() {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = '/logout';
};

window.exportarOrdenesExcel = function() {
    window.location.href = '/api/exportar-ordenes';
};

async function cargarOrdenes() {
    try {
        const res = await fetch('/api/ordenes');
        if (res.ok) {
            const data = await res.json();
            renderizarTablaOrdenes(data);
        }
    } catch (e) {
        console.error("Error cargando órdenes:", e);
    }
}

async function cargarPlacas() {
    try {
        const res = await fetch('/api/placas');
        if (res.ok) {
            const data = await res.json();
            renderizarTablaPlacas(data);
        }
    } catch (e) {
        console.error("Error cargando placas:", e);
    }
}

async function cargarFirmwares() {
    try {
        const res = await fetch('/api/firmwares');
        if (res.ok) {
            const data = await res.json();
            renderizarTablaFirmwares(data);
        }
    } catch (e) {
        console.error("Error cargando firmwares:", e);
    }
}

async function cargarRepuestos() {
    try {
        const res = await fetch('/api/repuestos');
        if (res.ok) {
            const data = await res.json();
            renderizarTablaRepuestos(data);
        }
    } catch (e) {
        console.error("Error cargando repuestos:", e);
    }
}

async function cargarVentas() {
    try {
        const res = await fetch('/api/ventas');
        if (res.ok) {
            const data = await res.json();
            renderizarTablaVentas(data);
        }
    } catch (e) {
        console.error("Error cargando ventas:", e);
    }
}

async function cargarCaja() {
    try {
        const res = await fetch('/api/caja');
        if (res.ok) {
            const data = await res.json();
            renderizarCaja(data);
        }
    } catch (e) {
        console.error("Error cargando caja:", e);
    }
}

function renderizarTablaOrdenes(datos) {
    const contenedor = document.getElementById('tabla-ordenes');
    if (!contenedor) return;
    contenedor.innerHTML = datos.map(o => `
        <tr>
            <td>${o.id}</td>
            <td>${o.cliente}</td>
            <td>${o.equipo}</td>
            <td>${o.falla}</td>
            <td>$${o.presupuesto}</td>
            <td>${o.estado}</td>
        </tr>
    `).join('');
}

function renderizarTablaPlacas(datos) {
    const contenedor = document.getElementById('tabla-placas');
    if (!contenedor) return;
    contenedor.innerHTML = datos.map(p => `
        <tr>
            <td>${p.tipo}</td>
            <td>${p.codigo}</td>
            <td>${p.modelo}</td>
            <td>${p.test_points}</td>
        </tr>
    `).join('');
}

function renderizarTablaFirmwares(datos) {
    const contenedor = document.getElementById('tabla-firmwares');
    if (!contenedor) return;
    contenedor.innerHTML = datos.map(f => `
        <tr>
            <td>${f.chasis}</td>
            <td>${f.modelo}</td>
            <td>${f.memoria}</td>
            <td><a href="${f.url_nube}" target="_blank">Descargar</a></td>
        </tr>
    `).join('');
}

function renderizarTablaRepuestos(datos) {
    const contenedor = document.getElementById('tabla-repuestos');
    if (!contenedor) return;
    contenedor.innerHTML = datos.map(r => `
        <tr>
            <td>${r.categoria}</td>
            <td>${r.nombre}</td>
            <td>${r.ubicacion}</td>
            <td>${r.cantidad}</td>
            <td>$${r.precio}</td>
        </tr>
    `).join('');
}

function renderizarTablaVentas(datos) {
    const contenedor = document.getElementById('tabla-ventas');
    if (!contenedor) return;
    contenedor.innerHTML = datos.map(v => `
        <tr>
            <td>${v.id}</td>
            <td>${v.producto}</td>
            <td>$${v.precio}</td>
            <td>${v.estado}</td>
        </tr>
    `).join('');
}

function renderizarCaja(datos) {
    const contenedor = document.getElementById('tabla-caja');
    if (contenedor && datos.movimientos) {
        contenedor.innerHTML = datos.movimientos.map(c => `
            <tr>
                <td>${c.fecha}</td>
                <td>${c.tipo}</td>
                <td>${c.concepto}</td>
                <td>$${c.monto}</td>
            </tr>
        `).join('');
    }
    
    const elemIngresos = document.getElementById('caja-ingresos');
    const elemEgresos = document.getElementById('caja-egresos');
    const elemBalance = document.getElementById('caja-balance');

    if (elemIngresos) elemIngresos.innerText = `$${datos.ingresos || 0}`;
    if (elemEgresos) elemEgresos.innerText = `$${datos.egresos || 0}`;
    if (elemBalance) elemBalance.innerText = `$${datos.balance || 0}`;
}

window.analizarFalla = async function() {
    const equipo = document.getElementById('diag-equipo')?.value;
    const falla = document.getElementById('diag-falla')?.value;
    const resultadoDiv = document.getElementById('diag-resultado');

    try {
        const res = await fetch('/api/analizar-falla', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ equipo, falla })
        });
        const data = await res.json();
        if (resultadoDiv) resultadoDiv.innerText = data.diagnostico;
    } catch (e) {
        console.error("Error analizando falla:", e);
    }
};

window.calcularBacklight = async function() {
    const driver = document.getElementById('driver-led')?.value;
    const resultadoDiv = document.getElementById('backlight-resultado');

    try {
        const res = await fetch('/api/calcular-backlight', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ driver })
        });
        const data = await res.json();
        if (resultadoDiv) resultadoDiv.innerText = `${data.driver}: ${data.procedimiento}`;
    } catch (e) {
        console.error("Error calculando backlight:", e);
    }
};
