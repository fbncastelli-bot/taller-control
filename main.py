from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

DB_NAME = "taller.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla de Usuarios (Login)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Insertar usuario administrador por defecto si no existe
    cursor.execute("INSERT OR IGNORE INTO usuarios (id, usuario, password) VALUES (1, 'admin', '1234')")
    
    # Tabla de Órdenes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ordenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            equipo TEXT NOT NULL,
            falla TEXT NOT NULL,
            estado TEXT DEFAULT 'Ingresado'
        )
    ''')
    
    # Tabla de Clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT
        )
    ''')

    # Tabla de Stock / Repuestos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repuestos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            cantidad INTEGER DEFAULT 0,
            precio REAL DEFAULT 0.0
        )
    ''')

    # Tabla de Movimientos de Caja
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS caja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            concepto TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

# Inicializar BD al arrancar
init_db()

@app.route('/')
def home():
    return render_template('index.html')

# --- ENDPOINT LOGIN ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    usuario = data.get('usuario')
    password = data.get('password')
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE usuario = ? AND password = ?', (usuario, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({"status": "ok", "mensaje": "Acceso correcto"})
    else:
        return jsonify({"status": "error", "mensaje": "Usuario o contraseña incorrectos"}), 401

# --- ENDPOINTS ÓRDENES ---
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
    cursor.execute('INSERT INTO ordenes (cliente, equipo, falla, estado) VALUES (?, ?, ?, ?)',
                   (data['cliente'], data['equipo'], data['falla'], 'Ingresado'))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

# --- ENDPOINTS CLIENTES ---
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
                   (data['nombre'], data['telefono'], data['direccion']))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

# --- ENDPOINTS REPUESTOS ---
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
    cursor.execute('INSERT INTO repuestos (nombre, cantidad, precio) VALUES (?, ?, ?)',
                   (data['nombre'], data['cantidad'], data['precio']))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

# --- ENDPOINTS CAJA ---
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
                   (data['tipo'], data['concepto'], data['monto'], data['fecha']))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)