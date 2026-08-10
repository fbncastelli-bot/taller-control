import os
import re
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import google.generativeai as genai
from pypdf import PdfReader
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "laboratorio_llave_secreta_2026")

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
    cur = conn.cursor()
    
    # Tabla de Usuarios
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            nombre_taller VARCHAR(100)
        );
    ''')

    # Crear usuario por defecto 'fabian' si no existe
    cur.execute("SELECT id FROM usuarios WHERE username = 'fabian';")
    user_default = cur.fetchone()
    if not user_default:
        default_hash = generate_password_hash("admin1234")
        cur.execute("INSERT INTO usuarios (username, password_hash, nombre_taller) VALUES (%s, %s, %s) RETURNING id;",
                    ('fabian', default_hash, 'Taller Fabian'))
        fabian_id = cur.fetchone()[0]
    else:
        fabian_id = user_default[0]

    # Tablas con aislamiento por usuario_id
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ordenes (
            id SERIAL PRIMARY KEY,
            usuario_id INT REFERENCES usuarios(id),
            cliente VARCHAR(100),
            telefono VARCHAR(50),
            equipo VARCHAR(100),
            falla TEXT,
            presupuesto NUMERIC(10,2),
            estado VARCHAR(50)
        );
        CREATE TABLE IF NOT EXISTS repuestos (
            id SERIAL PRIMARY KEY,
            usuario_id INT REFERENCES usuarios(id),
            categoria VARCHAR(100),
            nombre VARCHAR(100),
            ubicacion VARCHAR(100),
            cantidad INT,
            precio NUMERIC(10,2)
        );
        CREATE TABLE IF NOT EXISTS ventas (
            id SERIAL PRIMARY KEY,
            usuario_id INT REFERENCES usuarios(id),
            producto VARCHAR(100),
            precio NUMERIC(10,2),
            estado VARCHAR(50)
        );
        CREATE TABLE IF NOT EXISTS caja (
            id SERIAL PRIMARY KEY,
            usuario_id INT REFERENCES usuarios(id),
            fecha VARCHAR(50),
            tipo VARCHAR(20),
            concepto TEXT,
            monto NUMERIC(10,2)
        );
        CREATE TABLE IF NOT EXISTS placas (
            id SERIAL PRIMARY KEY,
            usuario_id INT REFERENCES usuarios(id),
            tipo VARCHAR(50),
            codigo VARCHAR(100),
            modelo VARCHAR(100),
            test_points TEXT
        );
    ''')

    # Asegurar migración de columna usuario_id para registros preexistentes
    for tabla in ['ordenes', 'repuestos', 'ventas', 'caja', 'placas']:
        cur.execute(f"ALTER TABLE {tabla} ADD COLUMN IF NOT EXISTS usuario_id INT REFERENCES usuarios(id);")
        cur.execute(f"UPDATE {tabla} SET usuario_id = %s WHERE usuario_id IS NULL;", (fabian_id,))

    conn.commit()
    cur.close()
    conn.close()

try:
    init_db()
except Exception as e:
    print("Error iniciando BBDD PostgreSQL:", e)

DRIVERS_LED = {
    "OB3350": "Pin 5 (ISET): Retirar una de las resistencias en paralelo conectadas a masa para aumentar la resistencia total de R_ISET y reducir la corriente del backlight un 25-30%.",
    "MAP3202": "Pin 6 (R_ISET): Aumentar el valor de la resistencia conectada de este pin a masa (ej: de 10k a 15k-18k).",
    "BIT3267": "Pin 4 (ISET): Retirar una de las resistencias en paralelo a masa para elevar la impedancia y bajar la corriente de los LED.",
    "AP3041": "Pin ISET: Modificar el divisor resistivo incrementando el valor de R_SET.",
    "OZ9998": "Pin ISET: Aumentar la resistencia conectada al pin ISET para limitar la corriente por rama.",
    "BD9488F": "Pin 10 (ISET): Aumentar el valor de la resistencia a masa para bajar la corriente total de salida.",
    "MP3394": "Pin 6 (ISET): Aumentar la resistencia R_ISET para limitar la corriente por canal."
}

