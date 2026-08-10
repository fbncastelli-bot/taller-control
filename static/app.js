let otSeleccionada = null;
let repSeleccionadoId = null;
let ventaSeleccionadaId = null;
let movSeleccionadoId = null;

document.addEventListener("DOMContentLoaded", () => {
    cargarOrdenes();
    cargarRepuestos();
    cargarVentas();
    cargarFirmwares();
    cargarCaja();
});

function mostrarSeccion(sec) {
    const secciones = ['ordenes', 'placas', 'repuestos', 'ventas', 'caja', 'firmwares'];
    secciones.forEach(s => {
        const el = document.getElementById(`sec-${s}`);
        if (el) el.style.display = (s === sec) ? 'block' : 'none';
    });

    const links = document.querySelectorAll('.nav-link');
    links.forEach(link => link.classList.remove('active'));
    if (window.event && window.event.currentTarget) {
        window.event.currentTarget.classList.add('active');
    }
}

function escapeQuotes(str) {
    return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// 1. ÓRDENES DE TRABAJO
function cargarOrdenes() {
    fetch('/api/ordenes').then(r => r.json()).then(data => {
        let html = '';
        data.forEach(o => {
            const jsonStr = escapeQuotes(JSON.stringify(o));
            html += `<tr onclick="seleccionarOTObj(${jsonStr}, this)" style="cursor: pointer;">
                <td>${o.id}</td>
                <td>${o.cliente}</td>
                <td>${o.telefono || '-'}</td>
                <td>${o.equipo}</td>
                <td>${o.falla}</td>
                <td>${o.solucion || '-'}</td>
                <td><span class="badge bg-info">${o.estado}</span></td>
                <td>$${Number(o.presupuesto).toLocaleString('es-AR')}</td>
            </tr>`;
        });
        document.getElementById('tabla-ordenes').innerHTML = html;
    }).catch(err => console.error("Error cargando órdenes:", err));
}

function seleccionarOTObj(obj, fila) {
    otSeleccionada = obj;
    document.querySelectorAll('#tabla-ordenes tr').forEach(r => r.classList.remove('table-active'));
    fila.classList.add('table-active');
    analizarFalla(obj.equipo, obj.falla);
}

function guardarOrden() {
    const cliente = document.getElementById('ot-cliente').value;
    const telefono = document.getElementById('ot-telefono').value;
    const equipo = document.getElementById('ot-equipo').value;
    const falla = document.getElementById('ot-falla').value;
    const solucion = document.getElementById('ot-solucion').value;
    const presupuesto = document.getElementById('ot-presupuesto').value;
    const estado = document.getElementById('ot-estado').value;

    if (!cliente || !equipo) {
        alert("Ingresá al menos el nombre del cliente y el equipo.");
        return;
    }

    fetch('/api/ordenes', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({cliente, telefono, equipo, falla, solucion, presupuesto, estado})
    }).then(() => {
        document.getElementById('ot-cliente').value = '';
        document.getElementById('ot-telefono').value = '';
        document.getElementById('ot-equipo').value = '';
        document.getElementById('ot-falla').value = '';
        document.getElementById('ot-solucion').value = '';
        document.getElementById('ot-presupuesto').value = '';
        cargarOrdenes();
    });
}

function eliminarOrdenSeleccionada() {
    if (!otSeleccionada) return alert("Seleccioná una orden de la lista.");
    if (confirm(`¿Eliminar la orden N° ${otSeleccionada.id}?`)) {
        fetch(`/api/ordenes/${otSeleccionada.id}`, { method: 'DELETE' }).then(() => {
            otSeleccionada = null;
            cerrarFicha();
            cargarOrdenes();
        });
    }
}

function filtrarTablaOT() {
    const q = document.getElementById('buscar-ot').value.toLowerCase();
    document.querySelectorAll('#tabla-ordenes tr').forEach(f => {
        f.style.display = f.innerText.toLowerCase().includes(q) ? '' : 'none';
    });
}

