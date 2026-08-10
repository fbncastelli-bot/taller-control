import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "lab_control_secret_2026")

DATABASE_URL = os.environ.get("DATABASE_URL")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def inicializar_bd():
    if not DATABASE_URL:
        return
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                usuario VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                password VARCHAR(255),
                nombre_taller VARCHAR(100) NOT NULL DEFAULT 'Mi Taller',
                telefono_taller VARCHAR(30),
                rol VARCHAR(20) DEFAULT 'admin'
            );
        """)
        
        try:
            cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);")
            cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS password VARCHAR(255);")
            cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS nombre_taller VARCHAR(100) DEFAULT 'Mi Taller';")
            cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS telefono_taller VARCHAR(30);")
        except Exception:
            pass

        cur.execute("""
            CREATE TABLE IF NOT EXISTS ordenes (
                id SERIAL PRIMARY KEY,
                usuario_id INT DEFAULT 1,
                cliente VARCHAR(100) NOT NULL,
                telefono VARCHAR(30),
                equipo VARCHAR(100) NOT NULL,
                falla TEXT,
                solucion TEXT,
                presupuesto NUMERIC(10, 2) DEFAULT 0,
                estado VARCHAR(30) DEFAULT 'Ingresado',
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS repuestos (
                id SERIAL PRIMARY KEY,
                usuario_id INT DEFAULT 1,
                categoria VARCHAR(50),
                nombre VARCHAR(100) NOT NULL,
                ubicacion VARCHAR(50),
                cantidad INT DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS ventas (
                id SERIAL PRIMARY KEY,
                usuario_id INT DEFAULT 1,
                producto VARCHAR(100) NOT NULL,
                precio NUMERIC(10, 2) DEFAULT 0,
                estado VARCHAR(30) DEFAULT 'En Venta'
            );

            CREATE TABLE IF NOT EXISTS caja (
                id SERIAL PRIMARY KEY,
                usuario_id INT DEFAULT 1,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo VARCHAR(20) NOT NULL,
                concepto VARCHAR(150) NOT NULL,
                monto NUMERIC(10, 2) DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS firmwares (
                id SERIAL PRIMARY KEY,
                chasis VARCHAR(100) NOT NULL,
                modelo VARCHAR(100),
                memoria VARCHAR(50),
                url_nube TEXT NOT NULL
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error inicializando BD:", e)

inicializar_bd()

@app.route('/')
def index():
    if 'usuario_id' not in session:
        return redirect(url_for('login_view'))
    return render_template('index.html', usuario=session.get('usuario'), taller=session.get('nombre_taller'))

@app.route('/login', methods=['GET', 'POST'])
def login_view():
    if request.method == 'POST':
        data = request.form
        user = data.get('usuario', '').strip()
        pwd = data.get('password', '').strip()
        
        if not user or not pwd:
            return render_template('login.html', error="Por favor ingrese usuario y contraseña")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE LOWER(usuario) = LOWER(%s)", (user,))
        u = cur.fetchone()
        cur.close()
        conn.close()

        if u:
            pwd_hash = u.get('password_hash') or ''
            pwd_plana = u.get('password') or ''
            valido = False
            
            if pwd_hash.startswith('pbkdf2:') or pwd_hash.startswith('scrypt:'):
                try:
                    valido = check_password_hash(pwd_hash, pwd)
                except Exception:
                    valido = False
            
            if not valido and pwd_plana:
                valido = (pwd_plana.strip() == pwd)

            if not valido and pwd_hash:
                valido = (pwd_hash.strip() == pwd)

            if valido:
                session['usuario_id'] = u['id']
                session['usuario'] = u['usuario']
                session['nombre_taller'] = u.get('nombre_taller') or 'Mi Taller'
                return redirect(url_for('index'))

        return render_template('login.html', error="Usuario o contraseña incorrectos")
            
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
@app.route('/registro_taller', methods=['GET', 'POST'])
@app.route('/crear_taller', methods=['GET', 'POST'])
@app.route('/crear-taller', methods=['GET', 'POST'])
def registro_view():
    if request.method == 'POST':
        data = request.form
        user = data.get('usuario', '').strip()
        pwd = data.get('password', '').strip()
        taller = data.get('nombre_taller', '').strip() or 'Mi Taller'
        tel = data.get('telefono_taller', '').strip()

        if not user or not pwd:
            return render_template('registro.html', error="El usuario y la contraseña son obligatorios")

        pwd_hash = generate_password_hash(pwd)

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO usuarios (usuario, password_hash, password, nombre_taller, telefono_taller)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, usuario, nombre_taller
            """, (user, pwd_hash, pwd, taller, tel))
            nuevo_u = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()

            session['usuario_id'] = nuevo_u['id']
            session['usuario'] = nuevo_u['usuario']
            session['nombre_taller'] = nuevo_u['nombre_taller']
            return redirect(url_for('index'))

        except Exception as e:
            return render_template('registro.html', error="El nombre de usuario ya existe o hubo un error al registrar.")

    return render_template('registro.html')

@app.route('/reset-clave', methods=['GET', 'POST'])
def reset_clave():
    if request.method == 'POST':
        user = request.form.get('usuario', '').strip()
        new_pwd = request.form.get('password', '').strip()
        if user and new_pwd:
            conn = get_db_connection()
            cur = conn.cursor()
            pwd_hash = generate_password_hash(new_pwd)
            cur.execute("""
                UPDATE usuarios 
                SET password_hash = %s, password = %s 
                WHERE LOWER(usuario) = LOWER(%s)
            """, (pwd_hash, new_pwd, user))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('login_view'))
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Restablecer Clave</title></head>
    <body style="background-color:#121212; color:#fff; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
        <form method="POST" style="background:#1e1e1e; padding:30px; border-radius:8px; border:1px solid #333; width:300px;">
            <h3 style="color:#0d6efd; text-align:center;">Restablecer Clave</h3>
            <label style="display:block; margin-top:10px;">Usuario:</label>
            <input type="text" name="usuario" required style="width:100%; padding:8px; margin-top:5px; background:#2b2b2b; color:#fff; border:1px solid #444; box-sizing:border-box;">
            <label style="display:block; margin-top:10px;">Nueva Contraseña:</label>
            <input type="password" name="password" required style="width:100%; padding:8px; margin-top:5px; background:#2b2b2b; color:#fff; border:1px solid #444; box-sizing:border-box;">
            <button type="submit" style="width:100%; padding:10px; margin-top:20px; background:#0d6efd; color:#fff; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">Actualizar e Ingresar</button>
        </form>
    </body>
    </html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_view'))

# API ÓRDENES
@app.route('/api/ordenes', methods=['GET', 'POST'])
def handle_ordenes():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    uid = session['usuario_id']
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        d = request.json
        cur.execute("""
            INSERT INTO ordenes (usuario_id, cliente, telefono, equipo, falla, solucion, presupuesto, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (uid, d.get('cliente'), d.get('telefono'), d.get('equipo'), d.get('falla'), d.get('solucion'), d.get('presupuesto', 0), d.get('estado', 'Ingresado')))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})

    cur.execute("SELECT * FROM ordenes WHERE usuario_id = %s ORDER BY id DESC", (uid,))
    ordenes = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(ordenes)

@app.route('/api/ordenes/<int:oid>', methods=['DELETE'])
def delete_orden(oid):
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM ordenes WHERE id = %s AND usuario_id = %s", (oid, session['usuario_id']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'ok'})

# API REPUESTOS
@app.route('/api/repuestos', methods=['GET', 'POST'])
def handle_repuestos():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    uid = session['usuario_id']
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        d = request.json
        cur.execute("""
            INSERT INTO repuestos (usuario_id, categoria, nombre, ubicacion, cantidad)
            VALUES (%s, %s, %s, %s, %s)
        """, (uid, d.get('categoria'), d.get('nombre'), d.get('ubicacion'), d.get('cantidad', 1)))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})

    cur.execute("SELECT * FROM repuestos WHERE usuario_id = %s ORDER BY id DESC", (uid,))
    rep = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rep)