def obtener_modelo_activo():
    if not GEMINI_KEY:
        return None, "Sin API Key"
    
    system_instruction = (
        "Sos un asistente técnico de laboratorio electrónico de Smart TVs. Respondé exclusivamente en español técnico. "
        "Queda strictly prohibido usar idioma inglés o escribir preámbulos, introducciones o saludos."
    )
    
    prioridad_modelos = ['gemini-2.0-pro-exp', 'gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash']
    
    try:
        modelos_cuenta = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for p in prioridad_modelos:
            if p in modelos_cuenta:
                return genai.GenerativeModel(model_name=p, system_instruction=system_instruction), p.replace('-', ' ').title()
    except Exception:
        pass

    for nombre in prioridad_modelos:
        try:
            m = genai.GenerativeModel(model_name=nombre, system_instruction=system_instruction)
            return m, nombre.replace('-', ' ').title()
        except Exception:
            continue

    return None, "No disponible"

def consultar_gemini_limpio(prompt):
    model, nombre_modelo = obtener_modelo_activo()
    if not model:
        return None, "Error al inicializar el modelo de IA"

    try:
        res = model.generate_content(prompt)
        if res and res.text:
            texto = res.text
            if '|' in texto:
                pos_tabla = texto.find('|')
                texto = texto[pos_tabla:]
            return texto.strip(), None
    except Exception as e:
        return None, str(e)

    return None, "Sin respuesta del modelo"

# SISTEMA DE AUTENTICACIÓN
@app.route('/')
def index():
    if 'usuario_id' not in session:
        return render_template('login.html')
    return render_template('index.html', usuario=session.get('username'), taller=session.get('taller'))

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión con la base de datos'}), 500

    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM usuarios WHERE LOWER(username) = %s;", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        session['usuario_id'] = user['id']
        session['username'] = user['username']
        session['taller'] = user['nombre_taller'] or user['username']
        return jsonify({'status': 'ok', 'taller': session['taller']})
    
    return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401

@app.route('/api/registro', methods=['POST'])
def registro():
    data = request.json or {}
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')
    taller = data.get('taller', '').strip() or f"Taller {username}"

    if not username or not password:
        return jsonify({'error': 'Completá usuario y contraseña'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error BBDD'}), 500

    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id FROM usuarios WHERE LOWER(username) = %s;", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({'error': 'El nombre de usuario ya existe'}), 400

    p_hash = generate_password_hash(password)
    cur.execute("INSERT INTO usuarios (username, password_hash, nombre_taller) VALUES (%s, %s, %s) RETURNING *;",
                (username, p_hash, taller))
    nuevo = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    session['usuario_id'] = nuevo['id']
    session['username'] = nuevo['username']
    session['taller'] = nuevo['nombre_taller']
    return jsonify({'status': 'ok'})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'status': 'ok'})

@app.route('/api/info-modelo', methods=['GET'])
def info_modelo():
    _, nombre = obtener_modelo_activo()
    return jsonify({'modelo_activo': nombre, 'usuario': session.get('username', ''), 'taller': session.get('taller', '')})

# ENDPOINTS FILTRADOS POR USUARIO_ID
@app.route('/api/ordenes', methods=['GET'])
def get_ordenes():
    if 'usuario_id' not in session: return jsonify([]), 401
    conn = get_db_connection()
    if not conn: return jsonify([])
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM ordenes WHERE usuario_id = %s ORDER BY id ASC;", (session['usuario_id'],))
    filas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(filas)

@app.route('/api/ordenes', methods=['POST'])
def add_orden():
    if 'usuario_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Sin conexion BBDD'}), 500
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "INSERT INTO ordenes (usuario_id, cliente, telefono, equipo, falla, presupuesto, estado) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *;",
            (
                session['usuario_id'],
                data.get("cliente", ""),
                data.get("telefono", ""),
                data.get("equipo", ""),
                data.get("falla", ""),
                float(data.get("presupuesto", 0) or 0),
                data.get("estado", "Ingresado")
            )
        )
        nuevo = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(nuevo), 201
    except Exception as e:
        if conn: conn.rollback(); conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/ordenes/<int:ot_id>', methods=['DELETE'])
def delete_orden(ot_id):
    if 'usuario_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM ordenes WHERE id = %s AND usuario_id = %s;", (ot_id, session['usuario_id']))
        conn.commit()
        cur.close()
        conn.close()
    return jsonify({"status": "deleted"})

