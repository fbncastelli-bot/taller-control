from flask import Flask, render_template, request, jsonify, render_template_string
import sqlite3
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

DB_NAME = "taller.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO usuarios (id, usuario, password) VALUES (1, 'admin', '1234')")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ordenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            equipo TEXT NOT NULL,
            falla TEXT NOT NULL,
            presupuesto REAL DEFAULT 0.0,
            estado TEXT DEFAULT 'Ingresado'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repuestos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT,
            nombre TEXT NOT NULL,
            ubicacion TEXT,
            cantidad INTEGER DEFAULT 0,
            precio REAL DEFAULT 0.0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS placas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            codigo TEXT NOT NULL,
            modelo_tv TEXT,
            ubicacion TEXT,
            estado TEXT DEFAULT 'Probada / OK',
            cantidad INTEGER DEFAULT 1
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS publicaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto TEXT NOT NULL,
            precio REAL DEFAULT 0.0,
            estado TEXT DEFAULT 'En Venta'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS caja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            concepto TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS firmwares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chasis TEXT NOT NULL,
            modelo TEXT NOT NULL,
            memoria TEXT,
            tamano TEXT,
            url_archivo TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE usuario = ? AND password = ?', (data.get('usuario'), data.get('password')))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "mensaje": "Credenciales inválidas"}), 401

@app.route('/api/ordenes', methods=['GET'])
def get_ordenes():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ordenes ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/ordenes', methods=['POST'])
def add_orden():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO ordenes (cliente, equipo, falla, presupuesto, estado) VALUES (?, ?, ?, ?, ?)',
                   (data.get('cliente'), data.get('equipo'), data.get('falla'), data.get('presupuesto', 0), data.get('estado', 'Ingresado')))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

# --- IMPRESIÓN DE FICHA, COMPROBANTE Y TICKET ---
@app.route('/imprimir/comprobante/<int:orden_id>')
def imprimir_comprobante(orden_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ordenes WHERE id = ?', (orden_id,))
    ord_data = cursor.fetchone()
    conn.close()
    if not ord_data:
        return "Orden no encontrada", 404

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Comprobante Cliente - OT #{ord_data['id']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; color: #000; }}
            .box {{ border: 2px solid #000; padding: 15px; border-radius: 8px; max-width: 600px; margin: auto; }}
            h2 {{ text-align: center; margin-top: 0; text-transform: uppercase; border-bottom: 1px solid #000; padding-bottom: 5px; }}
            .row {{ margin-bottom: 8px; font-size: 14px; }}
            .label {{ font-weight: bold; }}
            .footer {{ margin-top: 20px; font-size: 11px; text-align: center; border-top: 1px dashed #000; padding-top: 8px; }}
        </style>
    </head>
    <body onload="window.print()">
        <div class="box">
            <h2>Comprobante de Recepción - Servicio Técnico</h2>
            <div class="row"><span class="label">Orden N°:</span> #{ord_data['id']}</div>
            <div class="row"><span class="label">Cliente:</span> {ord_data['cliente']}</div>
            <div class="row"><span class="label">Equipo / Modelo:</span> {ord_data['equipo']}</div>
            <div class="row"><span class="label">Falla / Trabajo:</span> {ord_data['falla']}</div>
            <div class="row"><span class="label">Presupuesto Estimado:</span> ${ord_data['presupuesto']}</div>
            <div class="row"><span class="label">Estado Actual:</span> {ord_data['estado']}</div>
            <div class="footer">
                Conserve este comprobante para retirar el equipo.
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/imprimir/ticket/<int:orden_id>')
def imprimir_ticket(orden_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ordenes WHERE id = ?', (orden_id,))
    ord_data = cursor.fetchone()
    conn.close()
    if not ord_data:
        return "Orden no encontrada", 404

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ticket Tapa TV - OT #{ord_data['id']}</title>
        <style>
            body {{ font-family: monospace; padding: 10px; width: 280px; margin: auto; border: 1px solid #000; }}
            h3 {{ text-align: center; margin: 0 0 5px 0; font-size: 16px; }}
            p {{ margin: 3px 0; font-size: 12px; }}
        </style>
    </head>
    <body onload="window.print()">
        <h3>TALLER CONTROL OT #{ord_data['id']}</h3>
        <p><b>CLI:</b> {ord_data['cliente']}</p>
        <p><b>EQ:</b> {ord_data['equipo']}</p>
        <p><b>FALLA:</b> {ord_data['falla']}</p>
        <p><b>EST:</b> {ord_data['estado']}</p>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/api/clientes', methods=['GET', 'POST'])
def handle_clientes():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute('INSERT INTO clientes (nombre, telefono, direccion) VALUES (?, ?, ?)',
                       (data.get('nombre'), data.get('telefono'), data.get('direccion')))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})
    cursor.execute('SELECT * FROM clientes ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# --- GESTIÓN DE PLACAS (MAIN, POWER, T-CON, ETC.) ---
@app.route('/api/placas', methods=['GET', 'POST'])
def handle_placas():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute('INSERT INTO placas (tipo, codigo, modelo_tv, ubicacion, estado, cantidad) VALUES (?, ?, ?, ?, ?, ?)',
                       (data.get('tipo'), data.get('codigo'), data.get('modelo_tv'), data.get('ubicacion'), data.get('estado', 'Probada / OK'), data.get('cantidad', 1)))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})
    cursor.execute('SELECT * FROM placas ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/placas/<int:placa_id>/stock', methods=['PUT'])
def update_stock_placa(placa_id):
    data = request.json
    cambio = data.get('cambio', 0)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE placas SET cantidad = MAX(0, cantidad + ?) WHERE id = ?', (cambio, placa_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/placas/<int:placa_id>', methods=['DELETE'])
def delete_placa(placa_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM placas WHERE id = ?', (placa_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/repuestos', methods=['GET', 'POST'])
def handle_repuestos():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute('INSERT INTO repuestos (categoria, nombre, ubicacion, cantidad, precio) VALUES (?, ?, ?, ?, ?)',
                       (data.get('categoria'), data.get('nombre'), data.get('ubicacion'), data.get('cantidad', 1), data.get('precio', 0.0)))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})
    cursor.execute('SELECT * FROM repuestos ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/repuestos/<int:repuesto_id>/stock', methods=['PUT'])
def update_stock(repuesto_id):
    data = request.json
    cambio = data.get('cambio', 0)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE repuestos SET cantidad = MAX(0, cantidad + ?) WHERE id = ?', (cambio, repuesto_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/publicaciones', methods=['GET', 'POST'])
def handle_publicaciones():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute('INSERT INTO publicaciones (producto, precio, estado) VALUES (?, ?, ?)',
                       (data.get('producto'), data.get('precio', 0.0), data.get('estado', 'En Venta')))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})
    cursor.execute('SELECT * FROM publicaciones ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/caja', methods=['GET', 'POST'])
def handle_caja():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute('INSERT INTO caja (tipo, concepto, monto, fecha) VALUES (?, ?, ?, ?)',
                       (data.get('tipo'), data.get('concepto'), data.get('monto'), data.get('fecha')))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})
    cursor.execute('SELECT * FROM caja ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/firmwares', methods=['GET'])
def get_firmwares():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM firmwares ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
