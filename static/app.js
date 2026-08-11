document.addEventListener('DOMContentLoaded', () => {
    cargarOrdenes();
    cargarRepuestos();
    cargarVentas();
    cargarCaja();
    cargarPlacas();
    cargarFirmwares();

    const formOT = document.getElementById('form-ot');
    if (formOT) {
        formOT.addEventListener('submit', guardarOrden);
    }
});

function comprimirImagen(file, maxWidth = 1200, quality = 0.7) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = (e) => {
            const img = new Image();
            img.src = e.target.result;
            img.onload = () => {
                let width = img.width;
                let height = img.height;

                if (width > maxWidth) {
                    height = Math.round((height * maxWidth) / width);
                    width = maxWidth;
                }

                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;

                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);

                canvas.toBlob((blob) => {
                    if (blob) {
                        resolve(blob);
                    } else {
                        reject(new Error('Error al comprimir la imagen.'));
                    }
                }, 'image/jpeg', quality);
            };
            img.onerror = (err) => reject(err);
        };
        reader.onerror = (err) => reject(err);
    });
}

async function guardarOrden(event) {
    if (event) event.preventDefault();

    const cliente = document.getElementById('ot-cliente').value.trim();
    const telefono = document.getElementById('ot-telefono').value.trim();
    const equipo = document.getElementById('ot-equipo').value.trim();
    const falla = document.getElementById('ot-falla').value.trim();
    const solucion = document.getElementById('ot-solucion').value.trim();
    const presupuesto = document.getElementById('ot-presupuesto').value.trim();
    const estado = document.getElementById('ot-estado').value;
    const fileInput = document.getElementById('ot-foto');

    if (!cliente || !equipo) {
        alert('Por favor complete al menos Cliente y Equipo.');
        return;
    }

    let urlFoto = '';

    if (fileInput && fileInput.files.length > 0) {
        try {
            const archivoOriginal = fileInput.files[0];
            const imagenComprimida = await comprimirImagen(archivoOriginal, 1200, 0.7);

            const formData = new FormData();
            formData.append('archivo', imagenComprimida, 'foto_orden.jpg');

            const uploadRes = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const uploadData = await uploadRes.json();

            if (!uploadRes.ok) {
                alert('Error al subir imagen: ' + (uploadData.error || 'Error desconocido'));
                return;
            }

            urlFoto = uploadData.url;
        } catch (err) {
            alert('Error al procesar la imagen: ' + err.message);
            return;
        }
    }

    const payload = {
        cliente: cliente,
        telefono: telefono,
        equipo: equipo,
        falla: falla,
        solucion: solucion + (urlFoto ? `\n[Foto]: ${urlFoto}` : ''),
        presupuesto: parseFloat(presupuesto) || 0,
        estado: estado
    };

    try {
        const res = await fetch('/api/ordenes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            alert('Orden guardada con éxito');
            document.getElementById('ot-cliente').value = '';
            document.getElementById('ot-telefono').value = '';
            document.getElementById('ot-equipo').value = '';
            document.getElementById('ot-falla').value = '';
            document.getElementById('ot-solucion').value = '';
            document.getElementById('ot-presupuesto').value = '';
            if (fileInput) fileInput.value = '';
            cargarOrdenes();
        } else {
            const errData = await res.json();
            alert('Error al guardar la orden: ' + (errData.error || 'Error en el servidor'));
        }
    } catch (err) {
        alert('Error de red al guardar la orden: ' + err.message);
    }
}

let cacheOrdenes = [];