@app.route('/api/repuestos/<int:rid>', methods=['PUT'])
def update_repuesto(rid):
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    d = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    if 'cantidad' in d:
        cur.execute("UPDATE repuestos SET cantidad = %s WHERE id = %s AND usuario_id = %s", (d['cantidad'], rid, session['usuario_id']))
    if 'ubicacion' in d:
        cur.execute("UPDATE repuestos SET ubicacion = %s WHERE id = %s AND usuario_id = %s", (d['ubicacion'], rid, session['usuario_id']))
        
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'ok'})

# API CAJA
@app.route('/api/caja', methods=['GET', 'POST'])
def handle_caja():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    uid = session['usuario_id']
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        d = request.json
        cur.execute("""
            INSERT INTO caja (usuario_id, tipo, concepto, monto)
            VALUES (%s, %s, %s, %s)
        """, (uid, d.get('tipo'), d.get('concepto'), d.get('monto', 0)))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})

    cur.execute("SELECT * FROM caja WHERE usuario_id = %s ORDER BY id DESC", (uid,))
    movs = cur.fetchall()

    ingresos = sum(float(m['monto']) for m in movs if m['tipo'] == 'Ingreso')
    egresos = sum(float(m['monto']) for m in movs if m['tipo'] == 'Egreso')

    cur.close()
    conn.close()
    return jsonify({
        'movimientos': movs,
        'ingresos': ingresos,
        'egresos': egresos,
        'balance': ingresos - egresos
    })

