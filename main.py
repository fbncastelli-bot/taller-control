import os
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template_string, request, jsonify, send_from_directory, redirect, session
import google.generativeai as genai

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY', 'clave_secreta_taller_123')

DATABASE_URL = os.environ.get('DATABASE_URL')
IMGBB_API_KEY = os.environ.get('IMGBB_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    if not DATABASE_URL:
        return
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ordenes (
            id SERIAL PRIMARY KEY,
            cliente VARCHAR(250),
            telefono VARCHAR(100),
            equipo VARCHAR(250),
            falla TEXT,
            solucion TEXT,
            presupuesto NUMERIC(12, 2) DEFAULT 0,
            estado VARCHAR(100) DEFAULT 'Ingresado',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS repuestos (
            id SERIAL PRIMARY KEY,
            categoria VARCHAR(100),
            nombre VARCHAR(250),
            ubicacion VARCHAR(100),
            cantidad INTEGER DEFAULT 1,
            precio NUMERIC(12, 2) DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS ventas (
            id SERIAL PRIMARY KEY,
            producto VARCHAR(250),
            precio NUMERIC(12, 2) DEFAULT 0,
            estado VARCHAR(100) DEFAULT 'En Venta'
        );
        CREATE TABLE IF NOT EXISTS caja (
            id SERIAL PRIMARY KEY,
            tipo VARCHAR(50),
            concepto TEXT,
            monto NUMERIC(12, 2) DEFAULT 0,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS placas (
            id SERIAL PRIMARY KEY,
            tipo VARCHAR(100),
            codigo VARCHAR(250),
            modelo VARCHAR(250),
            test_points TEXT
        );
        CREATE TABLE IF NOT EXISTS firmwares (
            id SERIAL PRIMARY KEY,
            chasis VARCHAR(250),
            modelo VARCHAR(250),
            memoria VARCHAR(100),
            url_nube TEXT
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

try:
    init_db()
except Exception as e:
    print("Error inicializando BD:", e)

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/login')
def login_page():
    return send_from_directory('templates', 'login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/consulta')
def consulta_publica():
    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Consulta de Estado de Reparación</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
            .card { background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); width: 100%; max-width: 450px; padding: 25px; box-sizing: border-box; }
            .header { text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 15px; margin-bottom: 20px; }
            .header h2 { margin: 0; color: #333; font-size: 20px; }
            .header p { margin: 5px 0 0; color: #666; font-size: 13px; }
            .campo { margin-bottom: 12px; }
            .campo label { font-weight: bold; color: #555; font-size: 13px; display: block; }
            .campo span { font-size: 16px; color: #111; }
            .estado-badge { display: inline-block; padding: 6px 12px; border-radius: 4px; background-color: #17a2b8; color: #fff; font-weight: bold; font-size: 14px; margin-top: 4px; }
            .monto { font-size: 20px; font-weight: bold; color: #28a745; }
            .error { color: #dc3545; text-align: center; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <h2>Laboratorio Técnico de Electrónica</h2>
                <p>Consulta pública de estado de equipo</p>
            </div>
            <div id="loading" style="text-align: center;">Cargando información...</div>
            <div id="contenido" style="display: none;">
                <div class="campo"><label>Orden de Trabajo N°:</label><span id="ot-id"></span></div>
                <div class="campo"><label>Cliente:</label><span id="ot-cliente"></span></div>
                <div class="campo"><label>Equipo / Modelo:</label><span id="ot-equipo"></span></div>
                <div class="campo"><label>Falla Reportada:</label><span id="ot-falla"></span></div>
                <div class="campo"><label>Estado Actual:</label><div class="estado-badge" id="ot-estado"></div></div>
                <div class="campo" style="margin-top: 15px;"><label>Presupuesto:</label><div class="monto" id="ot-presupuesto"></div></div>
            </div>
            <div id="error-msg" class="error" style="display: none;"></div>
        </div>
        <script>
            async function consultar() {
                const urlParams = new URLSearchParams(window.location.search);
                const id = urlParams.get('id');
                if (!id) {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('error-msg').innerText = 'Número de orden no especificado.';
                    document.getElementById('error-msg').style.display = 'block';
                    return;
                }
                try {
                    const res = await fetch('/api/ordenes');
                    const data = await res.json();
                    const ot = data.find(item => item.id == id);
                    document.getElementById('loading').style.display = 'none';
                    if (ot) {
                        document.getElementById('ot-id').innerText = '#' + ot.id;
                        document.getElementById('ot-cliente').innerText = ot.cliente || 'Sin especificar';
                        document.getElementById('ot-equipo').innerText = ot.equipo || 'Sin especificar';
                        document.getElementById('ot-falla').innerText = ot.falla || 'Sin especificar';
                        document.getElementById('ot-estado').innerText = ot.estado || 'Ingresado';
                        document.getElementById('ot-presupuesto').innerText = '$' + parseFloat(ot.presupuesto || 0).toFixed(2);
                        document.getElementById('contenido').style.display = 'block';
                    } else {
                        document.getElementById('error-msg').innerText = 'No se encontró la Orden de Trabajo #' + id;
                        document.getElementById('error-msg').style.display = 'block';
                    }
                } catch (err) {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('error-msg').innerText = 'Error de conexión al obtener los datos.';
                    document.getElementById('error-msg').style.display = 'block';
                }
            }
            document.addEventListener('DOMContentLoaded', consultar);
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    file = request.files['archivo']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400
    if not IMGBB_API_KEY:
        return jsonify({'error': 'Falta configurar IMGBB_API_KEY'}), 500

    try:
        url = 'https://api.imgbb.com/1/upload'
        payload = {'key': IMGBB_API_KEY}
        files = {'image': (file.filename, file.stream, file.mimetype)}
        response = requests.post(url, data=payload, files=files)
        res_data = response.json()

        if response.status_code == 200 and res_data.get('success'):
            return jsonify({'url': res_data['data']['url']}), 200
        else:
            return jsonify({'error': res_data.get('error', {}).get('message', 'Error subiendo a ImgBB')}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ordenes', methods=['GET', 'POST'])
def handle_ordenes():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cur.execute(
            "INSERT INTO ordenes (cliente, telefono, equipo, falla, solucion, presupuesto, estado) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;",
            (data.get('cliente'), data.get('telefono'), data.get('equipo'), data.get('falla'), data.get('solucion'), data.get('presupuesto', 0), data.get('estado', 'Ingresado'))
        )
        new_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'id': new_id, 'status': 'success'}), 201
    else:
        cur.execute("SELECT * FROM ordenes ORDER BY id DESC;")
        ordenes = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(ordenes)

@app.route('/api/ordenes/<int:id_orden>', methods=['DELETE'])
def delete_orden(id_orden):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM ordenes WHERE id = %s;", (id_orden,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'deleted'})

@app.route('/api/repuestos', methods=['GET', 'POST'])
def handle_repuestos():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cur.execute(
            "INSERT INTO repuestos (categoria, nombre, ubicacion, cantidad, precio) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
            (data.get('categoria'), data.get('nombre'), data.get('ubicacion'), data.get('cantidad', 1), data.get('precio', 0))
        )
        new_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'id': new_id, 'status': 'success'}), 201
    else:
        cur.execute("SELECT * FROM repuestos ORDER BY id DESC;")
        repuestos = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(repuestos)

@app.route('/api/ventas', methods=['GET', 'POST'])
def handle_ventas():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cur.execute(
            "INSERT INTO ventas (producto, precio, estado) VALUES (%s, %s, %s) RETURNING id;",
            (data.get('producto'), data.get('precio', 0), data.get('estado', 'En Venta'))
        )
        new_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'id': new_id, 'status': 'success'}), 201
    else:
        cur.execute("SELECT * FROM ventas ORDER BY id DESC;")
        ventas = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(ventas)

@app.route('/api/ventas/<int:id_venta>', methods=['DELETE'])
def delete_venta(id_venta):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM ventas WHERE id = %s;", (id_venta,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'deleted'})

@app.route('/api/caja', methods=['GET', 'POST'])
def handle_caja():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cur.execute(
            "INSERT INTO caja (tipo, concepto, monto) VALUES (%s, %s, %s) RETURNING id;",
            (data.get('tipo'), data.get('concepto'), data.get('monto', 0))
        )
        new_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'id': new_id, 'status': 'success'}), 201
    else:
        cur.execute("SELECT * FROM caja ORDER BY id DESC;")
        movimientos = cur.fetchall()
        cur.execute("SELECT COALESCE(SUM(monto), 0) as ingresos FROM caja WHERE tipo = 'Ingreso';")
        ingresos = cur.fetchone()['ingresos']
        cur.execute("SELECT COALESCE(SUM(monto), 0) as egresos FROM caja WHERE tipo = 'Egreso';")
        egresos = cur.fetchone()['egresos']
        cur.close()
        conn.close()
        return jsonify({
            'movimientos': movimientos,
            'ingresos': float(ingresos),
            'egresos': float(egresos),
            'balance': float(ingresos - egresos)
        })

@app.route('/api/caja/<int:id_movimiento>', methods=['DELETE'])
def delete_movimiento(id_movimiento):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM caja WHERE id = %s;", (id_movimiento,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'deleted'})

@app.route('/api/placas', methods=['GET'])
def get_placas():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM placas ORDER BY id DESC;")
    placas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(placas)

@app.route('/api/firmwares', methods=['GET'])
def get_firmwares():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM firmwares ORDER BY id DESC;")
    firmwares = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(firmwares)

@app.route('/api/analizar-falla', methods=['POST'])
def analizar_falla():
    data = request.json
    equipo = data.get('equipo', '')
    falla = data.get('falla', '')

    if not GEMINI_API_KEY:
        return jsonify({'error': 'Gemini API Key no configurada'}), 500

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Analiza esta falla técnica de Smart TV o Audio:\nEquipo: {equipo}\nFalla: {falla}\nProporciona pasos de diagnóstico específicos y componentes habituales causantes."
        response = model.generate_content(prompt)
        return jsonify({'diagnostico': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/obtener-test-points', methods=['POST'])
def obtener_test_points():
    data = request.json
    chasis = data.get('chasis', '')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT test_points FROM placas WHERE codigo = %s LIMIT 1;", (chasis,))
    res = cur.fetchone()
    cur.close()
    conn.close()

    if res:
        return jsonify({'test_points': res['test_points']})
    
    if not GEMINI_API_KEY:
        return jsonify({'error': 'No se encontró en BD y Gemini no está disponible'}), 404

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Dame los Test Points y voltajes principales de la placa de TV/Audio con chasis/código: {chasis}."
        response = model.generate_content(prompt)
        return jsonify({'test_points': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