function verFichaOT() {
    if (!otSeleccionada) return alert("Seleccioná una orden primero.");
    const modal = document.getElementById('modal-ficha');
    const cont = document.getElementById('contenido-ficha');

    cont.innerHTML = `
        <div class="row g-2">
            <div class="col-md-6"><strong>N° ORDEN:</strong> #${otSeleccionada.id}</div>
            <div class="col-md-6"><strong>CLIENTE:</strong> ${otSeleccionada.cliente}</div>
            <div class="col-md-6"><strong>TELÉFONO:</strong> ${otSeleccionada.telefono || 'No registrado'}</div>
            <div class="col-md-6"><strong>EQUIPO:</strong> ${otSeleccionada.equipo}</div>
            <div class="col-md-6"><strong>FALLA REPORTADA:</strong> ${otSeleccionada.falla}</div>
            <div class="col-md-6"><strong>SOLUCIÓN:</strong> ${otSeleccionada.solucion || 'Pendiente'}</div>
            <div class="col-md-6"><strong>ESTADO DEL TRABAJO:</strong> ${otSeleccionada.estado}</div>
            <div class="col-md-12 text-warning fs-6"><strong>PRESUPUESTO:</strong> $${Number(otSeleccionada.presupuesto).toLocaleString('es-AR')}</div>
        </div>
    `;

    modal.style.display = 'block';
    modal.scrollIntoView({ behavior: 'smooth' });
}

function cerrarFicha() {
    document.getElementById('modal-ficha').style.display = 'none';
}

function enviarWhatsApp() {
    if (!otSeleccionada) return alert("Seleccioná una orden primero.");
    if (!otSeleccionada.telefono) return alert("Esta orden no tiene cargado un número de teléfono.");

    let num = otSeleccionada.telefono.replace(/\D/g, '');
    if (!num.startsWith('549') && num.length <= 11) {
        num = '549' + num;
    }

    const mensaje = `Hola ${otSeleccionada.cliente}, te escribimos de *SERVICIO TÉCNICO*. 
Le informamos que su equipo *${otSeleccionada.equipo}* ingresado con falla *"${otSeleccionada.falla}"* se encuentra en estado: *${otSeleccionada.estado}*.
Presupuesto: *$${Number(otSeleccionada.presupuesto).toLocaleString('es-AR')}*.
Cualquier consulta quedamos a disposición.`;

    const url = `https://wa.me/${num}?text=${encodeURIComponent(mensaje)}`;
    window.open(url, '_blank');
}

function enviarWhatsAppModal() {
    enviarWhatsApp();
}

function generarComprobanteImpresion() {
    if (!otSeleccionada) return alert("Seleccioná una orden de la lista primero.");

    document.getElementById('imp-ot-num').innerText = `OT #${otSeleccionada.id}`;
    document.getElementById('imp-fecha').innerText = `Fecha: ${new Date().toLocaleDateString('es-AR')}`;
    document.getElementById('imp-cliente').innerText = otSeleccionada.cliente;
    document.getElementById('imp-telefono').innerText = otSeleccionada.telefono || 'No registrado';
    document.getElementById('imp-equipo').innerText = otSeleccionada.equipo;
    document.getElementById('imp-falla').innerText = otSeleccionada.falla;
    document.getElementById('imp-estado').innerText = otSeleccionada.estado;
    document.getElementById('imp-presupuesto').innerText = Number(otSeleccionada.presupuesto).toLocaleString('es-AR', {minimumFractionDigits: 2});

    let numTel = (otSeleccionada.telefono || '').replace(/\D/g, '');
    let qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://wa.me/${numTel}?text=Hola,%20consulto%20por%20la%20OT%20%23${otSeleccionada.id}`;
    document.getElementById('imp-qr').src = qrUrl;

    const areaImp = document.getElementById('area-impresion');
    areaImp.style.display = 'block';
    window.print();
    areaImp.style.display = 'none';
}

function analizarFalla(equipo, falla) {
    const box = document.getElementById('box-diagnostico');
    box.innerHTML = `⏳ Analizando circuito y falla para ${equipo}...`;

    fetch('/api/analizar-falla', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({equipo, falla})
    })
    .then(r => r.json())
    .then(data => {
        box.innerHTML = `<pre>${data.diagnostico || data.error || 'Sin respuesta'}</pre>`;
    })
    .catch(err => {
        box.innerHTML = `<pre class="text-danger">Error de conexión: ${err}</pre>`;
    });
}

