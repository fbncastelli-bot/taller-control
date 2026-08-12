import os
import json
import io
import datetime
from decimal import Decimal
from flask import (
    Flask, render_template_string, request, redirect, url_for, 
    flash, jsonify, make_response
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

# Cargar variables de entorno / Configuración de Base de Datos
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'desarrollo-clave-secreta-123')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///taller_local.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Importar db y modelos
from database import db
db.init_app(app)

from models import Cliente, Orden, ItemServicio, Presupuesto, Cobro, Repuesto

# ---------------------------------------------------------------------------
# DATOS OFICIALES DEL TALLER
# ---------------------------------------------------------------------------
NOMBRE_TALLER = "AGCelectronica"
DIRECCION_TALLER = "Alsina 4336, Claypole"
TELEFONO_TALLER = "1164992829"

# ---------------------------------------------------------------------------
# PLANTILLA HTML INTEGRADA (FUERZA EL NOMBRE OFICIAL Y PDF QR)
# ---------------------------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ nombre_taller }} - Sistema de Gestión</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>
        body { background-color: #f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .navbar-custom { background-color: #1e293b; color: white; }
        .card-custom { border: none; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .header-info { font-size: 0.85rem; color: #cbd5e1; }
        .badge-estado { font-size: 0.85rem; padding: 0.4em 0.8em; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-custom px-4 py-3 shadow-sm">
        <div class="container-fluid">
            <a class="navbar-brand text-white fw-bold d-flex align-items-center" href="/">
                <i class="bi bi-tools me-2 fs-3 text-warning"></i>
                <div>
                    <span class="fs-4">{{ nombre_taller }}</span>
                    <div class="header-info">{{ direccion_taller }} | Tel: {{ telefono_taller }}</div>
                </div>
            </a>
            <div class="d-flex align-items-center">
                <a href="/orden/nueva" class="btn btn-warning me-2 fw-semibold btn-sm">
                    <i class="bi bi-plus-circle me-1"></i> Nueva Órden
                </a>
                <a href="/clientes" class="btn btn-outline-light btn-sm me-2">Clientes</a>
                <a href="/repuestos" class="btn btn-outline-light btn-sm">Stock Repuestos</a>
            </div>
        </div>
    </nav>

    <div class="container my-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show shadow-sm" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card card-custom p-3 bg-white">
                    <form action="/" method="GET" class="row g-2">
                        <div class="col-md-10">
                            <input type="text" name="q" class="form-control" placeholder="Buscar por cliente, N° de orden, equipo o falla..." value="{{ busqueda or '' }}">
                        </div>
                        <div class="col-md-2">
                            <button type="submit" class="btn btn-primary w-100">Buscar</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <div class="card card-custom p-4 bg-white">
            <h5 class="fw-bold mb-3 text-secondary">Órdenes de Trabajo Activas</h5>
            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>N° Orden</th>
                            <th>Ingreso</th>
                            <th>Cliente</th>
                            <th>Equipo / Modelo</th>
                            <th>Estado</th>
                            <th class="text-end">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% if ordenes %}
                            {% for orden in ordenes %}
                            <tr>
                                <td class="fw-bold">#{{ "%05d"|format(orden.id) }}</td>
                                <td>{{ orden.fecha_ingreso.strftime('%d/%m/%Y') if orden.fecha_ingreso else '-' }}</td>
                                <td>{{ orden.cliente.nombre if orden.cliente else 'Consumidor Final' }}</td>
                                <td>{{ orden.equipo_tipo }} {{ orden.equipo_marca }} {{ orden.equipo_modelo }}</td>
                                <td>
                                    <span class="badge bg-secondary badge-estado">{{ orden.estado }}</span>
                                </td>
                                <td class="text-end">
                                    <a href="/orden/{{ orden.id }}" class="btn btn-sm btn-outline-primary me-1">Ver/Editar</a>
                                    <a href="/orden/{{ orden.id }}/pdf" target="_blank" class="btn btn-sm btn-outline-danger">
                                        <i class="bi bi-file-pdf"></i> Imprimir PDF (QR)
                                    </a>
                                </td>
                            </tr>
                            {% endfor %}
                        {% else %}
                            <tr>
                                <td colspan="6" class="text-center text-muted py-4">No hay órdenes registradas actualmente.</td>
                            </tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# RUTAS DE NAVEGACIÓN Y GESTIÓN
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    query = Orden.query
    if q:
        query = query.join(Cliente, isouter=True).filter(
            or_(
                Orden.id.cast(db.String).like(f"%{q}%"),
                Orden.equipo_marca.ilike(f"%{q}%"),
                Orden.equipo_modelo.ilike(f"%{q}%"),
                Orden.falla_reportada.ilike(f"%{q}%"),
                Cliente.nombre.ilike(f"%{q}%")
            )
        )
    ordenes = query.order_by(Orden.id.desc()).all()
    
    return render_template_string(
        HTML_TEMPLATE, 
        ordenes=ordenes, 
        busqueda=q,
        nombre_taller=NOMBRE_TALLER,
        direccion_taller=DIRECCION_TALLER,
        telefono_taller=TELEFONO_TALLER
    )

# ---------------------------------------------------------------------------
# GENERACIÓN DE PDF COMPROBANTE CON QR Y CABECERA OFICIAL
# ---------------------------------------------------------------------------

@app.route('/orden/<int:orden_id>/pdf')
@app.route('/orden/<int:orden_id>/imprimir')
def generar_pdf_orden(orden_id):
    orden = Orden.query.get_or_404(orden_id)
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        import qrcode
    except ImportError:
        return "Error: Faltan librerías ReportLab o QRCode en el servidor.", 500

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    styles = getSampleStyleSheet()

    # Generar QR dinámico
    qr_url = f"https://taller-control-js3z.onrender.com/orden/{orden.id}"
    qr_img = qrcode.make(qr_url)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    rl_qr = RLImage(qr_buffer, width=2.5*cm, height=2.5*cm)

    # Estilos
    style_sub = ParagraphStyle(
        'HeaderSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#334155')
    )

    # Encabezado AGCelectronica
    info_header = Paragraph(f"""
        <font size="14" color="#1E293B"><b>{NOMBRE_TALLER}</b></font><br/>
        <b>Dirección:</b> {DIRECCION_TALLER}<br/>
        <b>Tel / WhatsApp:</b> {TELEFONO_TALLER}<br/>
        <i>Servicio Técnico Especializado en Smart TV, Audio y Consolas</i>
    """, style_sub)

    info_orden = Paragraph(f"""
        <font size="12" color="#1E293B"><b>COMPROBANTE DE INGRESO</b></font><br/>
        <font size="12" color="#DC2626"><b>ÓRDEN N° #{orden.id:05d}</b></font><br/>
        <b>Fecha:</b> {orden.fecha_ingreso.strftime('%d/%m/%Y') if orden.fecha_ingreso else '-'}<br/>
        <b>Estado:</b> {orden.estado}
    """, style_sub)

    tbl_header = Table([[info_header, info_orden, rl_qr]], colWidths=[8*cm, 6*cm, 3.5*cm])
    tbl_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
    ]))
    story.append(tbl_header)
    story.append(Spacer(1, 0.5*cm))

    # Datos Cliente y Equipo
    cliente_nom = orden.cliente.nombre if orden.cliente else "Consumidor Final"
    cliente_tel = orden.cliente.telefono if orden.cliente else "-"

    datos_tabla = [
        [Paragraph("<b>DATOS DEL CLIENTE</b>", styles['Heading4']), Paragraph("<b>DATOS DEL EQUIPO</b>", styles['Heading4'])],
        [
            Paragraph(f"<b>Cliente:</b> {cliente_nom}<br/><b>Teléfono:</b> {cliente_tel}", styles['Normal']),
            Paragraph(f"<b>Tipo:</b> {orden.equipo_tipo}<br/><b>Marca/Modelo:</b> {orden.equipo_marca} {orden.equipo_modelo}<br/><b>N° Serie:</b> {orden.numero_serie or '-'}", styles['Normal'])
        ]
    ]
    tbl_datos = Table(datos_tabla, colWidths=[8.75*cm, 8.75*cm])
    tbl_datos.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(tbl_datos)
    story.append(Spacer(1, 0.4*cm))

    # Detalles de falla
    falla_p = Paragraph(f"<b>Falla Reportada:</b> {orden.falla_reportada or 'Sin especificar'}", styles['Normal'])
    obs_p = Paragraph(f"<b>Observaciones / Accesorios:</b> {orden.observaciones or 'Sin observaciones'}", styles['Normal'])
    
    tbl_falla = Table([[falla_p], [obs_p]], colWidths=[17.5*cm])
    tbl_falla.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(tbl_falla)
    story.append(Spacer(1, 1*cm))

    # Firma
    firma_p = Paragraph("<b>Firma del Cliente:</b> ___________________________<br/><font size='7'>Conforme recepción de equipo y condiciones generales de servicio.</font>", style_sub)
    story.append(firma_p)

    doc.build(story)
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=Orden_{orden.id:05d}_AGCelectronica.pdf'
    return response

# ---------------------------------------------------------------------------
# INICIALIZACIÓN
# ---------------------------------------------------------------------------
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