@app.route('/api/repuestos', methods=['GET'])
def get_repuestos():
    if 'usuario_id' not in session: return jsonify([]), 401
    conn = get_db_connection()
    if not conn: return jsonify([])
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM repuestos WHERE usuario_id = %s ORDER BY id ASC;", (session['usuario_id'],))
    filas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(filas)

@app.route('/api/repuestos', methods=['POST'])
def add_repuesto():
    if 'usuario_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Sin conexion BBDD'}), 500
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "INSERT INTO repuestos (usuario_id, categoria, nombre, ubicacion, cantidad, precio) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *;",
        (session['usuario_id'], data.get("categoria", ""), data.get("nombre", ""), data.get("ubicacion", ""), int(data.get("cantidad", 1)), float(data.get("precio", 0)))
    )
    nuevo = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(nuevo), 201

@app.route('/api/repuestos/<int:rep_id>', methods=['PUT'])
def update_repuesto(rep_id):
    if 'usuario_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Sin conexion BBDD'}), 500
    cur = conn.cursor(cursor_factory=RealDictCursor)
    if 'cantidad' in data:
        cur.execute("UPDATE repuestos SET cantidad = %s WHERE id = %s AND usuario_id = %s RETURNING *;", (int(data['cantidad']), rep_id, session['usuario_id']))
    elif 'ubicacion' in data:
        cur.execute("UPDATE repuestos SET ubicacion = %s WHERE id = %s AND usuario_id = %s RETURNING *;", (data['ubicacion'], rep_id, session['usuario_id']))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(res)

@app.route('/api/ventas', methods=['GET'])
def get_ventas():
    if 'usuario_id' not in session: return jsonify([]), 401
    conn = get_db_connection()
    if not conn: return jsonify([])
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM ventas WHERE usuario_id = %s ORDER BY id ASC;", (session['usuario_id'],))
    filas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(filas)

@app.route('/api/ventas', methods=['POST'])
def add_venta():
    if 'usuario_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Sin conexion BBDD'}), 500
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "INSERT INTO ventas (usuario_id, producto, precio, estado) VALUES (%s, %s, %s, %s) RETURNING *;",
        (session['usuario_id'], data.get("producto", ""), float(data.get("precio", 0)), data.get("estado", "En Venta"))
    )
    nuevo = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(nuevo), 201

@app.route('/api/ventas/<int:v_id>', methods=['DELETE'])
def delete_venta(v_id):
    if 'usuario_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM ventas WHERE id = %s AND usuario_id = %s;", (v_id, session['usuario_id']))
        conn.commit()
        cur.close()
        conn.close()
    return jsonify({"status": "deleted"})

@app.route('/api/placas', methods=['GET'])
def get_placas():
    if 'usuario_id' not in session: return jsonify([]), 401
    conn = get_db_connection()
    if not conn: return jsonify([])
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM placas WHERE usuario_id = %s ORDER BY id ASC;", (session['usuario_id'],))
    filas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(filas)

@app.route('/api/firmwares', methods=['GET'])
def get_firmwares():
    return jsonify([
        {"id": 1, "chasis": "MS33930.PB751", "modelo": "Noblex 32LD870HI", "memoria": "SPI Flash 25Q64", "url_nube": "https://drive.google.com"}
    ])

@app.route('/api/caja', methods=['GET'])
def get_caja():
    if 'usuario_id' not in session: return jsonify({"movimientos": [], "ingresos": 0, "egresos": 0, "balance": 0}), 401
    conn = get_db_connection()
    if not conn: return jsonify({"movimientos": [], "ingresos": 0, "egresos": 0, "balance": 0})
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM caja WHERE usuario_id = %s ORDER BY id ASC;", (session['usuario_id'],))
    movimientos = cur.fetchall()
    cur.close()
    conn.close()

    total_ingresos = sum(float(m['monto']) for m in movimientos if m['tipo'] == 'Ingreso')
    total_egresos = sum(float(m['monto']) for m in movimientos if m['tipo'] == 'Egreso')
    balance = total_ingresos - total_egresos

    return jsonify({"movimientos": movimientos, "ingresos": total_ingresos, "egresos": total_egresos, "balance": balance})

