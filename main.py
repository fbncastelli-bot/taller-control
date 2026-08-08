import os
import sqlite3
import psycopg2
from flask import Flask, render_template, request, jsonify, render_template_string

app = Flask(__name__, template_folder='templates', static_folder='static')

DATABASE_URL = os.environ.get('DATABASE_URL')

def is_postgres():
    return bool(DATABASE_URL)

def get_db():
    if is_postgres():
        url = DATABASE_URL.replace("postgres://", "postgresql://")
        return psycopg2.connect(url)
    else:
        conn = sqlite3.connect("taller.db")
        conn.row_factory = sqlite3.Row
        return conn

def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_db()
    cursor = conn.cursor()
    
    formatted_query = query.replace('?', '%s') if is_postgres() else query
    cursor.execute(formatted_query, params)
    
    result = None
    if fetchone:
        row = cursor.fetchone()
        if row:
            if is_postgres():
                colnames = [desc[0] for desc in cursor.description]
                result = dict(zip(colnames, row))
            else:
                result = dict(row)
    elif fetchall:
        rows = cursor.fetchall()
        if is_postgres():
            colnames = [desc[0] for desc in cursor.description]
            result = [dict(zip(colnames, r)) for r in rows]
        else:
            result = [dict(r) for r in rows]
            
    if commit:
        conn.commit()
        
    cursor.close()
    conn.close()
    return result

def init_db():
    pk = "SERIAL PRIMARY KEY" if is_postgres() else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    queries = [
        f'''CREATE TABLE IF NOT EXISTS usuarios (
            id {pk}, usuario TEXT UNIQUE NOT NULL, password TEXT NOT NULL
        );''',
        f'''CREATE TABLE IF NOT EXISTS ordenes (
            id {pk}, cliente TEXT NOT NULL, equipo TEXT NOT NULL, falla TEXT NOT NULL,
            presupuesto REAL DEFAULT 0.0, estado TEXT DEFAULT 'Ingresado'
        );''',
        f'''CREATE TABLE IF NOT EXISTS clientes (
            id {pk}, nombre TEXT NOT NULL, telefono TEXT, direccion TEXT
        );''',
        f'''CREATE TABLE IF NOT EXISTS repuestos (
            id {pk}, categoria TEXT, nombre TEXT NOT NULL, ubicacion TEXT,
            cantidad INTEGER DEFAULT 0, precio REAL DEFAULT 0.0
        );''',
        f'''CREATE TABLE IF NOT EXISTS placas (
            id {pk}, tipo TEXT NOT NULL, codigo TEXT NOT NULL, modelo_tv TEXT,
            ubicacion TEXT, estado TEXT DEFAULT 'Probada / OK', cantidad INTEGER DEFAULT 1
        );''',
        f'''CREATE TABLE IF NOT EXISTS publicaciones (
            id {pk}, producto TEXT NOT NULL, precio REAL DEFAULT 0.0, estado TEXT DEFAULT 'En Venta'
        );''',
        f'''CREATE TABLE IF NOT EXISTS caja (
            id {pk}, tipo TEXT NOT NULL, concepto TEXT NOT NULL, monto REAL NOT NULL, fecha TEXT NOT NULL
        );''',
        f'''CREATE TABLE IF NOT EXISTS firmwares (
            id {pk}, chasis TEXT NOT NULL, modelo TEXT NOT NULL, memoria TEXT, tamano TEXT, url_archivo TEXT NOT NULL
        );'''
    ]
    
    conn = get_db()
    cursor = conn.cursor()
    for q in queries:
        cursor.execute(q)
        
    if is_postgres():
        cursor.execute("INSERT INTO usuarios (usuario, password) VALUES ('admin', '1234') ON CONFLICT (usuario) DO NOTHING;")
    else:
        cursor.execute("INSERT OR IGNORE INTO usuarios (id, usuario, password) VALUES (1, 'admin', '1234')")
        
    conn.commit()
    cursor.close()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = execute_query('SELECT * FROM usuarios WHERE usuario = ? AND password = ?',
                          (data.get('usuario'), data.get('password')), fetchone=True)
    if user:
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "mensaje": "Credenciales inválidas"}), 401

@app.route('/api/ordenes', methods=['GET', 'POST'])
def handle_ordenes():
    if request.method == 'POST':
        data = request.json
        execute_query('INSERT INTO ordenes (cliente, equipo, falla, presupuesto, estado) VALUES (?, ?, ?, ?, ?)',
                      (data.get('cliente'), data.get('equipo'), data.get('falla'), data.get('presupuesto', 0), data.get('estado', 'Ingresado')), commit=True)
        return jsonify({"status": "ok"})
    rows = execute_query('SELECT * FROM ordenes ORDER BY id DESC', fetchall=True)
    return jsonify(rows or [])

