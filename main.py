import os
from flask import Flask, render_template, jsonify, request
import google.generativeai as genai

app = Flask(__name__)

# Configuración API Key centralizada
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# Base de datos local
db_ordenes = [
    {
        "id": 1,
        "cliente": "Jose RCA",
        "equipo": "RCA L40T20SMART",
        "falla": "Leds quemados, cambio de tiras",
        "presupuesto": 45000
    }
]

db_repuestos = [
    {
        "id": 1,
        "categoria": "IC Fuente",
        "nombre": "RT6905",
        "ubicacion": "Caja 1 - SMD",
        "cantidad": 5
    }
]

db_placas = [
    {
        "id": 1,
        "tipo": "Main Board",
        "codigo": "715G5155-M01-002-005K",
        "modelo": "Philips 32PFL3008D/77",
        "test_points": "VGH: 28V | VGL: -7V | VDD: 3.3V | VCOM: 6.5V | 12V_STB: 12V"
    }
]

db_firmwares = [
    {
        "id": 1,
        "chasis": "MS33930.PB751",
        "modelo": "Noblex 32LD870HI",
        "memoria": "SPI Flash 25Q64",
        "url_nube": "https://drive.google.com"
    }
]

DRIVERS_LED = {
    "OB3350": "Retirar una de las resistencias en paralelo conectadas al pin ISET (pin 5) para aumentar la resistencia total a masa y reducir la corriente un 25-30%.",
    "MAP3202": "Aumentar el valor de la resistencia conectada en la línea R_ISET (pin 6).",
    "BIT3267": "Retirar una resistencia de la red conectada entre ISET (pin 4) y masa.",
    "AP3041": "Modificar el divisor en el pin ISET incrementando el valor de R_SET.",
    "OZ9998": "Aumentar la resistencia conectada al pin ISET para limitar la corriente por rama."
}

def consultar_gemini_dinamico(prompt):
    candidatos = [
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-2.0-flash',
        'gemini-pro'
    ]
    ultimo_error = None

    for nombre in candidatos:
        try:
            model = genai.GenerativeModel(nombre)
            res = model.generate_content(prompt)
            if res and res.text:
                return res.text, None
        except Exception as e:
            ultimo_error = str(e)

    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                try:
                    model = genai.GenerativeModel(m.name)
                    res = model.generate_content(prompt)
                    if res and res.text:
                        return res.text, None
                except Exception as e:
                    ultimo_error = str(e)
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
        "presupuesto": data.get("presupuesto", 0)
    }
    db_ordenes.append(nueva_ot)
    return jsonify(nueva_ot), 201

# ENDPOINTS REPUESTOS
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
        "cantidad": int(data.get("cantidad", 1))
    }
    db_repuestos.append(nuevo_rep)
    return jsonify(nuevo_rep), 201

# ENDPOINTS PLACAS
@app.route('/api/placas', methods=['GET'])
def get_placas():
    return jsonify(db_placas)

@app.route('/api/placas', methods=['POST'])
def add_placa():
    data = request.json or {}
    nueva_placa = {
        "id": len(db_placas) + 1,
        "tipo": data.get("tipo", ""),
        "codigo": data.get("codigo", ""),
        "modelo": data.get("modelo", ""),
        "test_points": data.get("test_points", "Sin datos")
    }
    db_placas.append(nueva_placa)
    return jsonify(nueva_placa), 201

# ENDPOINTS FIRMWARES
@app.route('/api/firmwares', methods=['GET'])
def get_firmwares():
    return jsonify(db_firmwares)

# DIAGNÓSTICO IA
@app.route('/api/analizar-falla', methods=['POST'])
def analizar_falla():
    try:
        data = request.json or {}
        equipo = data.get('equipo', '')
        falla = data.get('falla', '')

        if not GEMINI_KEY:
            return jsonify({'error': 'La variable GEMINI_API_KEY no está configurada'}), 500

        prompt = f"""Sos un técnico profesional especializado en reparación de electrónica de Smart TVs, consolas y audio.
Analizá el siguiente caso y responde OBLIGATORIAMENTE Y ÚNICAMENTE EN ESPAÑOL TÉCNICO:

- Equipo / Modelo: {equipo}
- Falla reportada: {falla}

Proporcioná una guía estructurada:
1. Mediciones clave (VGH, VGL, VDD, PFC, sub-fuentes SMD, señales LVDS).
2. Métodos de aislamiento o descarte de etapas.
3. Componentes o sectores propensos a falla en este chasis."""

        texto, err = consultar_gemini_dinamico(prompt)
        if texto:
            return jsonify({'diagnostico': texto})
        return jsonify({'error': f'No se pudo conectar a un modelo activo: {err}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# TEST POINTS VÍA IA
@app.route('/api/obtener-test-points', methods=['POST'])
def obtener_test_points():
    try:
        data = request.json or {}
        chasis = data.get('chasis', '')

        if not GEMINI_KEY:
            return jsonify({'error': 'Clave API no configurada'}), 500

        prompt = f"""Sos un técnico experto en reparación de TV LED y LCD. 
Generá en ESPAÑOL la tabla de puntos de prueba (Test Points) y tensiones nominales de referencia para el chasis o placa: {chasis}.

Detallá:
1. Tensiones T-CON (VGH, VGL, VDD, VCOM).
2. Sub-fuentes SMD y bobinas de la Main (Core, RAM, 3.3V, 5V, 12V).
3. Prueba de resistencia/diodos típica respecto a masa para descartar cortos."""

        texto, err = consultar_gemini_dinamico(prompt)
        if texto:
            return jsonify({'test_points': texto})
        return jsonify({'error': f'No se pudo conectar a un modelo activo: {err}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# CALCULADORA BACKLIGHT
@app.route('/api/calcular-backlight', methods=['POST'])
def calcular_backlight():
    data = request.json or {}
    driver = data.get('driver', '').upper().strip()

    instruccion = DRIVERS_LED.get(
        driver, 
        "Driver no registrado en la base fija. Regla general: Identificar el pin ISET/IREF del CI y aumentar un 25-50% el valor de la resistencia a masa o retirar una resistencia SMD en paralelo para bajar la corriente de LEDs."
    )

    return jsonify({'driver': driver, 'procedimiento': instruccion})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
