import os
from flask import Flask, render_template, jsonify, request
import google.generativeai as genai

app = Flask(__name__)

# Configuración API Key centralizada
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# Datos iniciales en memoria
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
        "modelo": "Philips 32PFL3008D/77"
    }
]

db_firmwares = [
    {
        "id": 1,
        "chasis": "MS33930.PB751",
        "modelo": "Noblex 32LD870HI",
        "memoria": "SPI Flash 25Q64"
    }
]

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
        "modelo": data.get("modelo", "")
    }
    db_placas.append(nueva_placa)
    return jsonify(nueva_placa), 201

# ENDPOINTS FIRMWARES
@app.route('/api/firmwares', methods=['GET'])
def get_firmwares():
    return jsonify(db_firmwares)

# DIAGNÓSTICO IA CON FALLBACK DINÁMICO
@app.route('/api/analizar-falla', methods=['POST'])
def analizar_falla():
    try:
        data = request.json or {}
        equipo = data.get('equipo', '')
        falla = data.get('falla', '')

        if not GEMINI_KEY:
            return jsonify({'error': 'La variable GEMINI_API_KEY no está configurada'}), 500

        prompt = f"""Sos un técnico especializado en electrónica de TV, consolas y audio.
Analizá el siguiente caso:
- Equipo / Modelo: {equipo}
- Falla reportada: {falla}

Proporcioná una guía técnica directa:
1. Mediciones clave (VGH, VGL, VDD, PFC, sub-fuentes SMD, señales LVDS).
2. Métodos de aislamiento o descarte de etapas.
3. Componentes o sectores propensos a falla en este chasis."""

        candidatos = [
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-2.0-flash',
            'gemini-pro'
        ]

        respuesta_texto = None
        ultimo_error = None

        # 1. Probar modelos candidatos
        for nombre in candidatos:
            try:
                model = genai.GenerativeModel(nombre)
                res = model.generate_content(prompt)
                if res and res.text:
                    respuesta_texto = res.text
                    break
            except Exception as e:
                ultimo_error = str(e)

        # 2. Si fallan los nombres fijos, listar modelos disponibles en la cuenta
        if not respuesta_texto:
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        try:
                            model = genai.GenerativeModel(m.name)
                            res = model.generate_content(prompt)
                            if res and res.text:
                                respuesta_texto = res.text
                                break
                        except Exception as e:
                            ultimo_error = str(e)
            except Exception as e:
                ultimo_error = str(e)

        if respuesta_texto:
            return jsonify({'diagnostico': respuesta_texto})
        else:
            return jsonify({'error': f'No se pudo conectar a un modelo activo: {ultimo_error}'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
