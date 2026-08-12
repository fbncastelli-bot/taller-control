import os
import sqlite3
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'super_secret_key_taller'

DB_NAME = 'taller.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        password TEXT,
        nombre TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS ordenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cliente TEXT, telefono TEXT, equipo TEXT, falla TEXT, presupuesto REAL, ubicacion TEXT, estado TEXT DEFAULT 'Ingresado'
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS placas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, codigo TEXT, modelo TEXT, test_points TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS firmwares (
        id INTEGER PRIMARY KEY AUTOINCREMENT, chasis TEXT, modelo TEXT, memoria TEXT, url_nube TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS repuestos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, nombre TEXT, ubicacion TEXT, cantidad INTEGER, precio REAL
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, producto TEXT, precio REAL, estado TEXT DEFAULT 'En Venta'
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS caja (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP, tipo TEXT, concepto TEXT, monto REAL
    )''')
    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO usuarios (usuario, password, nombre) VALUES ('Fabian', '1234', 'Fabián')")
        cur.execute("INSERT INTO usuarios (usuario, password, nombre) VALUES ('Jose', '1234', 'José')")
        cur.execute("INSERT INTO usuarios (usuario, password, nombre) VALUES ('Gerardo', '1234', 'Gerardo')")
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

DRIVERS_LED = {
    "OB3350": "Modificar resistencia en pin ISET (pin 5). Aumentar el valor de R para reducir corriente.",
    "MAP3202": "Modificar resistencias conectadas a los pines CS1/CS2. Retirar resistencias en paralelo.",
    "BIT3267": "Ajustar pin OVP o cambiar resistencia en pin ISET (pin 4).",
    "OZ9998": "Modificar valor de resistencia conectada a pin ISEN.",
    "AP3031": "Aumentar valor de resistencia conectada al pin FB (Feedback)."
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    usuario = data.get('usuario')
    password = data.get('password')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE usuario = ? AND password = ?", (usuario, password))
    user = cur.fetchone()
    conn.close()
    if user:
        session['usuario'] = user['nombre']
        return jsonify({'success': True, 'usuario': user['nombre']})
    return jsonify({'success': False, 'message': 'Credenciales inválidas'}), 401

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect('/')

@app.route('/api/ordenes', methods=['GET', 'POST'])
def handle_ordenes():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'POST':
        data = request.json or {}
        cur.execute('''INSERT INTO ordenes (cliente, telefono, equipo, falla, presupuesto, ubicacion)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (data.get('cliente'), data.get('telefono'), data.get('equipo'), 
                     data.get('falla'), data.get('presupuesto', 0), data.get('ubicacion')))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})
    else:
        cur.execute("SELECT * FROM ordenes ORDER BY id DESC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)

@app.route('/api/ordenes/<int:id>', methods=['DELETE'])
def delete_orden(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM ordenes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/placas', methods=['GET', 'POST'])
def handle_placas():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'POST':
        data = request.json or {}
        cur.execute("INSERT INTO placas (tipo, codigo, modelo, test_points) VALUES (?, ?, ?, ?)",
                    (data.get('tipo'), data.get('codigo'), data.get('modelo'), data.get('test_points')))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})
    else:
        cur.execute("SELECT * FROM placas ORDER BY id DESC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)

@app.route('/api/firmwares', methods=['GET', 'POST'])
def handle_firmwares():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'POST':
        data = request.json or {}
        cur.execute("INSERT INTO firmwares (chasis, modelo, memoria, url_nube) VALUES (?, ?, ?, ?)",
                    (data.get('chasis'), data.get('modelo'), data.get('memoria'), data.get('url_nube')))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})
    else:
        cur.execute("SELECT * FROM firmwares ORDER BY id DESC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)

@app.route('/api/repuestos', methods=['GET', 'POST'])
def handle_repuestos():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'POST':
        data = request.json or {}
        cur.execute("INSERT INTO repuestos (categoria, nombre, ubicacion, cantidad, precio) VALUES (?, ?, ?, ?, ?)",
                    (data.get('categoria'), data.get('nombre'), data.get('ubicacion'), data.get('cantidad', 0), data.get('precio', 0)))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})
    else:
        cur.execute("SELECT * FROM repuestos ORDER BY id DESC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)

@app.route('/api/ventas', methods=['GET', 'POST'])
def handle_ventas():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'POST':
        data = request.json or {}
        cur.execute("INSERT INTO ventas (producto, precio) VALUES (?, ?)",
                    (data.get('producto'), data.get('precio', 0)))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})
    else:
        cur.execute("SELECT * FROM ventas ORDER BY id DESC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)

@app.route('/api/caja', methods=['GET', 'POST'])
def handle_caja():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'POST':
        data = request.json or {}
        cur.execute("INSERT INTO caja (tipo, concepto, monto) VALUES (?, ?, ?)",
                    (data.get('tipo'), data.get('concepto'), data.get('monto', 0)))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})
    else:
        cur.execute("SELECT * FROM caja ORDER BY id DESC")
        movimientos = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT SUM(monto) FROM caja WHERE tipo = 'Ingreso'")
        ingresos = cur.fetchone()[0] or 0
        cur.execute("SELECT SUM(monto) FROM caja WHERE tipo = 'Egreso'")
        egresos = cur.fetchone()[0] or 0
        conn.close()
        return jsonify({
            'movimientos': movimientos,
            'ingresos': ingresos,
            'egresos': egresos,
            'balance': ingresos - egresos
        })

@app.route('/api/analizar-falla', methods=['POST'])
def analizar_falla():
    data = request.json or {}
    equipo = data.get('equipo', '')
    falla = data.get('falla', '')
    diagnostico = f"Diagnóstico sugerido para {equipo}:\n- Falla reportada: {falla}\n- Verificación inicial: Comprobar voltajes de fuente (STBY y Power-On).\n- Si no hay imagen pero hay audio: Revisar circuito inverter / driver LED."
    return jsonify({'diagnostico': diagnostico})

@app.route('/api/calcular-backlight', methods=['POST'])
def calcular_backlight():
    data = request.json or {}
    driver = data.get('driver', '').upper().strip()
    instruccion = DRIVERS_LED.get(driver, "Driver no registrado. Modificar la resistencia conectada al pin ISET o CS.")
    return jsonify({'driver': driver, 'procedimiento': instruccion})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