@app.route('/api/caja', methods=['POST'])
def add_movimiento():
    if 'usuario_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Sin conexion BBDD'}), 500
    
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
    return jsonify(nuevo), 201

@app.route('/api/caja/<int:mov_id>', methods=['DELETE'])
def delete_movimiento(mov_id):
    if 'usuario_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM caja WHERE id = %s AND usuario_id = %s;", (mov_id, session['usuario_id']))
        conn.commit()
        cur.close()
        conn.close()
    return jsonify({"status": "deleted"})

@app.route('/api/calcular-backlight', methods=['POST'])
def calcular_backlight():
    data = request.json or {}
    driver = data.get('driver', '').upper().strip()
    instruccion = DRIVERS_LED.get(driver, f"Driver '{driver}' no registrado de fábrica. Procedimiento general: Localizar el pin ISET / IREF / ISENSE del integrado, medir la resistencia total conectada a masa y aumentarla entre un 20% y 35% para lograr una reducción de corriente proporcional.")
    return jsonify({'driver': driver, 'procedimiento': instruccion})

@app.route('/api/analizar-falla', methods=['POST'])
def analizar_falla():
    try:
        data = request.json or {}
        equipo, falla = data.get('equipo', ''), data.get('falla', '')
        if not GEMINI_KEY: return jsonify({'error': 'Clave API no configurada'}), 500
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
        if conn and 'usuario_id' in session:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM placas WHERE UPPER(codigo) LIKE %s AND usuario_id = %s;", (f"%{chasis_buscado}%", session['usuario_id']))
            placa = cur.fetchone()
            cur.close()
            conn.close()
            if placa:
                return jsonify({'test_points': f"=== DATOS LOCALES DEL TALLER ===\nChasis: {placa['codigo']}\nModelo: {placa['modelo']}\nTest Points:\n{placa['test_points']}"})

        if not GEMINI_KEY: return jsonify({'error': 'Clave API no configurada'}), 500

        prompt = f"""Analizá la arquitectura del chasis / placa de TV LED: {chasis_buscado}.
Devolvé ÚNICAMENTE una tabla Markdown en español técnico referenciada a CIs reguladores y bobinas de paso SMD, indicando la comparación entre Standby y ON:
| Sub-fuente / Etapa | IC Regulador o Diodo Salida | Pin de Medición o Bobina | Tensión Standby | Tensión ON (Encendido) | Resistencia a GND |"""

        texto, err = consultar_gemini_limpio(prompt)
        return jsonify({'test_points': texto}) if texto else jsonify({'error': f'Error de conexión: {err}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analizar-esquematico-pdf', methods=['POST'])
def analizar_esquematico_pdf():
    try:
        if 'usuario_id' not in session: return jsonify({'error': 'No autorizado'}), 401
        if 'archivo' not in request.files: return jsonify({'error': 'No se adjuntó ningún archivo PDF'}), 400
        
        file = request.files['archivo']
        chasis = request.form.get('chasis', '').strip().upper()
        if file.filename == '': return jsonify({'error': 'Archivo no seleccionado'}), 400

        reader = PdfReader(file)
        texto_extraido = "".join([page.extract_text() + "\n" for page in reader.pages if page.extract_text()])

        if not texto_extraido.strip():
            return jsonify({'error': 'El PDF es un documento escaneado como imagen pura. Seleccioná el texto del diagrama.'}), 400

        if not GEMINI_KEY: return jsonify({'error': 'Clave API no configurada'}), 500

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
                    "INSERT INTO placas (usuario_id, tipo, codigo, modelo, test_points) VALUES (%s, %s, %s, %s, %s);",
                    (session['usuario_id'], "Esquemático PDF Cargado", chasis, file.filename, texto)
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
        chasis, pregunta, contexto = data.get('chasis', ''), data.get('pregunta', ''), data.get('contexto', '')

        if not GEMINI_KEY: return jsonify({'error': 'Clave API no configurada'}), 500

        prompt = f"""Basándote en el plano esquemático del chasis/fuente {chasis} con la siguiente estructura:
{contexto}
Consulta técnica:
{pregunta}
Respondé de forma directa y técnica en español, indicando componentes o reemplazos directos."""

        texto, err = consultar_gemini_limpio(prompt)
        return jsonify({'respuesta': texto}) if texto else jsonify({'error': f'Error al procesar: {err}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
