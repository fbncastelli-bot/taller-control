from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

DB_NAME = "taller.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO usuarios (id, usuario, password) VALUES (1, 'admin', '1234')")
    
    # Órdenes de Trabajo con Presupuesto
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
    
    # Clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT
        )
    ''')

    # Stock Componentes
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

    # Ventas y Usados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS publicaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto TEXT NOT NULL,
            precio REAL DEFAULT 0.0,
            estado TEXT DEFAULT 'En Venta'
        )
    ''')

    # Caja y Finanzas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS caja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            concepto TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha TEXT NOT NULL
        )
    ''')

    # Firmwares
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

# --- LOGIN ---
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

# --- ÓRDENES ---
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

# --- CLIENTES ---
@app.route('/api/clientes', methods=['GET'])
def get_clientes():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clientes ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/clientes', methods=['POST'])
def add_cliente():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO clientes (nombre, telefono, direccion) VALUES (?, ?, ?)',
                   (data.get('nombre'), data.get('telefono'), data.get('direccion')))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

# --- STOCK COMPONENTES ---
@app.route('/api/repuestos', methods=['GET'])
def get_repuestos():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM repuestos ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/repuestos', methods=['POST'])
def add_repuesto():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO repuestos (categoria, nombre, ubicacion, cantidad, precio) VALUES (?, ?, ?, ?, ?)',
                   (data.get('categoria'), data.get('nombre'), data.get('ubicacion'), data.get('cantidad', 1), data.get('precio', 0.0)))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

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

# --- VENTAS Y USADOS ---
@app.route('/api/publicaciones', methods=['GET'])
def get_publicaciones():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM publicaciones ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/publicaciones', methods=['POST'])
def add_publicacion():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO publicaciones (producto, precio, estado) VALUES (?, ?, ?)',
                   (data.get('producto'), data.get('precio', 0.0), data.get('estado', 'En Venta')))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

# --- CAJA ---
@app.route('/api/caja', methods=['GET'])
def get_caja():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM caja ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/caja', methods=['POST'])
def add_caja():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO caja (tipo, concepto, monto, fecha) VALUES (?, ?, ?, ?)',
                   (data.get('tipo'), data.get('concepto'), data.get('monto'), data.get('fecha')))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

# --- FIRMWARES ---
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
