from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app import database
from app.logic import bolsillos, proyeccion, semaforo, inversion
from app.models import IngresoRequest, GastoRequest, DashboardResponse, TransaccionResponse

# Inicializar base de datos al arrancar
database.init_db()

app = FastAPI(title="Sistema Financiero Migratorio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Sistema Financiero Migratorio API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    "Obtiene el estado completo del dashboard"
    estado = database.cargar_estado()
    
    fondo_actual = database.obtener_fondo_migratorio()
    meta_total = estado["meta_total"]
    
    semaforo_info = semaforo.obtener_semaforo(fondo_actual, meta_total)
    
    bolsillos_data = [
        {"nombre": nombre.capitalize(), "monto": monto, "porcentaje": 35 if nombre == "migracion" else 50 if nombre == "vida_diaria" else 10 if nombre == "liquidez" else 5}
        for nombre, monto in estado["bolsillos"].items()
    ]
    
    tasa_ahorro = estado["bolsillos"].get("migracion", 0) * 0.7
    if tasa_ahorro <= 0:
        tasa_ahorro = 500_000
    
    proyecciones = proyeccion.generar_escenarios(fondo_actual, meta_total, tasa_ahorro)
    
    with database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT capital, tasa, meses FROM cdt 
            ORDER BY fecha_inicio DESC 
            LIMIT 1
        """)
        cdt_row = cursor.fetchone()
    
    if cdt_row:
        cdt_info = inversion.calcular_cdt(cdt_row["capital"], cdt_row["tasa"], cdt_row["meses"])
    else:
        cdt_info = {"capital": 0, "tasa": 0, "meses": 0, "interes_proyectado": 0, "monto_final": 0}
    
    meses_actual = proyecciones.get("actual", 0)
    dias_restantes = round(meses_actual * 30) if isinstance(meses_actual, (int, float)) else 0
    
    return DashboardResponse(
        fondo_migratorio=fondo_actual,
        meta_total=meta_total,
        progreso=round((fondo_actual / meta_total) * 100, 1),
        semaforo=semaforo_info,
        bolsillos=bolsillos_data,
        proyeccion_escenarios=proyecciones,
        cdt=cdt_info,
        dias_restantes=dias_restantes,
    )

@app.post("/ingreso")
async def registrar_ingreso(ingreso: IngresoRequest):
    "Registra un ingreso y lo distribuye automáticamente"
    if ingreso.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a cero")
    
    distribucion = bolsillos.distribuir_ingreso(ingreso.monto)
    
    with database.get_db() as conn:
        cursor = conn.cursor()
        for bolsillo, monto in distribucion.items():
            cursor.execute("""
                UPDATE bolsillos 
                SET monto = monto + ?, updated_at = CURRENT_TIMESTAMP
                WHERE nombre = ?
            """, (monto, bolsillo))
        
        cursor.execute("""
            UPDATE config 
            SET valor = ?, updated_at = CURRENT_TIMESTAMP
            WHERE clave = 'ultimo_ingreso_mensual'
        """, (str(ingreso.monto),))
        conn.commit()
    
    database.guardar_transaccion(
        tipo="ingreso",
        monto=ingreso.monto,
        descripcion=ingreso.descripcion
    )
    
    return {"status": "ok", "distribucion": distribucion}

@app.post("/gasto")
async def registrar_gasto(gasto: GastoRequest):
    "Registra un gasto descontando del bolsillo correspondiente"
    if gasto.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a cero")
    
    with database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT monto FROM bolsillos WHERE nombre = ?", (gasto.bolsillo,))
        resultado = cursor.fetchone()
        
        if not resultado:
            raise HTTPException(status_code=400, detail=f"Bolsillo {gasto.bolsillo} no válido")
        
        if resultado["monto"] < gasto.monto:
            raise HTTPException(status_code=400, detail="Fondos insuficientes en el bolsillo")
        
        cursor.execute("""
            UPDATE bolsillos 
            SET monto = monto - ?, updated_at = CURRENT_TIMESTAMP
            WHERE nombre = ?
        """, (gasto.monto, gasto.bolsillo))
        conn.commit()
    
    database.guardar_transaccion(
        tipo="gasto",
        bolsillo=gasto.bolsillo,
        monto=gasto.monto,
        descripcion=gasto.descripcion
    )
    
    return {"status": "ok"}

@app.get("/transacciones", response_model=list[TransaccionResponse])
async def get_transacciones(limite: int = 50):
    "Obtiene el historial de transacciones"
    return database.obtener_historial(limite)

@app.post("/cdt")
async def crear_cdt(capital: int, tasa: float, meses: int = 12):
    "Registra un nuevo CDT"
    if capital <= 0 or tasa <= 0:
        raise HTTPException(status_code=400, detail="Capital y tasa deben ser positivos")
    
    with database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cdt (capital, tasa, meses)
            VALUES (?, ?, ?)
        """, (capital, tasa, meses))
        conn.commit()
    
    return {"status": "ok", "cdt_id": cursor.lastrowid}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