// 2. BANCO DE PLACAS, TEST POINTS Y BÚSQUEDA MULTIPLATAFORMA
function buscarFallasRecurrentes() {
    const chasis = document.getElementById('input-chasis-fallas').value;
    if (!chasis) return alert("Ingresá el chasis o modelo para consultar.");

    const box = document.getElementById('box-test-points');
    box.innerText = "⏳ Buscando reparaciones anteriores en tu taller y consultando fallas típicas con IA...";

    fetch('/api/fallas-recurrentes', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ chasis })
    })
    .then(r => r.json())
    .then(data => {
        box.innerText = data.resultado || data.error || 'Sin datos.';
    })
    .catch(err => {
        box.innerText = `Error de consulta: ${err}`;
    });
}

function buscarEnPlataforma(plataforma) {
    const chasis = document.getElementById('input-chasis-fallas').value || document.getElementById('input-chasis-tp').value;
    if (!chasis) return alert("Ingresá primero un chasis o modelo en la casilla superior.");

    let url = "";
    if (plataforma === 'youtube') {
        url = `https://www.youtube.com/results?search_query=${encodeURIComponent(chasis + " reparacion falla tv")}`;
    } else if (plataforma === 'telegram') {
        url = `https://t.me/s/tv_repair_dump?q=${encodeURIComponent(chasis)}`;
    } else if (plataforma === 'google') {
        url = `https://www.google.com/search?q=${encodeURIComponent(chasis + " falla resuelta diagrama firmware")}`;
    }
    window.open(url, '_blank');
}

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
    if (!chasis || fileInput.files.length === 0) return alert("Ingresá el código del chasis y seleccioná un archivo PDF.");

    const formData = new FormData();
    formData.append('chasis', chasis);
    formData.append('archivo', fileInput.files[0]);

    document.getElementById('box-test-points').innerText = "⏳ Subiendo archivo PDF y procesando plano con IA...";

    fetch('/api/analizar-esquematico-pdf', { method: 'POST', body: formData })
    .then(r => r.json()).then(data => {
        document.getElementById('box-test-points').innerText = data.resultado || data.error;
    });
}

function preguntarSobreEsquema() {
    const chasis = document.getElementById('pdf-chasis-nombre').value || document.getElementById('input-chasis-tp').value;
    const pregunta = document.getElementById('input-pregunta-esquema').value;
    const contextoActual = document.getElementById('box-test-points').innerText;
    if (!pregunta) return alert("Escribí una pregunta técnica.");

    document.getElementById('box-respuesta-esquema').innerText = "⏳ Analizando circuito para responder...";

    fetch('/api/preguntar-esquematico', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ chasis, pregunta, contexto: contextoActual })
    }).then(r => r.json()).then(data => {
        document.getElementById('box-respuesta-esquema').innerText = data.respuesta || data.error;
    });
}

// 3. STOCK COMPONENTES
function cargarRepuestos() {
    fetch('/api/repuestos').then(r => r.json()).then(data => {
        let html = '';
        data.forEach(r => {
            html += `<tr onclick="seleccionarRepuesto(${r.id}, ${r.cantidad}, '${escapeQuotes(r.ubicacion)}', '${escapeQuotes(r.nombre)}', this)" style="cursor: pointer;">
                <td>${r.id}</td>
                <td>${r.categoria}</td>
                <td>${r.nombre}</td>
                <td>${r.ubicacion}</td>
                <td><strong>${r.cantidad}</strong></td>
            </tr>`;
        });
        document.getElementById('tabla-repuestos').innerHTML = html;
    });
}

function seleccionarRepuesto(id, cant, ub, nombre, fila) {
    repSeleccionadoId = id;
    window.repCantActual = cant;
    window.repUbActual = ub;
    window.repNombreActual = nombre;
    document.querySelectorAll('#tabla-repuestos tr').forEach(r => r.classList.remove('table-active'));
    fila.classList.add('table-active');
}

function guardarRepuesto() {
    const categoria = document.getElementById('rep-cat').value;
    const nombre = document.getElementById('rep-nombre').value;
    const ubicacion = document.getElementById('rep-ubicacion').value;
    const cantidad = document.getElementById('rep-cant').value;

    fetch('/api/repuestos', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({categoria, nombre, ubicacion, cantidad})
    }).then(() => {
        document.getElementById('rep-nombre').value = '';
        document.getElementById('rep-ubicacion').value = '';
        cargarRepuestos();
    });
}