@app.route('/api/caja/<int:mid>', methods=['DELETE'])
def delete_caja(mid):
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM caja WHERE id = %s AND usuario_id = %s", (mid, session['usuario_id']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'ok'})

# API VENTAS
@app.route('/api/ventas', methods=['GET', 'POST'])
def handle_ventas():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    uid = session['usuario_id']
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        d = request.json
        cur.execute("""
            INSERT INTO ventas (usuario_id, producto, precio, estado)
            VALUES (%s, %s, %s, %s)
        """, (uid, d.get('producto'), d.get('precio', 0), d.get('estado', 'En Venta')))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})

    cur.execute("SELECT * FROM ventas WHERE usuario_id = %s ORDER BY id DESC", (uid,))
    v = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(v)

@app.route('/api/ventas/<int:vid>', methods=['DELETE'])
def delete_venta(vid):
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM ventas WHERE id = %s AND usuario_id = %s", (vid, session['usuario_id']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'ok'})

# API FIRMWARES
@app.route('/api/firmwares')
def handle_firmwares():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM firmwares ORDER BY id DESC")
    f = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(f)

# API IA DIAGNÓSTICO
@app.route('/api/analizar-falla', methods=['POST'])
def analizar_falla():
    d = request.json
    equipo = d.get('equipo', '')
    falla = d.get('falla', '')

    if not GEMINI_API_KEY:
        return jsonify({'diagnostico': 'API Key de Gemini no configurada.'})

    prompt = f"Como técnico electrónico especialista en Smart TV y audio, analizá el equipo '{equipo}' con la falla '{falla}'. Indica: 1. Etapa del circuito a revisar. 2. Componentes críticos a medir (MOSFET, PWM, diodos, capacitores). 3. Prueba rápida en mesa de trabajo."
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        res = model.generate_content(prompt)
        return jsonify({'diagnostico': res.text})
    except Exception as e:
        return jsonify({'diagnostico': f'Error al consultar IA: {e}'})

@app.route('/api/fallas-recurrentes', methods=['POST'])
def fallas_recurrentes():
    d = request.json
    chasis = d.get('chasis', '')

    if not GEMINI_API_KEY:
        return jsonify({'resultado': 'API Key no disponible.'})

    prompt = f"Para el chasis/placa de TV '{chasis}', enumera las 3 fallas más típicas reportadas en talleres y los componentes específicos que suelen fallar (ej: posiciones R, C, Q, IC)."

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        res = model.generate_content(prompt)
        return jsonify({'resultado': res.text})
    except Exception as e:
        return jsonify({'resultado': f'Error al consultar IA: {e}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
