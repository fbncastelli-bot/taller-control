import os
import re
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

def consultar_gemini_limpio(prompt):
    system_instruction = (
        "Sos un asistente técnico de laboratorio electrónico de Smart TVs. "
        "Tu única función es responder directamente en español técnico. "
        "Queda estrictamente prohibido escribir frases, análisis, verificaciones o encabezados en inglés."
    )
    
    ultimo_error = None

    # 1. Búsqueda dinámica de modelos activos en la cuenta
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                try:
                    model = genai.GenerativeModel(
                        model_name=m.name,
                        system_instruction=system_instruction
                    )
                    res = model.generate_content(prompt)
                    if res and res.text:
                        texto_limpio = re.sub(
                            r'^(Role:|Constraints:|Input Case:|Required Structure:|Model:).*?\n\n', 
                            '', 
                            res.text, 
                            flags=re.DOTALL | re.IGNORECASE
                        )
                        return texto_limpio.strip(), None
                except Exception as e:
                    ultimo_error = str(e)
    except Exception as e:
        ultimo_error = str(e)

    # 2. Reintento alternativo con modelos flash/pro actuales
    candidatos = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash']
    for nombre in candidatos:
        try:
            model = genai.GenerativeModel(
                model_name=nombre,
                system_instruction=system_instruction
            )
            res = model.generate_content(prompt)
            if res and res.text:
                texto_limpio = re.sub(
                    r'^(Role:|Constraints:|Input Case:|Required Structure:|Model:).*?\n\n', 
                    '', 
                    res.text, 
                    flags=re.DOTALL | re.IGNORECASE
                )
                return texto_limpio.strip(), None
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

        prompt = f"""Analizá la siguiente reparación de taller:
- Equipo / Modelo: {equipo}
- Falla reportada: {falla}

Entregá una guía técnica directa:
1. Mediciones de voltaje clave.
2. Método de descarte paso a paso.
3. Componentes propensos a falla en esta etapa."""

        texto, err = consultar_gemini_limpio(prompt)
        if texto:
            return jsonify({'diagnostico': texto})
        return jsonify({'error': f'Error de conexión: {err}'}), 500
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

        prompt = f"""Analizá el chasis / placa de TV: {chasis}

Proporcioná la guía de mediciones referenciando prioritariamente a PINES DE CIRCUITOS INTEGRADOS y BOBINAS DE PASO SMD:

1. PUNTOS DE MEDICIÓN EN CIs Y BOBINAS:
   - Indicá los integrados reguladores Buck/LDO clave de la placa y sus pines de entrada/salida (ej. Pin VCC, Pin LX/OUT, Pin EN).
   - Identificá las bobinas asociadas a las sub-fuentes (1.1V Core, 1.5V/1.8V RAM, 3.3V_STB, 5V, 12V).
   - En el sector T-CON / Panel, indicá los pines del CI generador de VGH, VGL, VDD, VCOM o sus diodos de salida directos.

2. TABLA DE TENSIONES ESPERADAS:
   - Componente / Pin de CI | Tensión Standby | Tensión ON (Encendido)

3. PRUEBAS DE RESISTENCIA EN FRÍO:
   - Valores de resistencia a masa (GND) en las bobinas principales para descartar micros o memorias en corto."""

        texto, err = consultar_gemini_limpio(prompt)
        if texto:
            return jsonify({'test_points': texto})
        return jsonify({'error': f'Error de conexión: {err}'}), 500
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
