import os
import re
from flask import Flask, render_template, jsonify, request
import google.generativeai as genai

app = Flask(__name__)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# BASES DE DATOS EN MEMORIA
db_ordenes = [
    {"id": 1, "cliente": "Jose RCA", "equipo": "RCA L40T20SMART", "falla": "Leds quemados, cambio de tiras", "presupuesto": 45000, "estado": "En Proceso"}
]

db_repuestos = [
    {"id": 1, "categoria": "IC Fuente", "nombre": "RT6905", "ubicacion": "Caja 1 - SMD", "cantidad": 5, "precio": 3500},
    {"id": 2, "categoria": "Driver LED", "nombre": "MAP3202", "ubicacion": "Caja 2 - SMD", "cantidad": 3, "precio": 2800}
]

db_placas = [
    {
        "id": 1,
        "tipo": "Main / Power Combo",
        "codigo": "RSAG7.820.4680",
        "modelo": "BGH / Hisense / Noblex 32-40",
        "test_points": "12V_MAIN: 12V | 3.3V_STB: 3.3V | 1.1V_CORE: 1.1V | VGH: 28V | VGL: -7V | VDD: 3.3V"
    }
]

db_firmwares = [
    {"id": 1, "chasis": "MS33930.PB751", "modelo": "Noblex 32LD870HI", "memoria": "SPI Flash 25Q64", "url_nube": "https://drive.google.com"}
]

db_caja = [
    {"id": 1, "tipo": "Ingreso", "concepto": "Cobro OT #1 - RCA L40T20SMART", "monto": 45000, "fecha": "2026-08-08"}
]

DRIVERS_LED = {
    "OB3350": "Retirar una de las resistencias en paralelo conectadas al pin ISET (pin 5) para aumentar la resistencia total a masa y reducir la corriente un 25-30%.",
    "MAP3202": "Aumentar el valor de la resistencia conectada en la línea R_ISET (pin 6).",
    "BIT3267": "Retirar una resistencia de la red conectada entre ISET (pin 4) y masa.",
    "AP3041": "Modificar el divisor en el pin ISET incrementando el valor de R_SET.",
    "OZ9998": "Aumentar la resistencia conectada al pin ISET para limitar la corriente por rama."
}