function modificarStock(delta) {
    if (!repSeleccionadoId) return alert("Seleccioná un componente.");
    const nuevaCant = Math.max(0, window.repCantActual + delta);
    fetch(`/api/repuestos/${repSeleccionadoId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({cantidad: nuevaCant})
    }).then(() => cargarRepuestos());
}

function cambiarCantidadModal() {
    if (!repSeleccionadoId) return alert("Seleccioná un componente.");
    const c = prompt("Nueva cantidad:", window.repCantActual);
    if (c !== null) {
        fetch(`/api/repuestos/${repSeleccionadoId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({cantidad: parseInt(c)})
        }).then(() => cargarRepuestos());
    }
}

function cambiarUbicacionModal() {
    if (!repSeleccionadoId) return alert("Seleccioná un componente.");
    const u = prompt("Nueva ubicación/gaveta:", window.repUbActual);
    if (u) {
        fetch(`/api/repuestos/${repSeleccionadoId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ubicacion: u})
        }).then(() => cargarRepuestos());
    }
}

function buscarDatasheet() {
    if (!window.repNombreActual) return alert("Seleccioná un componente.");
    window.open(`https://www.google.com/search?q=${window.repNombreActual}+datasheet+pdf`, '_blank');
}

function imprimirEtiqueta() {
    if (!repSeleccionadoId) return alert("Seleccioná un componente.");
    alert(`Imprimiendo etiqueta para gaveta: ${window.repNombreActual} (Ubicación: ${window.repUbActual})`);
}

function filtrarComp() {
    const q = document.getElementById('buscar-comp').value.toLowerCase();
    document.querySelectorAll('#tabla-repuestos tr').forEach(f => {
        f.style.display = f.innerText.toLowerCase().includes(q) ? '' : 'none';
    });
}

// 4. VENTAS Y USADOS
function cargarVentas() {
    fetch('/api/ventas').then(r => r.json()).then(data => {
        let html = '';
        data.forEach(v => {
            html += `<tr onclick="seleccionarVenta(${v.id}, this)" style="cursor: pointer;">
                <td>${v.id}</td>
                <td>${v.producto}</td>
                <td>$${Number(v.precio).toLocaleString('es-AR')}</td>
                <td><span class="badge bg-success">${v.estado}</span></td>
            </tr>`;
        });
        document.getElementById('tabla-ventas').innerHTML = html;
    });
}

function seleccionarVenta(id, fila) {
    ventaSeleccionadaId = id;
    document.querySelectorAll('#tabla-ventas tr').forEach(r => r.classList.remove('table-active'));
    fila.classList.add('table-active');
}

function guardarVenta() {
    const producto = document.getElementById('v-producto').value;
    const precio = document.getElementById('v-precio').value;
    const estado = document.getElementById('v-estado').value;

    fetch('/api/ventas', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({producto, precio, estado})
    }).then(() => {
        document.getElementById('v-producto').value = '';
        document.getElementById('v-precio').value = '';
        cargarVentas();
    });
}

function eliminarVentaSeleccionada() {
    if (!ventaSeleccionadaId) return alert("Seleccioná un registro.");
    fetch(`/api/ventas/${ventaSeleccionadaId}`, { method: 'DELETE' }).then(() => {
        ventaSeleccionadaId = null;
        cargarVentas();
    });
}

function consultarML() {
    const prod = document.getElementById('v-producto').value;
    if (!prod) return alert("Ingresá el nombre del producto o chasis.");
    window.open(`https://listado.mercadolibre.com.ar/${prod}`, '_blank');
}

// 5. CAJA Y FINANZAS
function cargarCaja() {
    fetch('/api/caja').then(r => r.json()).then(data => {
        document.getElementById('caja-ingresos').innerText = `$${data.ingresos.toLocaleString('es-AR', {minimumFractionDigits: 2})}`;
        document.getElementById('caja-egresos').innerText = `$${data.egresos.toLocaleString('es-AR', {minimumFractionDigits: 2})}`;
        document.getElementById('caja-balance').innerText = `$${data.balance.toLocaleString('es-AR', {minimumFractionDigits: 2})}`;

        let html = '';
        data.movimientos.forEach(m => {
            const colorClass = m.tipo === 'Ingreso' ? 'text-success' : 'text-danger';
            html += `<tr onclick="seleccionarMovimientoCaja(${m.id}, this)" style="cursor: pointer;">
                <td>${m.id}</td>
                <td>${m.fecha}</td>
                <td>${m.tipo}</td>
                <td>${m.concepto}</td>
                <td class="${colorClass}">$${Number(m.monto).toLocaleString('es-AR', {minimumFractionDigits: 2})}</td>
            </tr>`;
        });
        document.getElementById('tabla-caja').innerHTML = html;
    });
}

function seleccionarMovimientoCaja(id, fila) {
    movSeleccionadoId = id;
    document.querySelectorAll('#tabla-caja tr').forEach(r => r.classList.remove('table-active'));
    fila.classList.add('table-active');
}

function guardarMovimientoCaja() {
    const tipo = document.getElementById('caja-tipo').value;
    const concepto = document.getElementById('caja-concepto').value;
    const monto = document.getElementById('caja-monto').value;

    if (!concepto || !monto) {
        alert("Completá el concepto y el monto.");
        return;
    }

    fetch('/api/caja', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({tipo, concepto, monto})
    }).then(() => {
        document.getElementById('caja-concepto').value = '';
        document.getElementById('caja-monto').value = '';
        cargarCaja();
    });
}

