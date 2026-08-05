import os
import json

TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".taller_session.json")

def guardar_session(username: str, token: str, can_download: bool):
    data = {
        "username": username,
        "token": token,
        "can_download": can_download
    }
    try:
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

def cargar_session():
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def borrar_session():
    if os.path.exists(TOKEN_FILE):
        try:
            os.remove(TOKEN_FILE)
        except Exception:
            pass