async function cargarOrdenes() {
    try {
        const res = await fetch('/api/ordenes');
        const data = await res.json();
        cacheOrdenes = data;
        const tbody = document.getElementById('tabla-ordenes');
        if (!tbody) return;
        tbody.innerHTML = '';

        data.forEach(ot => {
            let solucionFormateada = (ot.solucion || '').replace(
                /\[Foto\]:\s*(https?:\/\/[^\s]+)/g,
                '<br><a href="$1" target="_blank" style="color: #0d6efd; font-weight: bold;">[Ver Foto Adjunta]</a>'
            );

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${ot.id}</td>
                <td>${ot.cliente || ''}</td>
                <td>${ot.telefono || ''}</td>
                <td>${ot.equipo || ''}</td>
                <td>${ot.falla || ''}</td>
                <td>${solucionFormateada}</td>
                <td>$${parseFloat(ot.presupuesto || 0).toFixed(2)}</td>
                <td><span class="badge bg-info text-dark">${ot.estado || 'Ingresado'}</span></td>
                <td>
                    <button class="btn btn-sm btn-primary me-1" onclick="imprimirOT(${ot.id})">Imprimir</button>
                    <button class="btn btn-sm btn-danger" onclick="eliminarOrden(${ot.id})">Borrar</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error cargando órdenes:", e);
    }
}

function imprimirOT(id) {
    const ot = cacheOrdenes.find(item => item.id === id);
    if (!ot) {
        alert('No se encontró la orden especificada.');
        return;
    }

    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=OT-${ot.id}`;

    const ventanaImpresion = window.open('', '_blank', 'width=800,height=600');
    ventanaImpresion.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Comprobante Orden de Trabajo #${ot.id}</title>

        </head>
        <body>
            <div class="comprobante">
                <div class="header">
                    <h2>COMPROBANTE DE INGRESO - ORDEN #${ot.id}</h2>
                    <p><strong>Laboratorio Técnico de Electrónica</strong></p>
                </div>
                
                <div class="datos">
                    <p><strong>Cliente:</strong> ${ot.cliente || 'N/A'}</p>
                    <p><strong>Teléfono:</strong> ${ot.telefono || 'N/A'}</p>
                    <p><strong>Equipo:</strong> ${ot.equipo || 'N/A'}</p>
                    <p><strong>Falla Reportada:</strong> ${ot.falla || 'N/A'}</p>
                    <p><strong>Presupuesto Estimado:</strong> $${parseFloat(ot.presupuesto || 0).toFixed(2)}</p>
                    <p><strong>Estado:</strong> ${ot.estado || 'Ingresado'}</p>
                </div>

                <div class="qr-container">
                    <img src="${qrUrl}" alt="Código QR Orden #${ot.id}">
                    <p><small>Escanee este código para vincular o verificar la orden #${ot.id}</small></p>
                </div>

                <div class="footer">
                    <p>Conserve este comprobante para el retiro del equipo.</p>
                </div>
            </div>
            <script>
                window.onload = function() {
                    window.print();
                };
            </script>
        </body>
        </html>
    `);
    ventanaImpresion.document.close();
}

async function eliminarOrden(id) {
    if (!confirm('¿Borrar orden #' + id + '?')) return;
    await fetch('/api/ordenes/' + id, { method: 'DELETE' });
    cargarOrdenes();
}

async function cargarRepuestos() {
    try {
        const res = await fetch('/api/repuestos');
        const data = await res.json();
        const tbody = document.getElementById('tabla-repuestos');
        if (!tbody) return;
        tbody.innerHTML = '';

        data.forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${r.categoria || ''}</td>
                <td>${r.nombre || ''}</td>
                <td>${r.ubicacion || ''}</td>
                <td>${r.cantidad}</td>
                <td>$${parseFloat(r.precio || 0).toFixed(2)}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error cargando repuestos:", e);
    }
}

async function guardarRepuesto(e) {
    if (e) e.preventDefault();
    const payload = {
        categoria: document.getElementById('rep-cat').value.trim(),
        nombre: document.getElementById('rep-nombre').value.trim(),
        ubicacion: document.getElementById('rep-ubicacion').value.trim(),
        cantidad: parseInt(document.getElementById('rep-cant').value) || 1,
        precio: parseFloat(document.getElementById('rep-precio').value) || 0
    };
    const res = await fetch('/api/repuestos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    if (res.ok) {
        document.getElementById('rep-nombre').value = '';
        document.getElementById('rep-ubicacion').value = '';
        document.getElementById('rep-cant').value = '1';
        document.getElementById('rep-precio').value = '';
        cargarRepuestos();
    }
}

async function cargarVentas() {
    try {
        const res = await fetch('/api/ventas');
        const data = await res.json();
        const tbody = document.getElementById('tabla-ventas');
        if (!tbody) return;
        tbody.innerHTML = '';

        data.forEach(v => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${v.id}</td>
                <td>${v.producto || ''}</td>
                <td>$${parseFloat(v.precio || 0).toFixed(2)}</td>
                <td><span class="badge bg-success">${v.estado || 'En Venta'}</span></td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="eliminarVenta(${v.id})">Borrar</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error cargando ventas:", e);
    }
}

async function guardarVenta(e) {
    if (e) e.preventDefault();
    const payload = {
        producto: document.getElementById('venta-producto').value.trim(),
        precio: parseFloat(document.getElementById('venta-precio').value) || 0,
        estado: document.getElementById('venta-estado').value
    };
    const res = await fetch('/api/ventas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    if (res.ok) {
        document.getElementById('venta-producto').value = '';
        document.getElementById('venta-precio').value = '';
        cargarVentas();
    }
}

async function eliminarVenta(id) {
    if (!confirm('¿Borrar venta #' + id + '?')) return;
    await fetch('/api/ventas/' + id, { method: 'DELETE' });
    cargarVentas();
}

async function cargarCaja() {
    try {
        const res = await fetch('/api/caja');
        const data = await res.json();
        
        document.getElementById('caja-ingresos').innerText = '$' + parseFloat(data.ingresos || 0).toFixed(2);
        document.getElementById('caja-egresos').innerText = '$' + parseFloat(data.egresos || 0).toFixed(2);
        document.getElementById('caja-balance').innerText = '$' + parseFloat(data.balance || 0).toFixed(2);

        const tbody = document.getElementById('tabla-caja');
        if (!tbody) return;
        tbody.innerHTML = '';

        (data.movimientos || []).forEach(m => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${m.fecha || ''}</td>
                <td><span class="badge ${m.tipo === 'Ingreso' ? 'bg-success' : 'bg-danger'}">${m.tipo}</span></td>
                <td>${m.concepto || ''}</td>
                <td>$${parseFloat(m.monto || 0).toFixed(2)}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="eliminarMovimiento(${m.id})">Borrar</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error cargando caja:", e);
    }
}

async function guardarMovimiento(e) {
    if (e) e.preventDefault();
    const payload = {
        tipo: document.getElementById('caja-tipo').value,
        concepto: document.getElementById('caja-concepto').value.trim(),
        monto: parseFloat(document.getElementById('caja-monto').value) || 0
    };
    const res = await fetch('/api/caja', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    if (res.ok) {
        document.getElementById('caja-concepto').value = '';
        document.getElementById('caja-monto').value = '';
        cargarCaja();
    }
}

async function eliminarMovimiento(id) {
    if (!confirm('¿Borrar movimiento #' + id + '?')) return;
    await fetch('/api/caja/' + id, { method: 'DELETE' });
    cargarCaja();
}

async function cargarPlacas() {
    try {
        const res = await fetch('/api/placas');
        const data = await res.json();
        const tbody = document.getElementById('tabla-placas');
        if (!tbody) return;
        tbody.innerHTML = '';

        data.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${p.tipo || ''}</td>
                <td>${p.codigo || ''}</td>
                <td>${p.modelo || ''}</td>
                <td><pre style="white-space: pre-wrap; font-size: 11px; margin: 0;">${p.test_points || ''}</pre></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error cargando placas:", e);
    }
}

async function cargarFirmwares() {
    try {
        const res = await fetch('/api/firmwares');
        const data = await res.json();
        const tbody = document.getElementById('tabla-firmwares');
        if (!tbody) return;
        tbody.innerHTML = '';

        data.forEach(f => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${f.chasis || ''}</td>
                <td>${f.modelo || ''}</td>
                <td>${f.memoria || ''}</td>
                <td><a href="${f.url_nube}" target="_blank">Descargar</a></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error cargando firmwares:", e);
    }
}

async function consultarIA(e) {
    if (e) e.preventDefault();
    const equipo = document.getElementById('ia-equipo').value.trim();
    const falla = document.getElementById('ia-falla').value.trim();
    const resDiv = document.getElementById('ia-resultado');
    
    if (!equipo || !falla) {
        alert('Complete equipo y falla');
        return;
    }

    resDiv.innerText = 'Analizando diagnóstico con Gemini...';

    try {
        const res = await fetch('/api/analizar-falla', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ equipo, falla })
        });
        const data = await res.json();
        if (res.ok) {
            resDiv.innerText = data.diagnostico;
        } else {
            resDiv.innerText = 'Error: ' + (data.error || 'No se pudo obtener respuesta');
        }
    } catch (err) {
        resDiv.innerText = 'Error de conexión: ' + err.message;
    }
}

async function buscarTestPoints(e) {
    if (e) e.preventDefault();
    const chasis = document.getElementById('tp-chasis').value.trim();
    const resDiv = document.getElementById('tp-resultado');

    if (!chasis) {
        alert('Ingrese el código de chasis');
        return;
    }

    resDiv.innerText = 'Buscando esquema de tensiones...';

    try {
        const res = await fetch('/api/obtener-test-points', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chasis })
        });
        const data = await res.json();
        if (res.ok) {
            resDiv.innerText = data.test_points;
        } else {
            resDiv.innerText = 'Error: ' + (data.error || 'No se pudo consultar');
        }
    } catch (err) {
        resDiv.innerText = 'Error de conexión: ' + err.message;
    }
}

