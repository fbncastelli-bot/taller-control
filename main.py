import os
from flask import Flask, render_template, jsonify, request
import google.generativeai as genai

app = Flask(__name__)

# Configurar API Key de Gemini
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analizar-falla', methods=['POST'])
def analizar_falla():
    try:
        data = request.json or {}
        equipo = data.get('equipo', 'TV LED')
        falla = data.get('falla', 'Sin imagen / Con audio')

        if not GEMINI_KEY:
            return jsonify({'error': 'GEMINI_API_KEY no está configurada'}), 500

        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Analizá la siguiente falla técnica en electrónica de TV/Consolas. Equipo: {equipo}. Falla: {falla}. Dame un diagnóstico técnico directo, puntos de medición clave (voltajes VGH, VGL, VDD, etc.) y pruebas rápidas en 3 viñetas concisas."

        response = model.generate_content(prompt)
        return jsonify({'diagnostico': response.text})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
