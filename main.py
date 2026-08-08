import os
from flask import Flask, render_template, jsonify, request
import google.generativeai as genai

app = Flask(__name__)

# Configuración API Key
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# Memoria temporal
db_ordenes = []
db_repuestos = []
db_placas = []

@app.route('/')
def index():
    return render_template('index.html')

# RUTAS ÓRDENES
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

# RUTAS REPUESTOS
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
        "cantidad": data.get("cantidad", 1)
    }
    db_repuestos.append(nuevo_rep)
    return jsonify(nuevo_rep), 201

# RUTAS PLACAS
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

# ANALIZADOR IA
@app.route('/api/analizar-falla', methods=['POST'])
def analizar_falla():
    try:
        data = request.json or {}
        equipo = data.get('equipo', '')
        falla = data.get('falla', '')

        if not GEMINI_KEY:
            return jsonify({'error': 'API Key no configurada'}), 500

        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Técnico de TV: Analizá este equipo: {equipo}. Falla: {falla}. Indicá mediciones, pruebas de aislamiento y componentes críticos."

        response = model.generate_content(prompt)
        return jsonify({'diagnostico': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