async function analizarPDF(e) {
    if (e) e.preventDefault();
    const fileInput = document.getElementById('pdf-archivo');
    const chasis = document.getElementById('pdf-chasis').value.trim();
    const resDiv = document.getElementById('pdf-resultado');

    if (!fileInput.files.length || !chasis) {
        alert('Seleccione un archivo PDF e ingrese el chasis');
        return;
    }

    const formData = new FormData();
    formData.append('archivo', fileInput.files[0]);
    formData.append('chasis', chasis);

    resDiv.innerText = 'Procesando diagrama PDF con IA...';

    try {
        const res = await fetch('/api/analizar-esquematico-pdf', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            resDiv.innerText = data.resultado;
            cargarPlacas();
        } else {
            resDiv.innerText = 'Error: ' + (data.error || 'Fallo en la lectura');
        }
    } catch (err) {
        resDiv.innerText = 'Error de conexión: ' + err.message;
    }
}

async function calcularBacklight(e) {
    if (e) e.preventDefault();
    const driver = document.getElementById('led-driver').value.trim();
    const resDiv = document.getElementById('led-resultado');

    if (!driver) {
        alert('Ingrese el código del Driver LED');
        return;
    }

    try {
        const res = await fetch('/api/calcular-backlight', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ driver })
        });
        const data = await res.json();
        if (res.ok) {
            resDiv.innerText = `Driver: ${data.driver}\n\nProcedimiento:\n${data.procedimiento}`;
        }
    } catch (err) {
        resDiv.innerText = 'Error de conexión: ' + err.message;
    }
}
