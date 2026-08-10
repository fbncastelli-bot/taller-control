import os
import re
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import google.generativeai as genai
from pypdf import PdfReader
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

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
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            usuario VARCHAR(50) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre_taller VARCHAR(100)
        );
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ordenes (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
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
            user_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
            categoria VARCHAR(100),
            nombre VARCHAR(100),
            ubicacion VARCHAR(100),
            cantidad INT,
            precio NUMERIC(10,2)
        );
        CREATE TABLE IF NOT EXISTS ventas (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
            producto VARCHAR(100),
            precio NUMERIC(10,2),
            estado VARCHAR(50)
        );
        CREATE TABLE IF NOT EXISTS caja (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
            fecha VARCHAR(50),
            tipo VARCHAR(20),
            concepto TEXT,
            monto NUMERIC(10,2)
        );
        CREATE TABLE IF NOT EXISTS placas (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
            tipo VARCHAR(50),
            codigo VARCHAR(100),
            modelo VARCHAR(100),
            test_points TEXT
        );
    ''')
    cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS nombre_taller VARCHAR(100);")
    cur.execute("ALTER TABLE ordenes ADD COLUMN IF NOT EXISTS telefono VARCHAR(50);")
    cur.execute("ALTER TABLE ordenes ADD COLUMN IF NOT EXISTS solucion TEXT;")
    cur.execute("ALTER TABLE ordenes ADD COLUMN IF NOT EXISTS user_id INT;")
    cur.execute("ALTER TABLE repuestos ADD COLUMN IF NOT EXISTS user_id INT;")
    cur.execute("ALTER TABLE ventas ADD COLUMN IF NOT EXISTS user_id INT;")
    cur.execute("ALTER TABLE caja ADD COLUMN IF NOT EXISTS user_id INT;")
    cur.execute("ALTER TABLE placas ADD COLUMN IF NOT EXISTS user_id INT;")
    
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
        "Queda estrictamente prohibido usar idioma inglés o escribir preámbulos, introducciones o saludos."
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

# RUTAS AUTENTICACIÓN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('usuario', '').strip()
        pwd = request.form.get('password', '').strip()
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM usuarios WHERE LOWER(usuario) = LOWER(%s);", (user,))
            u = cur.fetchone()
            
            if u:
                if check_password_hash(u['password'], pwd):
                    session['user_id'] = u['id']
                    session['usuario'] = u['usuario']
                    session['taller'] = u['nombre_taller'] or "Servicio Técnico"
                    cur.close()
                    conn.close()
                    return redirect('/')
                else:
                    cur.close()
                    conn.close()
                    return render_template('login.html', error="Contraseña incorrecta.")
            else:
                pwd_hash = generate_password_hash(pwd)
                cur.execute("INSERT INTO usuarios (usuario, password, nombre_taller) VALUES (%s, %s, %s) RETURNING *;", (user, pwd_hash, "Servicio Técnico"))
                u_nuevo = cur.fetchone()
                conn.commit()
                cur.close()
                conn.close()
                session['user_id'] = u_nuevo['id']
                session['usuario'] = u_nuevo['usuario']
                session['taller'] = u_nuevo['nombre_taller']
                return redirect('/')
        return render_template('login.html', error="Error de conexión a la BBDD.")
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    user = request.form.get('usuario', '').strip()
    pwd = request.form.get('password', '').strip()
    taller = request.form.get('nombre_taller', 'Servicio Técnico').strip()
    if not user or not pwd:
        return render_template('login.html', error="Completá todos los campos.")
    
    pwd_hash = generate_password_hash(pwd)
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM usuarios WHERE LOWER(usuario) = LOWER(%s);", (user,))
            u_existente = cur.fetchone()
            if u_existente:
                cur.execute("UPDATE usuarios SET password = %s, nombre_taller = %s WHERE id = %s RETURNING *;", (pwd_hash, taller, u_existente['id']))
                u_final = cur.fetchone()
            else:
                cur.execute("INSERT INTO usuarios (usuario, password, nombre_taller) VALUES (%s, %s, %s) RETURNING *;", (user, pwd_hash, taller))
                u_final = cur.fetchone()
                
            conn.commit()
            cur.close()
            conn.close()
            
            session['user_id'] = u_final['id']
            session['usuario'] = u_final['usuario']
            session['taller'] = u_final['nombre_taller']
            return redirect('/')
        except Exception as e:
            if conn: conn.close()
            return render_template('login.html', error=f"Error en registro: {e}")
    return render_template('login.html', error="Error de conexión a la base de datos.")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('index.html', usuario=session.get('usuario'), taller=session.get('taller'))

# ENDPOINTS ÓRDENES
@app.route('/api/ordenes', methods=['GET'])
def get_ordenes():
    if 'user_id' not in session: return jsonify([]), 401
    conn = get_db_connection()
    if not conn: return jsonify([])
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM ordenes WHERE user_id = %s OR user_id IS NULL ORDER BY id ASC;", (session['user_id'],))
    filas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(filas)

@app.route('/api/ordenes', methods=['POST'])
def add_orden():
    if 'user_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Sin conexion BBDD'}), 500
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "INSERT INTO ordenes (user_id, cliente, telefono, equipo, falla, solucion, presupuesto, estado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *;",
            (session['user_id'], data.get("cliente", ""), data.get("telefono", ""), data.get("equipo", ""), data.get("falla", ""), data.get("solucion", ""), float(data.get("presupuesto", 0) or 0), data.get("estado", "Ingresado"))
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
    if 'user_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM ordenes WHERE id = %s AND (user_id = %s OR user_id IS NULL);", (ot_id, session['user_id']))
        conn.commit()
        cur.close()
        conn.close()
    return jsonify({"status": "deleted"})

# BUSCADOR DE FALLAS RECURRENTES (BBDD LOCAL + IA)
@app.route('/api/fallas-recurrentes', methods=['POST'])
def fallas_recurrentes():
    if 'user_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    chasis = data.get('chasis', '').strip().upper()

    if not chasis:
        return jsonify({'error': 'Ingresá el modelo o chasis del equipo.'}), 400

    conn = get_db_connection()
    historial_local = []
    if conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT id, equipo, falla, solucion, estado FROM ordenes WHERE (user_id = %s OR user_id IS NULL) AND UPPER(equipo) LIKE %s AND solucion IS NOT NULL AND solucion != '';",
            (session['user_id'], f"%{chasis}%")
        )
        historial_local = cur.fetchall()
        cur.close()
        conn.close()

    res_texto = ""
    if historial_local:
        res_texto += "=== ANTECEDENTES REGISTRADOS EN TU TALLER ===\n"
        for h in historial_local:
            res_texto += f"• OT #{h['id']} ({h['equipo']}): Falla: {h['falla']} -> Solución: {h['solucion']}\n"
        res_texto += "\n"

    if GEMINI_KEY:
        prompt = f"""Proporcioná las fallas recurrentes típicas, componentes propensos a falla y subfuentes críticas del chasis / modelo de TV LED: {chasis}.
Devolvé una tabla Markdown en español técnico con:
| Etapa / Circuito | Síntoma / Falla | Componente Crítico / Posición | Solución / Reemplazo Recomendado |"""
        texto_ia, err_ia = consultar_gemini_limpio(prompt)
        if texto_ia:
            res_texto += "=== SUGERENCIAS DE FALLAS TÍPICAS (IA) ===\n" + texto_ia
        elif err_ia and not historial_local:
            res_texto += f"Error IA: {err_ia}"

    return jsonify({'resultado': res_texto if res_texto else "Sin datos registrados ni respuesta de IA."})

# ENDPOINTS STOCK / REPUESTOS
@app.route('/api/repuestos', methods=['GET'])
def get_repuestos():
    if 'user_id' not in session: return jsonify([]), 401
    conn = get_db_connection()
    if not conn: return jsonify([])
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM repuestos WHERE user_id = %s OR user_id IS NULL ORDER BY id ASC;", (session['user_id'],))
    filas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(filas)

@app.route('/api/repuestos', methods=['POST'])
def add_repuesto():
    if 'user_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Sin conexion BBDD'}), 500
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "INSERT INTO repuestos (user_id, categoria, nombre, ubicacion, cantidad, precio) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *;",
        (session['user_id'], data.get("categoria", ""), data.get("nombre", ""), data.get("ubicacion", ""), int(data.get("cantidad", 1)), float(data.get("precio", 0)))
    )
    nuevo = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(nuevo), 201

@app.route('/api/repuestos/<int:rep_id>', methods=['PUT'])
def update_repuesto(rep_id):
    if 'user_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Sin conexion BBDD'}), 500
    cur = conn.cursor(cursor_factory=RealDictCursor)
    if 'cantidad' in data:
        cur.execute("UPDATE repuestos SET cantidad = %s WHERE id = %s AND (user_id = %s OR user_id IS NULL) RETURNING *;", (int(data['cantidad']), rep_id, session['user_id']))
    elif 'ubicacion' in data:
        cur.execute("UPDATE repuestos SET ubicacion = %s WHERE id = %s AND (user_id = %s OR user_id IS NULL) RETURNING *;", (data['ubicacion'], rep_id, session['user_id']))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(res)

# ENDPOINTS VENTAS Y USADOS
@app.route('/api/ventas', methods=['GET'])
def get_ventas():
    if 'user_id' not in session: return jsonify([]), 401
    conn = get_db_connection()
    if not conn: return jsonify([])
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM ventas WHERE user_id = %s OR user_id IS NULL ORDER BY id ASC;", (session['user_id'],))
    filas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(filas)

@app.route('/api/ventas', methods=['POST'])
def add_venta():
    if 'user_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Sin conexion BBDD'}), 500
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "INSERT INTO ventas (user_id, producto, precio, estado) VALUES (%s, %s, %s, %s) RETURNING *;",
        (session['user_id'], data.get("producto", ""), float(data.get("precio", 0)), data.get("estado", "En Venta"))
    )
    nuevo = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(nuevo), 201

@app.route('/api/ventas/<int:v_id>', methods=['DELETE'])
def delete_venta(v_id):
    if 'user_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM ventas WHERE id = %s AND (user_id = %s OR user_id IS NULL);", (v_id, session['user_id']))
        conn.commit()
        cur.close()
        conn.close()
    return jsonify({"status": "deleted"})

# ENDPOINTS BANCO DE PLACAS
@app.route('/api/placas', methods=['GET'])
def get_placas():
    if 'user_id' not in session: return jsonify([]), 401
    conn = get_db_connection()
    if not conn: return jsonify([])
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM placas WHERE user_id = %s OR user_id IS NULL ORDER BY id ASC;", (session['user_id'],))
    filas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(filas)

# ENDPOINTS FIRMWARES
@app.route('/api/firmwares', methods=['GET'])
def get_firmwares():
    return jsonify([
        {"id": 1, "chasis": "MS33930.PB751", "modelo": "Noblex 32LD870HI", "memoria": "SPI Flash 25Q64", "url_nube": "https://drive.google.com"}
    ])

# ENDPOINTS CAJA Y FINANZAS
@app.route('/api/caja', methods=['GET'])
def get_caja():
    if 'user_id' not in session: return jsonify({"movimientos": [], "ingresos": 0, "egresos": 0, "balance": 0}), 401
    conn = get_db_connection()
    if not conn: return jsonify({"movimientos": [], "ingresos": 0, "egresos": 0, "balance": 0})
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM caja WHERE user_id = %s OR user_id IS NULL ORDER BY id ASC;", (session['user_id'],))
    movimientos = cur.fetchall()
    cur.close()
    conn.close()

    total_ingresos = sum(float(m['monto']) for m in movimientos if m['tipo'] == 'Ingreso')
    total_egresos = sum(float(m['monto']) for m in movimientos if m['tipo'] == 'Egreso')
    balance = total_ingresos - total_egresos

    return jsonify({
        "movimientos": movimientos,
        "ingresos": total_ingresos,
        "egresos": total_egresos,
        "balance": balance
    })

@app.route('/api/caja', methods=['POST'])
def add_movimiento():
    if 'user_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Sin conexion BBDD'}), 500
    
    hora_arg = datetime.utcnow() - timedelta(hours=3)
    fecha_str = hora_arg.strftime("%Y-%m-%d %H:%M")

    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "INSERT INTO caja (user_id, fecha, tipo, concepto, monto) VALUES (%s, %s, %s, %s, %s) RETURNING *;",
        (session['user_id'], fecha_str, data.get("tipo", "Ingreso"), data.get("concepto", ""), float(data.get("monto", 0)))
    )
    nuevo = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(nuevo), 201

@app.route('/api/caja/<int:mov_id>', methods=['DELETE'])
def delete_movimiento(mov_id):
    if 'user_id' not in session: return jsonify({'error': 'No autorizado'}), 401
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM caja WHERE id = %s AND (user_id = %s OR user_id IS NULL);", (mov_id, session['user_id']))
        conn.commit()
        cur.close()
        conn.close()
    return jsonify({"status": "deleted"})

# CONSULTAS IA Y TEST POINTS
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
        if conn and 'user_id' in session:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM placas WHERE UPPER(codigo) LIKE %s AND (user_id = %s OR user_id IS NULL);", (f"%{chasis_buscado}%", session['user_id']))
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
            if conn and 'user_id' in session:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO placas (user_id, tipo, codigo, modelo, test_points) VALUES (%s, %s, %s, %s, %s);",
                    (session['user_id'], "Esquemático PDF Cargado", chasis, file.filename, texto)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
