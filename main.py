from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import io
from datetime import datetime

app = FastAPI(title="API Servidor Taller Control v3.3", version="3.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
DB_SERVER = "servidor_taller.db"

def init_server_db():
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        can_download INTEGER DEFAULT 1
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS tokens_activos (
        token TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        can_download INTEGER DEFAULT 1
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS firmwares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        modelo TEXT NOT NULL,
        chasis TEXT NOT NULL,
        filename TEXT NOT NULL
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS ordenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT NOT NULL,
        equipo TEXT NOT NULL,
        falla TEXT,
        estado TEXT DEFAULT 'Ingresado',
        presupuesto REAL DEFAULT 0.0,
        notas TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS placas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_main TEXT NOT NULL,
        tv_modelo TEXT,
        panel TEXT,
        ubicacion TEXT,
        estado TEXT DEFAULT 'Probada OK',
        notas TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS componentes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT NOT NULL,
        codigo TEXT NOT NULL,
        ubicacion TEXT,
        cantidad INTEGER DEFAULT 1,
        notas TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS caja (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        tipo TEXT NOT NULL,
        concepto TEXT NOT NULL,
        monto REAL DEFAULT 0.0
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto TEXT NOT NULL,
        precio REAL DEFAULT 0.0,
        estado TEXT DEFAULT 'En Venta',
        notas TEXT
    )''')

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (username, password, can_download) VALUES (?, ?, ?)", ("admin", "1234", 1))

    cursor.execute("SELECT COUNT(*) FROM firmwares")
    if cursor.fetchone()[0] == 0:
        firmwares_iniciales = [
            ("Smart TV BGH 50 4K (B5019US6A)", "RSAG7.820.8339", "BGH_50_4K_RSAG78208339_Dump.bin"),
            ("Philips 43PFG5102/77", "715G8524-M01-000-004K", "Philips_43PFG5102_NAND_eMMC.bin"),
            ("TCL L40S6500", "RT41K", "TCL_L40S6500_RT41K_PKG.bin"),
            ("Noblex DK50X6500", "RSAG7.820.8752", "Noblex_DK50X6500_Main.bin")
        ]
        cursor.executemany("INSERT INTO firmwares (modelo, chasis, filename) VALUES (?, ?, ?)", firmwares_iniciales)

    conn.commit()
    conn.close()

init_server_db()

# ==================== MODELOS PYDANTIC ====================
class LoginRequest(BaseModel):
    username: str
    password: str

class OrdenCreate(BaseModel):
    cliente: str
    equipo: str
    falla: str
    estado: str
    presupuesto: float

class PlacaCreate(BaseModel):
    codigo_main: str
    tv_modelo: str
    panel: str
    ubicacion: str
    estado: str

class ComponenteCreate(BaseModel):
    categoria: str
    codigo: str
    ubicacion: str
    cantidad: int

class CajaCreate(BaseModel):
    tipo: str
    concepto: str
    monto: float

class VentaCreate(BaseModel):
    producto: str
    precio: float
    estado: str

# ==================== ENDPOINTS AUTENTICACIÓN ====================
@app.post("/api/login")
def login(credentials: LoginRequest):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("SELECT username, can_download FROM usuarios WHERE username=? AND password=?", (credentials.username, credentials.password))
    user = cursor.fetchone()

    if user:
        username, can_dl = user[0], bool(user[1])
        token_generado = f"TOKEN_BEARER_{username.upper()}_2026"
        cursor.execute("INSERT OR REPLACE INTO tokens_activos (token, username, can_download) VALUES (?, ?, ?)", (token_generado, username, int(can_dl)))
        conn.commit()
        conn.close()
        return {"status": "success", "token": token_generado, "usuario": username, "can_download": can_dl}

    conn.close()
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

@app.get("/api/v1/verify-token")
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("SELECT username, can_download FROM tokens_activos WHERE token=?", (token,))
    row = cursor.fetchone()
    conn.close()
    if row: return {"status": "valid", "usuario": row[0], "can_download": bool(row[1])}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

# ==================== ENDPOINTS ÓRDENES ====================
@app.get("/api/v1/ordenes")
def get_ordenes(credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cliente, equipo, falla, estado, presupuesto FROM ordenes ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "cliente": r[1], "equipo": r[2], "falla": r[3], "estado": r[4], "presupuesto": r[5]} for r in rows]

@app.post("/api/v1/ordenes")
def add_orden(data: OrdenCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ordenes (cliente, equipo, falla, estado, presupuesto, notas) VALUES (?, ?, ?, ?, ?, ?)",
                   (data.cliente, data.equipo, data.falla, data.estado, data.presupuesto, ""))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete("/api/v1/ordenes/{item_id}")
def delete_orden(item_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ordenes WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

# ==================== ENDPOINTS PLACAS ====================
@app.get("/api/v1/placas")
def get_placas(credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("SELECT id, codigo_main, tv_modelo, panel, ubicacion, estado FROM placas ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "codigo_main": r[1], "tv_modelo": r[2], "panel": r[3], "ubicacion": r[4], "estado": r[5]} for r in rows]

@app.post("/api/v1/placas")
def add_placa(data: PlacaCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO placas (codigo_main, tv_modelo, panel, ubicacion, estado, notas) VALUES (?, ?, ?, ?, ?, ?)",
                   (data.codigo_main, data.tv_modelo, data.panel, data.ubicacion, data.estado, ""))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete("/api/v1/placas/{item_id}")
def delete_placa(item_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM placas WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

# ==================== ENDPOINTS COMPONENTES ====================
@app.get("/api/v1/componentes")
def get_componentes(credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("SELECT id, categoria, codigo, ubicacion, cantidad FROM componentes ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "categoria": r[1], "codigo": r[2], "ubicacion": r[3], "cantidad": r[4]} for r in rows]

@app.post("/api/v1/componentes")
def add_componente(data: ComponenteCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO componentes (categoria, codigo, ubicacion, cantidad, notas) VALUES (?, ?, ?, ?, ?)",
                   (data.categoria, data.codigo, data.ubicacion, data.cantidad, ""))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete("/api/v1/componentes/{item_id}")
def delete_componente(item_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM componentes WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

# ==================== ENDPOINTS CAJA ====================
@app.get("/api/v1/caja")
def get_caja(credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("SELECT id, fecha, tipo, concepto, monto FROM caja ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "fecha": r[1], "tipo": r[2], "concepto": r[3], "monto": r[4]} for r in rows]

@app.post("/api/v1/caja")
def add_caja(data: CajaCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("INSERT INTO caja (fecha, tipo, concepto, monto) VALUES (?, ?, ?, ?)",
                   (fecha_actual, data.tipo, data.concepto, data.monto))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete("/api/v1/caja/{item_id}")
def delete_caja(item_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM caja WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

# ==================== ENDPOINTS VENTAS ====================
@app.get("/api/v1/ventas")
def get_ventas(credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("SELECT id, producto, precio, estado FROM ventas ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "producto": r[1], "precio": r[2], "estado": r[3]} for r in rows]

@app.post("/api/v1/ventas")
def add_venta(data: VentaCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ventas (producto, precio, estado, notas) VALUES (?, ?, ?, ?)",
                   (data.producto, data.precio, data.estado, ""))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete("/api/v1/ventas/{item_id}")
def delete_venta(item_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ventas WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

# ==================== ENDPOINTS FIRMWARES ====================
@app.get("/api/v1/firmwares")
def get_firmwares(credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("SELECT id, modelo, chasis, filename FROM firmwares ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "modelo": r[1], "chasis": r[2], "filename": r[3]} for r in rows]

@app.get("/api/v1/firmwares/download/{firmware_id}")
def download_firmware(firmware_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    conn = sqlite3.connect(DB_SERVER)
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM firmwares WHERE id=?", (firmware_id,))
    item = cursor.fetchone()
    conn.close()
    if not item: raise HTTPException(status_code=404, detail="No encontrado")

    filename = item[0]
    dummy_payload = b"\x7FELF\x01\x01\x01\x00" + (b"\x00" * (1024 * 1024))
    buffer = io.BytesIO(dummy_payload)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="{filename}"'})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)