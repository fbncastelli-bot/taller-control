// LAB-CONTROL PRO v4.2 - Lógica de Interfaz e Impresión de Ticket Tapa TV

document.addEventListener('DOMContentLoaded', () => {
    cargarOrdenes();
});

// Cargar tabla de órdenes de trabajo
async function cargarOrdenes() {
    try {
        const res = await fetch('/api/ordenes');
        const ordenes = await res.json();
        const tbody = document.getElementById('tabla-ordenes');
        tbody.innerHTML = '';

        ordenes.forEach(ot => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="fw-bold">#${ot.id}</td>
                <td>${ot.fecha}</td>
                <td>${ot.cliente}<br><small class="text-muted">${ot.telefono}</small></td>
                <td>${ot.equipo} - ${ot.modelo}</td>
                <td><span class="badge bg-${getBadgeEstado(ot.estado)}">${ot.estado}</span></td>
                <td><span class="badge bg-outline-dark border text-dark">${ot.ubicacion || 'Taller'}</span></td>
                <td class="text-center">
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editarOT(${ot.id})" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-dark me-1" onclick="imprimirTicketTapa(${ot.id})" title="🏷️ Imprimir Ticket Tapa TV"><i class="bi bi-qr-code-scan"></i> Ticket Tapa</button>
                    <button class="btn btn-sm btn-success" onclick="enviarWhatsApp(${ot.id})" title="Enviar WhatsApp"><i class="bi bi-whatsapp"></i></button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('Error al cargar órdenes:', err);
    }
}

// Función exclusiva para generar e imprimir el Ticket QR pequeño para pegar en la tapa trasera
function imprimirTicketTapa(idOT) {
    fetch(`/api/ordenes/${idOT}`)
        .then(res => res.json())
        .then(ot => {
            document.getElementById('lbl-ot-id').innerText = ot.id;
            document.getElementById('lbl-ot-fecha').innerText = ot.fecha;
            document.getElementById('lbl-ot-cliente').innerText = ot.cliente;
            document.getElementById('lbl-ot-equipo').innerText = ot.equipo;
            document.getElementById('lbl-ot-modelo').innerText = ot.modelo;

            // Generación de URL del QR apuntando a la consulta del cliente
            const urlConsulta = `${window.location.origin}/consulta?ot=${ot.id}`;
            document.getElementById('lbl-qr-code').src = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(urlConsulta)}`;

            // Disparar ventana de impresión enfocada únicamente en el ticket
            setTimeout(() => {
                const contenidoTicket = document.getElementById('print-ticket-tapa').innerHTML;
                const ventanaImp = window.open('', '_blank', 'width=400,height=500');
                ventanaImp.document.write(`
                    <html>
                        <head>
                            <title>Ticket Tapa TV - OT #${ot.id}</title>
                            <style>
                                body { margin: 0; padding: 10px; display: flex; justify-content: center; }
                                @media print { @page { size: auto; margin: 0; } }
                            </style>
                        </head>
                        <body onload="window.print(); window.close();">
                            ${contenidoTicket}
                        </body>
                    </html>
                `);
                ventanaImp.document.close();
            }, 300);
        })
        .catch(err => alert('Error al obtener datos para la etiqueta: ' + err));
}

// Subida e integración de vista previa de foto
function previewImagen(event) {
    const reader = new FileReader();
    reader.onload = function() {
        const preview = document.getElementById('foto-preview');
        preview.src = reader.result;
        document.getElementById('preview-container').classList.remove('d-none');
        document.getElementById('ot-foto-url').value = reader.result; // Base64 / URL temporal
    };
    if (event.target.files[0]) {
        reader.readAsDataURL(event.target.files[0]);
    }
}

// Auxiliar para colores de badges
function getBadgeEstado(estado) {
    switch (estado) {
        case 'Ingresado': return 'secondary';
        case 'En Revisión': return 'warning text-dark';
        case 'Presupuestado': return 'info text-dark';
        case 'Aprobado': return 'primary';
        case 'Reparado': return 'success';
        case 'Entregado': return 'dark';
        default: return 'secondary';
    }
}

function abrirModalNuevaOT() {
    document.getElementById('form-ot').reset();
    document.getElementById('ot-id').value = '';
    document.getElementById('preview-container').classList.add('d-none');
    const modal = new bootstrap.Modal(document.getElementById('modalOT'));
    modal.show();
}
