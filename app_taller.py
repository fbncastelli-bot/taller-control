import os
import json
import io
import re
import datetime
from decimal import Decimal
from flask import (
    Flask, render_template, request, redirect, url_for, 
    flash, jsonify, make_response
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, text

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'desarrollo-clave-secreta-123')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///taller_local.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from database import db
db.init_app(app)

from models import Cliente, Orden, ItemServicio, Presupuesto, Cobro, Repuesto

NOMBRE_TALLER = "AGCelectronica"
DIRECCION_TALLER = "Alsina 4336, Claypole"
TELEFONO_TALLER = "1164992829"

@app.context_processor
def inject_taller_info():
    return dict(
        nombre_taller=NOMBRE_TALLER,
        direccion_taller=DIRECCION_TALLER,
        telefono_taller=TELEFONO_TALLER
    )

@app.after_request
def reemplazar_cabecera_html(response):
    if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
        contenido = response.get_data(as_text=True)
        
        # Reemplazo en código HTML
        patron = re.compile(r'FD\s*electr[oó]nica', re.IGNORECASE)
        contenido = patron.sub(NOMBRE_TALLER, contenido)
        
        # Inyección JavaScript para forzar cambio en el DOM del navegador
        js_override = f"""
        <script>
        document.addEventListener("DOMContentLoaded", function() {{
            document.body.innerHTML = document.body.innerHTML.replace(/FD\\s*electr[oó]nica/gi, "{NOMBRE_TALLER}");
        }});
        </script>
        </body>
        """
        if "</body>" in contenido:
            contenido = contenido.replace("</body>", js_override)
            
        response.set_data(contenido)
    return response

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
    return render_template('index.html', ordenes=ordenes, busqueda=q)

@app.route('/orden/<int:orden_id>')
def ver_orden(orden_id):
    orden = Orden.query.get_or_404(orden_id)
    return render_template('orden_detalle.html', orden=orden)

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

    qr_url = f"https://taller-control-js3z.onrender.com/orden/{orden.id}"
    qr_img = qrcode.make(qr_url)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    rl_qr = RLImage(qr_buffer, width=2.5*cm, height=2.5*cm)

    style_sub = ParagraphStyle(
        'HeaderSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#334155')
    )

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

    firma_p = Paragraph("<b>Firma del Cliente:</b> ___________________________<br/><font size='7'>Conforme recepción de equipo y condiciones generales de servicio.</font>", style_sub)
    story.append(firma_p)

    doc.build(story)
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=Orden_{orden.id:05d}_AGCelectronica.pdf'
    return response

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
