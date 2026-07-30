from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(
    title="API Servidor Taller Control",
    version="3.3"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos para la interfaz gráfica
app.mount("/static", StaticFiles(directory="static"), name="static")

# Modelos de datos
class LoginData(BaseModel):
    username: str
    password: str

class Orden(BaseModel):
    id: Optional[int] = None
    cliente: str
    equipo: str
    falla: str
    estado: str = "INGRESADO"
    presupuesto: float = 0.0

# Base de datos en memoria para pruebas
db_ordenes = [
    {
        "id": 1,
        "cliente": "Juan Pérez",
        "equipo": "Smart TV Samsung 55\"",
        "falla": "No enciende, led de standby titila",
        "estado": "EN_REVISION",
        "presupuesto": 45000.0
    },
    {
        "id": 2,
        "cliente": "Carlos Gómez",
        "equipo": "PlayStation 5",
        "falla": "Apagado repentino a los 10 minutos de juego",
        "estado": "INGRESADO",
        "presupuesto": 0.0
    }
]

# Servir la interfaz web en la raíz
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

# Endpoints de la API
@app.post("/api/login")
async def login(credentials: LoginData):
    if credentials.username == "admin" and credentials.password == "admin123":
        return {"access_token": "token_demo_12345", "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales incorrectas"
    )

@app.get("/api/v1/verify-token")
async def verify_token():
    return {"status": "ok", "message": "Token válido"}

@app.get("/api/v1/ordenes", response_model=List[Orden])
async def get_ordenes():
    return db_ordenes

@app.post("/api/v1/ordenes", response_model=Orden)
async def create_orden(orden: Orden):
    new_id = len(db_ordenes) + 1 if db_ordenes else 1
    orden_dict = orden.dict()
    orden_dict["id"] = new_id
    db_ordenes.append(orden_dict)
    return orden_dict

@app.delete("/api/v1/ordenes/{item_id}")
async def delete_orden(item_id: int):
    global db_ordenes
    db_ordenes = [o for o in db_ordenes if o.get("id") != item_id]
    return {"message": f"Orden {item_id} eliminada correctamente"}