def consultar_gemini_limpio(prompt):
    system_instruction = (
        "Sos un asistente técnico de laboratorio electrónico de Smart TVs y audio. "
        "Tu única función es responder directamente en español técnico. "
        "Queda estrictamente prohibido escribir frases, análisis, verificaciones o encabezados en inglés."
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

@app.route('/')
def index():
    return render_template('index.html')

# ENDPOINTS ÓRDENES
@app.route('/api/ordenes', methods=['GET'])
def get_ordenes():
    return jsonify(db_ordenes)

@app.route('/api/ordenes', methods=['POST'])
def add_orden():
    data = request.json or {}
    nueva_ot = {
        "id": len(db_ordenes) + 1,
        "cliente": data.get("cliente", ""),
        "equipo": data.get("equipo", ""),
        "falla": data.get("falla", ""),
        "presupuesto": float(data.get("presupuesto", 0)),
        "estado": data.get("estado", "En Taller")
    }
    db_ordenes.append(nueva_ot)
    return jsonify(nueva_ot), 201

# ENDPOINTS STOCK / REPUESTOS
@app.route('/api/repuestos', methods=['GET'])
def get_repuestos():
    return jsonify(db_repuestos)

@app.route('/api/repuestos', methods=['POST'])
def add_repuesto():
    data = request.json or {}
    nuevo_rep = {
        "id": len(db_repuestos) + 1,
        "categoria": data.get("categoria", ""),
        "nombre": data.get("nombre", ""),
        "ubicacion": data.get("ubicacion", ""),
        "cantidad": int(data.get("cantidad", 1)),
        "precio": float(data.get("precio", 0))
    }
    db_repuestos.append(nuevo_rep)
    return jsonify(nuevo_rep), 201

@app.route('/api/repuestos/<int:rep_id>/stock', methods=['PUT'])
def update_stock(rep_id):
    data = request.json or {}
    delta = int(data.get('delta', 0))
    for r in db_repuestos:
        if r['id'] == rep_id:
            r['cantidad'] = max(0, r['cantidad'] + delta)
            return jsonify(r)
    return jsonify({'error': 'Repuesto no encontrado'}), 404

@app.route('/api/consultar-datasheet', methods=['POST'])
def consultar_datasheet():
    try:
        data = request.json or {}
        componente = data.get('componente', '').strip()
        if not GEMINI_KEY:
            return jsonify({'error': 'Clave API no configurada'}), 500
        
        prompt = f"""Proporcioná la ficha técnica directa (Datasheet) del componente/IC: {componente}.
Entregá la respuesta en español técnico con la siguiente estructura:
1. Función principal y empaquetado (Encapsulado).
2. Pinout y función de pines clave (VCC, GND, FB/ISET, OUT/LX, EN).
3. Tensiones máximas de trabajo y rangos de operación.
4. Reemplazos directos o equivalentes recomendados."""
        
        texto, err = consultar_gemini_limpio(prompt)
        return jsonify({'datasheet': texto}) if texto else jsonify({'error': str(err)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ENDPOINTS PLACAS / TEST POINTS
@app.route('/api/placas', methods=['GET'])
def get_placas():
    return jsonify(db_placas)

@app.route('/api/placas', methods=['POST'])
def add_placa():
    data = request.json or {}
    nueva_placa = {
        "id": len(db_placas) + 1,
        "tipo": data.get("tipo", "Main Board"),
        "codigo": data.get("codigo", ""),
        "modelo": data.get("modelo", ""),
        "test_points": data.get("test_points", "Sin datos")
    }
    db_placas.append(nueva_placa)
    return jsonify(nueva_placa), 201

@app.route('/api/obtener-test-points', methods=['POST'])
def obtener_test_points():
    try:
        data = request.json or {}
        chasis_buscado = data.get('chasis', '').strip().upper()
        for placa in db_placas:
            if chasis_buscado in placa['codigo'].upper():
                return jsonify({'test_points': f"=== DATOS LOCALES DEL TALLER ===\nChasis: {placa['codigo']}\nModelo: {placa['modelo']}\nTest Points: {placa['test_points']}"})
        if not GEMINI_KEY:
            return jsonify({'error': 'Clave API no configurada'}), 500
        prompt = f"Tabla técnica de test points para el chasis {chasis_buscado}. Devolvé únicamente tabla Markdown en español con columnas: Sub-fuente, IC/Componente, Tensión Standby, Tensión ON, Resistencia a GND."
        texto, err = consultar_gemini_limpio(prompt)
        return jsonify({'test_points': texto}) if texto else jsonify({'error': str(err)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analizar-esquematico', methods=['POST'])
def analizar_esquematico():
    try:
        data = request.json or {}
        chasis, texto_esquema = data.get('chasis', ''), data.get('texto_esquema', '')
        if not GEMINI_KEY:
            return jsonify({'error': 'Clave API no configurada'}), 500
        prompt = f"Analizá el esquema del chasis {chasis}:\n{texto_esquema}\nExtraé las sub-fuentes, integrados y tensiones (Standby/ON) en una tabla Markdown."
        texto, err = consultar_gemini_limpio(prompt)
        return jsonify({'resultado': texto}) if texto else jsonify({'error': str(err)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ENDPOINTS FIRMWARES
@app.route('/api/firmwares', methods=['GET'])
def get_firmwares():
    return jsonify(db_firmwares)

@app.route('/api/firmwares', methods=['POST'])
def add_firmware():
    data = request.json or {}
    nuevo_fw = {
        "id": len(db_firmwares) + 1,
        "chasis": data.get("chasis", ""),
        "modelo": data.get("modelo", ""),
        "memoria": data.get("memoria", ""),
        "url_nube": data.get("url_nube", "")
    }
    db_firmwares.append(nuevo_fw)
    return jsonify(nuevo_fw), 201

# ENDPOINTS CAJA
@app.route('/api/caja', methods=['GET'])
def get_caja():
    total_ingresos = sum(item['monto'] for item in db_caja if item['tipo'] == 'Ingreso')
    total_egresos = sum(item['monto'] for item in db_caja if item['tipo'] == 'Egreso')
    balance = total_ingresos - total_egresos
    return jsonify({
        "movimientos": db_caja,
        "ingresos": total_ingresos,
        "egresos": total_egresos,
        "balance": balance
    })

@app.route('/api/caja', methods=['POST'])
def add_movimiento():
    data = request.json or {}
    nuevo_mov = {
        "id": len(db_caja) + 1,
        "tipo": data.get("tipo", "Ingreso"),
        "concepto": data.get("concepto", ""),
        "monto": float(data.get("monto", 0)),
        "fecha": data.get("fecha", "2026-08-08")
    }
    db_caja.append(nuevo_mov)
    return jsonify(nuevo_mov), 201

# DIAGNÓSTICO Y CALCULADORA
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

@app.route('/api/calcular-backlight', methods=['POST'])
def calcular_backlight():
    data = request.json or {}
    driver = data.get('driver', '').upper().strip()
    instruccion = DRIVERS_LED.get(driver, "Driver no registrado en la base fija. Modificar la resistencia en el pin ISET/IREF para reducir corriente un 25-30%.")
    return jsonify({'driver': driver, 'procedimiento': instruccion})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
