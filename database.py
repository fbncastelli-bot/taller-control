import requests
import sqlite3

# URL del servidor backend SaaS (en desarrollo local o en producción)
API_BASE_URL = "http://localhost:8000"

def autenticar_taller(email: str, password: str):
    """
    Envía credenciales al servidor SaaS y retorna el token con los permisos
    de la suscripción (Plan Básico / Plan Pro).
    """
    url = f"{API_BASE_URL}/auth/login"
    payload = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Guardamos el token y permisos de suscripción localmente
            return {
                "exito": True,
                "token": data.get("access_token"),
                "plan": data["tenant"]["plan"],
                "puedo_descargar": data["tenant"]["can_download_firmwares"]
            }
        else:
            return {"exito": False, "error": response.json().get("detail", "Error de autenticación")}
    except Exception as e:
        return {"exito": False, "error": f"Error de conexión con el servidor SaaS: {str(e)}"}