@app.route('/imprimir/comprobante/<int:orden_id>')
def imprimir_comprobante(orden_id):
    ord_data = execute_query('SELECT * FROM ordenes WHERE id = ?', (orden_id,), fetchone=True)
    if not ord_data:
        return "Orden no encontrada", 404
    html = f'''
    <!DOCTYPE html><html><head><title>Comprobante OT #{ord_data['id']}</title>
    <style>body {{ font-family: Arial; padding: 20px; }} .box {{ border: 2px solid #000; padding: 15px; max-width: 600px; margin: auto; }}</style>
    </head><body onload="window.print()"><div class="box">
    <h2>Comprobante de Recepción OT #{ord_data['id']}</h2>
    <p><b>Cliente:</b> {ord_data['cliente']}</p><p><b>Equipo:</b> {ord_data['equipo']}</p>
    <p><b>Falla:</b> {ord_data['falla']}</p><p><b>Presupuesto:</b> ${ord_data['presupuesto']}</p>
    </div></body></html>'''
    return render_template_string(html)

@app.route('/imprimir/ticket/<int:orden_id>')
def imprimir_ticket(orden_id):
    ord_data = execute_query('SELECT * FROM ordenes WHERE id = ?', (orden_id,), fetchone=True)
    if not ord_data:
        return "Orden no encontrada", 404
    html = f'''
    <!DOCTYPE html><html><head><title>Ticket OT #{ord_data['id']}</title>
    <style>body {{ font-family: monospace; padding: 10px; width: 280px; margin: auto; border: 1px solid #000; }}</style>
    </head><body onload="window.print()"><h3>TALLER CONTROL OT #{ord_data['id']}</h3>
    <p><b>CLI:</b> {ord_data['cliente']}</p><p><b>EQ:</b> {ord_data['equipo']}</p>
    <p><b>FALLA:</b> {ord_data['falla']}</p></body></html>'''
    return render_template_string(html)

@app.route('/api/placas', methods=['GET', 'POST'])
def handle_placas():
    if request.method == 'POST':
        data = request.json
        execute_query('INSERT INTO placas (tipo, codigo, modelo_tv, ubicacion, estado, cantidad) VALUES (?, ?, ?, ?, ?, ?)',
                      (data.get('tipo'), data.get('codigo'), data.get('modelo_tv'), data.get('ubicacion'), data.get('estado', 'Probada / OK'), data.get('cantidad', 1)), commit=True)
        return jsonify({"status": "ok"})
    rows = execute_query('SELECT * FROM placas ORDER BY id DESC', fetchall=True)
    return jsonify(rows or [])

@app.route('/api/placas/<int:placa_id>/stock', methods=['PUT'])
def update_stock_placa(placa_id):
    data = request.json
    cambio = data.get('cambio', 0)
    execute_query('UPDATE placas SET cantidad = GREATEST(0, cantidad + ?) WHERE id = ?' if is_postgres() else 'UPDATE placas SET cantidad = MAX(0, cantidad + ?) WHERE id = ?',
                  (cambio, placa_id), commit=True)
    return jsonify({"status": "ok"})

@app.route('/api/placas/<int:placa_id>', methods=['DELETE'])
def delete_placa(placa_id):
    execute_query('DELETE FROM placas WHERE id = ?', (placa_id,), commit=True)
    return jsonify({"status": "ok"})

@app.route('/api/repuestos', methods=['GET', 'POST'])
def handle_repuestos():
    if request.method == 'POST':
        data = request.json
        execute_query('INSERT INTO repuestos (categoria, nombre, ubicacion, cantidad, precio) VALUES (?, ?, ?, ?, ?)',
                      (data.get('categoria'), data.get('nombre'), data.get('ubicacion'), data.get('cantidad', 1), data.get('precio', 0.0)), commit=True)
        return jsonify({"status": "ok"})
    rows = execute_query('SELECT * FROM repuestos ORDER BY id DESC', fetchall=True)
    return jsonify(rows or [])

@app.route('/api/repuestos/<int:repuesto_id>/stock', methods=['PUT'])
def update_stock(repuesto_id):
    data = request.json
    cambio = data.get('cambio', 0)
    execute_query('UPDATE repuestos SET cantidad = GREATEST(0, cantidad + ?) WHERE id = ?' if is_postgres() else 'UPDATE repuestos SET cantidad = MAX(0, cantidad + ?) WHERE id = ?',
                  (cambio, repuesto_id), commit=True)
    return jsonify({"status": "ok"})

@app.route('/api/publicaciones', methods=['GET', 'POST'])
def handle_publicaciones():
    if request.method == 'POST':
        data = request.json
        execute_query('INSERT INTO publicaciones (producto, precio, estado) VALUES (?, ?, ?)',
                      (data.get('producto'), data.get('precio', 0.0), data.get('estado', 'En Venta')), commit=True)
        return jsonify({"status": "ok"})
    rows = execute_query('SELECT * FROM publicaciones ORDER BY id DESC', fetchall=True)
    return jsonify(rows or [])

@app.route('/api/caja', methods=['GET', 'POST'])
def handle_caja():
    if request.method == 'POST':
        data = request.json
        execute_query('INSERT INTO caja (tipo, concepto, monto, fecha) VALUES (?, ?, ?, ?)',
                      (data.get('tipo'), data.get('concepto'), data.get('monto'), data.get('fecha')), commit=True)
        return jsonify({"status": "ok"})
    rows = execute_query('SELECT * FROM caja ORDER BY id DESC', fetchall=True)
    return jsonify(rows or [])

@app.route('/api/firmwares', methods=['GET'])
def get_firmwares():
    rows = execute_query('SELECT * FROM firmwares ORDER BY id DESC', fetchall=True)
    return jsonify(rows or [])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
