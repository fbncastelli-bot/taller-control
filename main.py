import os
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import google.generativeai as genai
from pypdf import PdfReader
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave_secreta_taller_2026")

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def get_db_connection():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    return None

def init_db():
    conn = get_db_connection()
    if not conn:
        return
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            usuario VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            nombre_taller VARCHAR(100) DEFAULT 'Mi Taller'
        );
        CREATE TABLE IF NOT EXISTS ordenes (
            id SERIAL PRIMARY KEY,
            usuario_id INT DEFAULT 1,
            cliente VARCHAR(100),
            telefono VARCHAR(50),
            equipo VARCHAR(100),
            falla TEXT,
            solucion TEXT,
            presupuesto NUMERIC(10,2),
            estado VARCHAR(50)
        );
        CREATE TABLE IF NOT EXISTS repuestos (
            id SERIAL PRIMARY KEY,
            usuario_id INT DEFAULT 1,
            categoria VARCHAR(100),
            nombre VARCHAR(100),
            ubicacion VARCHAR(100),
            cantidad INT,
            precio NUMERIC(10,2)
        );
        CREATE TABLE IF NOT EXISTS ventas (
            id SERIAL PRIMARY KEY,
            usuario_id INT DEFAULT 1,
            producto VARCHAR(100),
            precio NUMERIC(10,2),
            estado VARCHAR(50)
        );
        CREATE TABLE IF NOT EXISTS caja (
            id SERIAL PRIMARY KEY,
            usuario_id INT DEFAULT 1,
            fecha VARCHAR(50),
            tipo VARCHAR(20),
            concepto TEXT,
            monto NUMERIC(10,2)
        );
        CREATE TABLE IF NOT EXISTS placas (
            id SERIAL PRIMARY KEY,
            tipo VARCHAR(50),
            codigo VARCHAR(100),
            modelo VARCHAR(100),
            test_points TEXT
        );
    ''')
    conn.commit()

    # MIGRAR REGISTROS HUÉRFANOS AL USUARIO FABIAN ACTUAL
    cur.execute("SELECT id FROM usuarios WHERE LOWER(usuario) = 'fabian';")
    user_fabian = cur.fetchone()
    if user_fabian:
        fid = user_fabian['id']
        cur.execute("UPDATE ordenes SET usuario_id = %s;", (fid,))
        cur.execute("UPDATE repuestos SET usuario_id = %s;", (fid,))
        cur.execute("UPDATE caja SET usuario_id = %s;", (fid,))
        cur.execute("UPDATE ventas SET usuario_id = %s;", (fid,))
        conn.commit()

    cur.close()
    conn.close()

try:
    init_db()
except Exception as e:
    print("Error iniciando BBDD PostgreSQL:", e)

DRIVERS_LED = {
    "OB3350": "Retirar una de las resistencias en paralelo conectadas al pin ISET (pin 5) para aumentar la resistencia total a masa y reducir la corriente un 25-30%.",
    "MAP3202": "Aumentar el valor de la resistencia conectada en la línea R_ISET (pin 6).",
    "BIT3267": "Retirar una resistencia de la red conectada entre ISET (pin 4) y masa.",
    "AP3041": "Modificar el divisor en el pin ISET incrementando el valor de R_SET.",
    "OZ9998": "Aumentar la resistencia conectada al pin ISET para limitar la corriente por rama."
}

def consultar_gemini_limpio(prompt):
    system_instruction = (
        "Sos un asistente técnico de laboratorio electrónico de Smart TVs. Respondé exclusivamente en español técnico. "
        "Queda strictly prohibido usar idioma inglés o escribir preámbulos, introducciones o saludos."
    )
    ultimo_error = None
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                try:
                    model = genai.GenerativeModel(model_name=m.name, system_instruction=system_instruction)
                    res = model.generate_content(prompt)
                    if res and res.text:
                        texto = res.text
                        if '|' in texto:
                            pos_tabla = texto.find('|')
                            texto = texto[pos_tabla:]
                        return texto.strip(), None
                except Exception as e:
                    ultimo_error = str(e)
    except Exception as e:
        ultimo_error = str(e)

    candidatos = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash']
    for nombre in candidatos:
        try:
            model = genai.GenerativeModel(model_name=nombre, system_instruction=system_instruction)
            res = model.generate_content(prompt)
            if res and res.text:
                texto = res.text
                if '|' in texto:
                    pos_tabla = texto.find('|')
                    texto = texto[pos_tabla:]
                return texto.strip(), None
        except Exception as e:
            ultimo_error = str(e)

    return None, ultimo_error

# RUTAS DE AUTENTICACIÓN Y NAVEGACIÓN
@app.route('/')
def index():
    if 'usuario_id' not in session:
        return redirect(url_for('login_view'))
    return render_template('index.html', usuario=session.get('usuario'), taller=session.get('nombre_taller'))

@app.route('/login', methods=['GET', 'POST'])
def login_view():
    if request.method == 'POST':
        user = request.form.get('usuario', '').strip()
        pwd = request.form.get('password', '').strip()
        
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM usuarios WHERE LOWER(usuario) = LOWER(%s) AND password = %s", (user, pwd))
            u = cur.fetchone()
            cur.close()
            conn.close()
            
            if u:
                session['usuario_id'] = u['id']
                session['usuario'] = u['usuario']
                session['nombre_taller'] = u['nombre_taller']
                return redirect(url_for('index'))
                
        return render_template('login.html', error="Usuario o contraseña incorrectos")
    return render_template('login.html')

@app.route('/registro', methods=['POST'])
def registro_view():
    user = request.form.get('usuario', '').strip()
    pwd = request.form.get('password', '').strip()
    taller = request.form.get('nombre_taller', '').strip() or 'Mi Taller'

    if not user or not pwd:
        return render_template('login.html', error="Completar usuario y contraseña")

    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                "INSERT INTO usuarios (usuario, password, nombre_taller) VALUES (%s, %s, %s) RETURNING *;",
                (user, pwd, taller)
            )
            nuevo_u = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()

            session['usuario_id'] = nuevo_u['id']
            session['usuario'] = nuevo_u['usuario']
            session['nombre_taller'] = nuevo_u['nombre_taller']
            return redirect(url_for('index'))
        except Exception:
            return render_template('login.html', error="El nombre de usuario ya existe")

    return render_template('login.html', error="Error al conectar con la base de datos")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_view'))

# ENDPOINTS ÓRDENES (FILTRADO POR USUARIO)
@app.route('/api/ordenes', methods=['GET'])
def get_ordenes():
    if 'usuario_id' not in session:
        return jsonify([])
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM ordenes WHERE usuario_id = %s ORDER BY id ASC;", (session['usuario_id'],))
    filas = cur.fetchall()
    cur.close()
    conn.close()
    for f in filas:
        f['presupuesto'] = float(f['presupuesto'] or 0)
    return jsonify(filas)

@app.route('/api/ordenes', methods=['POST'])
def add_orden():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Sin conexion BBDD'}), 500
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "INSERT INTO ordenes (usuario_id, cliente, telefono, equipo, falla, solucion, presupuesto, estado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *;",
        (session['usuario_id'], data.get("cliente", ""), data.get("telefono", ""), data.get("equipo", ""), data.get("falla", ""), data.get("solucion", ""), float(data.get("presupuesto", 0)), data.get("estado", "Ingresado"))
    )
    nuevo = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if nuevo:
        nuevo['presupuesto'] = float(nuevo['presupuesto'] or 0)
    return jsonify(nuevo), 201

@app.route('/api/ordenes/<int:ot_id>', methods=['DELETE'])
def delete_orden(ot_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM ordenes WHERE id = %s AND usuario_id = %s;", (ot_id, session['usuario_id']))
        conn.commit()
        cur.close()
        conn.close()
    return jsonify({"status": "deleted"})

# ENDPOINTS REPUESTOS (FILTRADO POR USUARIO)
@app.route('/api/repuestos', methods=['GET'])
def get_repuestos():
    if 'usuario_id' not in session:
        return jsonify([])
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM repuestos WHERE usuario_id = %s ORDER BY id ASC;", (session['usuario_id'],))
    filas = cur.fetchall()
    cur.close()
    conn.close()
    for f in filas:
        f['precio'] = float(f['precio'] or 0)
    return jsonify(filas)

@app.route('/api/repuestos', methods=['POST'])
def add_repuesto():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Sin conexion BBDD'}), 500
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "INSERT INTO repuestos (usuario_id, categoria, nombre, ubicacion, cantidad, precio) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *;",
        (session['usuario_id'], data.get("categoria", ""), data.get("nombre", ""), data.get("ubicacion", ""), int(data.get("cantidad", 1)), float(data.get("precio", 0)))
    )
    nuevo = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if nuevo:
        nuevo['precio'] = float(nuevo['precio'] or 0)
    return jsonify(nuevo), 201

@app.route('/api/repuestos/<int:rep_id>', methods=['PUT'])
def update_repuesto(rep_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Sin conexion BBDD'}), 500
    cur = conn.cursor(cursor_factory=RealDictCursor)
    if 'cantidad' in data:
        cur.execute("UPDATE repuestos SET cantidad = %s WHERE id = %s AND usuario_id = %s RETURNING *;", (int(data['cantidad']), rep_id, session['usuario_id']))
    elif 'ubicacion' in data:
        cur.execute("UPDATE repuestos SET ubicacion = %s WHERE id = %s AND usuario_id = %s RETURNING *;", (data['ubicacion'], rep_id, session['usuario_id']))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if res:
        res['precio'] = float(res['precio'] or 0)
    return jsonify(res)

# ENDPOINTS VENTAS (FILTRADO POR USUARIO)
@app.route('/api/ventas', methods=['GET'])
def get_ventas():
    if 'usuario_id' not in session:
        return jsonify([])
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM ventas WHERE usuario_id = %s ORDER BY id ASC;", (session['usuario_id'],))
    filas = cur.fetchall()
    cur.close()
    conn.close()
    for f in filas:
        f['precio'] = float(f['precio'] or 0)
    return jsonify(filas)

@app.route('/api/ventas', methods=['POST'])
def add_venta():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Sin conexion BBDD'}), 500
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "INSERT INTO ventas (usuario_id, producto, precio, estado) VALUES (%s, %s, %s, %s) RETURNING *;",
        (session['usuario_id'], data.get("producto", ""), float(data.get("precio", 0)), data.get("estado", "En Venta"))
    )
    nuevo = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if nuevo:
        nuevo['precio'] = float(nuevo['precio'] or 0)
    return jsonify(nuevo), 201

@app.route('/api/ventas/<int:v_id>', methods=['DELETE'])
def delete_venta(v_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM ventas WHERE id = %s AND usuario_id = %s;", (v_id, session['usuario_id']))
        conn.commit()
        cur.close()
        conn.close()
    return jsonify({"status": "deleted"})

# ENDPOINTS CAJA (FILTRADO POR USUARIO)
@app.route('/api/caja', methods=['GET'])
def get_caja():
    if 'usuario_id' not in session:
        return jsonify({"movimientos": [], "ingresos": 0, "egresos": 0, "balance": 0})
    conn = get_db_connection()
    if not conn:
        return jsonify({"movimientos": [], "ingresos": 0, "egresos": 0, "balance": 0})
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM caja WHERE usuario_id = %s ORDER BY id ASC;", (session['usuario_id'],))
    movimientos = cur.fetchall()
    cur.close()
    conn.close()

    for m in movimientos:
        m['monto'] = float(m['monto'] or 0)

    total_ingresos = sum(m['monto'] for m in movimientos if m['tipo'] == 'Ingreso')
    total_egresos = sum(m['monto'] for m in movimientos if m['tipo'] == 'Egreso')
    balance = total_ingresos - total_egresos

    return jsonify({
        "movimientos": movimientos,
        "ingresos": total_ingresos,
        "egresos": total_egresos,
        "balance": balance
    })

@app.route('/api/caja', methods=['POST'])
def add_movimiento():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Sin conexion BBDD'}), 500
    
    hora_arg = datetime.utcnow() - timedelta(hours=3)
    fecha_str = hora_arg.strftime("%Y-%m-%d %H:%M")

    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "INSERT INTO caja (usuario_id, fecha, tipo, concepto, monto) VALUES (%s, %s, %s, %s, %s) RETURNING *;",
        (session['usuario_id'], fecha_str, data.get("tipo", "Ingreso"), data.get("concepto", ""), float(data.get("monto", 0)))
    )
    nuevo = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if nuevo:
        nuevo['monto'] = float(nuevo['monto'] or 0)
    return jsonify(nuevo), 201

@app.route('/api/caja/<int:mov_id>', methods=['DELETE'])
def delete_movimiento(mov_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM caja WHERE id = %s AND usuario_id = %s;", (mov_id, session['usuario_id']))
        conn.commit()
        cur.close()
        conn.close()
    return jsonify({"status": "deleted"})

# ENDPOINTS RECURSOS COMPARTIDOS (PLACAS, FIRMWARES, IA)
@app.route('/api/placas', methods=['GET'])
def get_placas():
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM placas ORDER BY id ASC;")
    filas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(filas)

@app.route('/api/firmwares', methods=['GET'])
def get_firmwares():
    return jsonify([
        {"id": 1, "chasis": "MS33930.PB751", "modelo": "Noblex 32LD870HI", "memoria": "SPI Flash 25Q64", "url_nube": "https://drive.google.com"}
    ])

@app.route('/api/analizar-falla', methods=['POST'])
def analizar_falla():
    try:
        data = request.json or {}
        equipo, falla = data.get('equipo', ''), data.get('falla', '')
        if not GEMINI_KEY:
            return jsonify({'error': 'Clave API no configurada'}), 500
        prompt = f"Analizá la falla técnica del equipo {equipo} con síntoma {falla}. Brindá mediciones clave, descarte y componentes propensos a falla en español."
        texto, err = consultar_gemini_limpio(prompt)
        return jsonify({'diagnostico': texto}) if texto else jsonify({'error': str(err)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/obtener-test-points', methods=['POST'])
def obtener_test_points():
    try:
        data = request.json or {}
        chasis_buscado = data.get('chasis', '').strip().upper()
        
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM placas WHERE UPPER(codigo) LIKE %s;", (f"%{chasis_buscado}%",))
            placa = cur.fetchone()
            cur.close()
            conn.close()
            if placa:
                return jsonify({'test_points': f"=== DATOS LOCALES DEL TALLER ===\nChasis: {placa['codigo']}\nModelo: {placa['modelo']}\nTest Points:\n{placa['test_points']}"})

        if not GEMINI_KEY:
            return jsonify({'error': 'Clave API no configurada'}), 500

        prompt = f"""Analizá la arquitectura del chasis / placa de TV LED: {chasis_buscado}.

Devolvé ÚNICAMENTE una tabla Markdown en español técnico referenciada a CIs reguladores y bobinas de paso SMD, indicando la comparación entre Standby y ON:

| Sub-fuente / Etapa | IC Regulador o Diodo Salida | Pin de Medición o Bobina | Tensión Standby | Tensión ON (Encendido) | Resistencia a GND |"""

        texto, err = consultar_gemini_limpio(prompt)
        if texto:
            return jsonify({'test_points': texto})
        return jsonify({'error': f'Error de conexión: {err}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analizar-esquematico-pdf', methods=['POST'])
def analizar_esquematico_pdf():
    try:
        if 'archivo' not in request.files:
            return jsonify({'error': 'No se adjuntó ningún archivo PDF'}), 400
        
        file = request.files['archivo']
        chasis = request.form.get('chasis', '').strip().upper()

        if file.filename == '':
            return jsonify({'error': 'Archivo no seleccionado'}), 400

        reader = PdfReader(file)
        texto_extraido = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                texto_extraido += t + "\n"

        if not texto_extraido.strip():
            return jsonify({'error': 'El PDF es un documento escaneado como imagen pura. Seleccioná el texto del diagrama.'}), 400

        if not GEMINI_KEY:
            return jsonify({'error': 'Clave API no configurada'}), 500

        prompt = f"""Analizá el esquema técnico del chasis/fuente: {chasis}.

Contenido del plano extraído:
{texto_extraido[:8000]}

Devolvé ÚNICAMENTE una tabla Markdown en español técnico referenciada a la serigrafía real del plano:
| Etapa / Sub-fuente | IC / Transistor / Diodo Salida | Pin / Punto de Medición | Tensión Nominal | Estado (STB / ON) |"""

        texto, err = consultar_gemini_limpio(prompt)
        if texto:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO placas (tipo, codigo, modelo, test_points) VALUES (%s, %s, %s, %s);",
                    ("Esquemático PDF Cargado", chasis, file.filename, texto)
                )
                conn.commit()
                cur.close()
                conn.close()
            return jsonify({'resultado': texto})
            
        return jsonify({'error': f'Error de procesamiento: {err}'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/preguntar-esquematico', methods=['POST'])
def preguntar_esquematico():
    try:
        data = request.json or {}
        chasis = data.get('chasis', '')
        pregunta = data.get('pregunta', '')
        contexto = data.get('contexto', '')

        if not GEMINI_KEY:
            return jsonify({'error': 'Clave API no configurada'}), 500

        prompt = f"""Basándote en el plano esquemático del chasis/fuente {chasis} con la siguiente estructura:

{contexto}

Consulta técnica:
{pregunta}

Respondé de forma directa y técnica en español, indicando componentes o reemplazos directos."""

        texto, err = consultar_gemini_limpio(prompt)
        if texto:
            return jsonify({'respuesta': texto})
        return jsonify({'error': f'Error al procesar: {err}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calcular-backlight', methods=['POST'])
def calcular_backlight():
    data = request.json or {}
    driver = data.get('driver', '').upper().strip()
    instruccion = DRIVERS_LED.get(driver, "Driver no registrado. Modificar la resistencia en el pin ISET/IREF para reducir corriente un 25-30%.")
    return jsonify({'driver': driver, 'procedimiento': instruccion})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
