let otSeleccionada = null;
let repSeleccionadoId = null;
let ventaSeleccionadaId = null;
let movSeleccionadoId = null;
let dbCajaGlobal = [];

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
    const presupuesto = document.getElementById('ot-presupuesto').value;
    const estado = document.getElementById('ot-estado').value;

    if (!cliente || !equipo) {
        alert("Ingresá al menos el nombre del cliente y el equipo.");
        return;
    }

    fetch('/api/ordenes', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({cliente, telefono, equipo, falla, presupuesto, estado})
    }).then(() => {
        document.getElementById('ot-cliente').value = '';
        document.getElementById('ot-telefono').value = '';
        document.getElementById('ot-equipo').value = '';
        document.getElementById('ot-falla').value = '';
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

// IMPRESIÓN COMPROBANTE CLIENTE CON QR
function imprimirComprobanteCliente() {
    if (!otSeleccionada) return alert("Seleccioná una orden de la lista.");

    const area = document.getElementById('area-impresion');
    const fechaActual = new Date().toLocaleDateString('es-AR');
    
    const qrTexto = encodeURIComponent(`OT:${otSeleccionada.id}|Cliente:${otSeleccionada.cliente}|Equipo:${otSeleccionada.equipo}|Falla:${otSeleccionada.falla}`);
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${qrTexto}`;

    area.innerHTML = `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 2px solid #000; padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="margin: 0;">SERVICIO TÉCNICO ELECTRÓNICO</h2>
                    <p style="font-size: 14px; margin: 2px 0;">Comprobante de Recepción de Equipo</p>
                </div>
                <img src="${qrUrl}" alt="QR OT" style="width: 90px; height: 90px;">
            </div>
            <hr>
            <p><strong>N° Orden:</strong> #${otSeleccionada.id} &nbsp;&nbsp;&nbsp;&nbsp; <strong>Fecha:</strong> ${fechaActual}</p>
            <p><strong>Cliente:</strong> ${otSeleccionada.cliente} &nbsp;&nbsp;&nbsp;&nbsp; <strong>Teléfono:</strong> ${otSeleccionada.telefono || '-'}</p>
            <p><strong>Equipo / Modelo:</strong> ${otSeleccionada.equipo}</p>
            <p><strong>Falla Reportada:</strong> ${otSeleccionada.falla}</p>
            <p><strong>Estado Actual:</strong> ${otSeleccionada.estado}</p>
            <p><strong>Presupuesto Est.:</strong> $${Number(otSeleccionada.presupuesto).toLocaleString('es-AR')}</p>
            <hr>
            <p style="font-size: 11px; text-align: justify;">
                * Transcurridos los 90 días del aviso de reparación o presupuesto, los equipos no retirados serán considerados en abandono.
                * Indispensable presentar este comprobante para el retiro del equipo.
            </p>
            <br>
            <div style="display: flex; justify-content: space-between; margin-top: 20px;">
                <div style="border-top: 1px solid #000; width: 40%; text-align: center; font-size: 12px;">Firma del Cliente</div>
                <div style="border-top: 1px solid #000; width: 40%; text-align: center; font-size: 12px;">Firma Servicio Técnico</div>
            </div>
        </div>
    `;

    area.style.display = 'block';
    setTimeout(() => {
        window.print();
        area.style.display = 'none';
    }, 300);
}

// IMPRESIÓN TICKET PARA TAPA DE TV CON QR, MODELO Y CLIENTE
function imprimirTicketTapaTV() {
    if (!otSeleccionada) return alert("Seleccioná una orden de la lista.");

    const area = document.getElementById('area-impresion');
    const fechaActual = new Date().toLocaleDateString('es-AR');
    
    const qrTexto = encodeURIComponent(
        `OT:${otSeleccionada.id}|Cliente:${otSeleccionada.cliente}|Tel:${otSeleccionada.telefono || 'N/A'}|Equipo:${otSeleccionada.equipo}|Falla:${otSeleccionada.falla}|Presupuesto:${otSeleccionada.presupuesto}`
    );
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${qrTexto}`;

    area.innerHTML = `
        <div style="font-family: Arial, sans-serif; width: 240px; border: 2px solid #000; padding: 10px; text-align: center;">
            <h4 style="margin: 0; font-size: 14px; text-transform: uppercase;">CONTROL TALLER</h4>
            <h2 style="margin: 4px 0; font-size: 22px; font-weight: bold;">ORDEN #${otSeleccionada.id}</h2>
            
            <div style="margin: 8px 0;">
                <img src="${qrUrl}" alt="QR Tapa TV" style="width: 130px; height: 130px;">
            </div>

            <hr style="margin: 6px 0; border-top: 1px solid #000;">
            <p style="margin: 3px 0; font-size: 13px; text-align: left;"><strong>Cliente:</strong> ${otSeleccionada.cliente}</p>
            <p style="margin: 3px 0; font-size: 13px; text-align: left;"><strong>Modelo:</strong> ${otSeleccionada.equipo}</p>
            <p style="margin: 3px 0; font-size: 11px; text-align: left; color: #444;"><strong>Fecha:</strong> ${fechaActual}</p>
        </div>
    `;

    area.style.display = 'block';
    setTimeout(() => {
        window.print();
        area.style.display = 'none';
    }, 300);
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

// 2. STOCK COMPONENTES
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
    
    const area = document.getElementById('area-impresion');
    const qrTexto = encodeURIComponent(`COMP:${window.repNombreActual}|GAVETA:${window.repUbActual}`);
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=80x80&data=${qrTexto}`;

    area.innerHTML = `
        <div style="font-family: Arial, sans-serif; width: 180px; border: 1px solid #000; padding: 5px; font-size: 11px; text-align: center;">
            <strong>COMPONENTES TALLER</strong><br>
            <span style="font-size: 14px; font-weight: bold;">${window.repNombreActual}</span><br>
            <span>Ubicación: ${window.repUbActual}</span><br>
            <img src="${qrUrl}" alt="QR Componente" style="width: 50px; height: 50px; margin-top: 4px;">
        </div>
    `;

    area.style.display = 'block';
    setTimeout(() => {
        window.print();
        area.style.display = 'none';
    }, 300);
}

function filtrarComp() {
    const q = document.getElementById('buscar-comp').value.toLowerCase();
    document.querySelectorAll('#tabla-repuestos tr').forEach(f => {
        f.style.display = f.innerText.toLowerCase().includes(q) ? '' : 'none';
    });
}

// 3. VENTAS Y USADOS
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

// 4. BANCO DE PLACAS & REFORMA LED
function consultarReformaLED() {
    const driver = document.getElementById('input-driver-led').value;
    if (!driver) return alert("Ingresá la serigrafía del integrado driver de backlight.");

    document.getElementById('box-resultado-reforma').innerText = "⏳ Consultando pinout y procedimiento de reforma...";

    fetch('/api/calcular-backlight', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ driver })
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('box-resultado-reforma').innerText = `=== IC DRIVER: ${data.driver} ===\n${data.procedimiento}`;
    });
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

// 5. CAJA Y FINANZAS
function cargarCaja() {
    fetch('/api/caja').then(r => r.json()).then(data => {
        dbCajaGlobal = data.movimientos || [];
        renderizarTablaCaja(dbCajaGlobal);
    });
}

function renderizarTablaCaja(lista) {
    let ing = 0, egr = 0;
    let html = '';

    lista.forEach(m => {
        const monto = Number(m.monto);
        if (m.tipo === 'Ingreso') ing += monto; else egr += monto;

        const colorClass = m.tipo === 'Ingreso' ? 'text-success' : 'text-danger';
        html += `<tr onclick="seleccionarMovimientoCaja(${m.id}, this)" style="cursor: pointer;">
            <td>${m.id}</td>
            <td>${m.fecha}</td>
            <td>${m.tipo}</td>
            <td>${m.concepto}</td>
            <td class="${colorClass}">$${monto.toLocaleString('es-AR', {minimumFractionDigits: 2})}</td>
        </tr>`;
    });

    document.getElementById('caja-ingresos').innerText = `$${ing.toLocaleString('es-AR', {minimumFractionDigits: 2})}`;
    document.getElementById('caja-egresos').innerText = `$${egr.toLocaleString('es-AR', {minimumFractionDigits: 2})}`;
    document.getElementById('caja-balance').innerText = `$${(ing - egr).toLocaleString('es-AR', {minimumFractionDigits: 2})}`;
    document.getElementById('tabla-caja').innerHTML = html;
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

function seleccionarMovimientoCaja(id, fila) {
    movSeleccionadoId = id;
    document.querySelectorAll('#tabla-caja tr').forEach(r => r.classList.remove('table-active'));
    fila.classList.add('table-active');
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

function filtrarCajaTexto() {
    const q = document.getElementById('buscar-caja').value.toLowerCase();
    const filtrados = dbCajaGlobal.filter(m => 
        m.concepto.toLowerCase().includes(q) || 
        m.tipo.toLowerCase().includes(q) || 
        m.fecha.toLowerCase().includes(q)
    );
    renderizarTablaCaja(filtrados);
}

function filtrarCajaHoy() {
    const hoyStr = new Date().toISOString().split('T')[0];
    const filtrados = dbCajaGlobal.filter(m => m.fecha.startsWith(hoyStr));
    renderizarTablaCaja(filtrados);
}

function filtrarCajaMes() {
    const mesStr = new Date().toISOString().slice(0, 7);
    const filtrados = dbCajaGlobal.filter(m => m.fecha.startsWith(mesStr));
    renderizarTablaCaja(filtrados);
}

function imprimirReporteCaja() {
    const area = document.getElementById('area-impresion');
    const fechaActual = new Date().toLocaleString('es-AR');
    
    let filasHtml = '';
    let ing = 0, egr = 0;

    dbCajaGlobal.forEach(m => {
        const monto = Number(m.monto);
        if (m.tipo === 'Ingreso') ing += monto; else egr += monto;
        filasHtml += `
            <tr>
                <td style="border: 1px solid #000; padding: 4px;">${m.id}</td>
                <td style="border: 1px solid #000; padding: 4px;">${m.fecha}</td>
                <td style="border: 1px solid #000; padding: 4px;">${m.tipo}</td>
                <td style="border: 1px solid #000; padding: 4px;">${m.concepto}</td>
                <td style="border: 1px solid #000; padding: 4px; text-align: right;">$${monto.toLocaleString('es-AR', {minimumFractionDigits: 2})}</td>
            </tr>
        `;
    });

    area.innerHTML = `
        <div style="font-family: Arial, sans-serif; padding: 10px;">
            <h3 style="text-align: center; margin-bottom: 2px;">REPORTE DE CAJA Y FINANZAS - TALLER</h3>
            <p style="text-align: center; font-size: 12px; margin-top: 0;">Fecha Emisión: ${fechaActual}</p>
            <hr>
            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                <thead>
                    <tr style="background: #eee;">
                        <th style="border: 1px solid #000; padding: 4px;">N°</th>
                        <th style="border: 1px solid #000; padding: 4px;">Fecha y Hora</th>
                        <th style="border: 1px solid #000; padding: 4px;">Tipo</th>
                        <th style="border: 1px solid #000; padding: 4px;">Concepto / Detalle</th>
                        <th style="border: 1px solid #000; padding: 4px;">Monto ($)</th>
                    </tr>
                </thead>
                <tbody>${filasHtml}</tbody>
            </table>
            <br>
            <div style="font-size: 13px; text-align: right;">
                <p style="margin: 2px;">Total Ingresos: <strong>$${ing.toLocaleString('es-AR', {minimumFractionDigits: 2})}</strong></p>
                <p style="margin: 2px;">Total Egresos: <strong>$${egr.toLocaleString('es-AR', {minimumFractionDigits: 2})}</strong></p>
                <p style="margin: 2px; font-size: 15px;">Balance Neto: <strong>$${(ing - egr).toLocaleString('es-AR', {minimumFractionDigits: 2})}</strong></p>
            </div>
        </div>
    `;

    area.style.display = 'block';
    setTimeout(() => {
        window.print();
        area.style.display = 'none';
    }, 300);
}

// 6. FIRMWARES
function cargarFirmwares() {
    fetch('/api/firmwares').then(r => r.json()).then(data => {
        let html = '';
        data.forEach(f => {
            html += `<tr><td>${f.chasis}</td><td>${f.modelo}</td><td>${f.memoria}</td><td><a href="${f.url_nube}" target="_blank" class="btn btn-outline-info btn-sm">Descargar</a></td></tr>`;
        });
        document.getElementById('tabla-firmwares').innerHTML = html;
    });
}