function eliminarMovimientoSeleccionado() {
    if (!movSeleccionadoId) return alert("Seleccioná un movimiento de la lista.");
    if (confirm(`¿Eliminar el movimiento N° ${movSeleccionadoId}?`)) {
        fetch(`/api/caja/${movSeleccionadoId}`, { method: 'DELETE' }).then(() => {
            movSeleccionadoId = null;
            cargarCaja();
        });
    }
}

function filtrarCaja() {
    const q = document.getElementById('buscar-caja').value.toLowerCase();
    document.querySelectorAll('#tabla-caja tr').forEach(f => {
        f.style.display = f.innerText.toLowerCase().includes(q) ? '' : 'none';
    });
}

// 6. FIRMWARES Y SOLICITUDES POR WHATSAPP
function cargarFirmwares() {
    fetch('/api/firmwares').then(r => r.json()).then(data => {
        window.listaFirmwaresGlobal = data;
        renderizarTablaFirmwares(data);
    });
}

function renderizarTablaFirmwares(data) {
    let html = '';
    data.forEach(f => {
        html += `<tr>
            <td><strong>${f.chasis}</strong></td>
            <td>${f.modelo}</td>
            <td>${f.memoria}</td>
            <td><a href="${f.url_nube}" target="_blank" class="btn btn-outline-info btn-sm">Descargar Archivo</a></td>
        </tr>`;
    });
    document.getElementById('tabla-firmwares').innerHTML = html || '<tr><td colspan="4" class="text-center text-secondary">No se encontraron archivos con esa búsqueda. Usa el botón superior para pedirlo por WhatsApp.</td></tr>';
}

function filtrarFirmwares() {
    const q = document.getElementById('fw-buscar').value.toLowerCase();
    if (!window.listaFirmwaresGlobal) return;
    const filtrados = window.listaFirmwaresGlobal.filter(f => 
        f.chasis.toLowerCase().includes(q) || f.modelo.toLowerCase().includes(q) || f.memoria.toLowerCase().includes(q)
    );
    renderizarTablaFirmwares(filtrados);
}

function pedirFirmwareWhatsApp() {
    const buscado = document.getElementById('fw-buscar').value.trim();
    const textoChasis = buscado ? `*${buscado}*` : 'un equipo/chasis';
    
    // Podés reemplazar este número por el tuyo de soporte directo
    const numSoporte = "5491112345678"; 
    const msj = `Hola, necesito solicitar el firmware / dump para el chasis o modelo: ${textoChasis}. Quedo a la espera. ¡Gracias!`;
    
    window.open(`https://wa.me/${numSoporte}?text=${encodeURIComponent(msj)}`, '_blank');
}
