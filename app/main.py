from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from app.logic import bolsillos, proyeccion, semaforo, inversion

class IngresoRequest(BaseModel):
    monto: float

class GastoRequest(BaseModel):
    bolsillo: str
    monto: float

class DashboardResponse(BaseModel):
    fondo_migratorio: float
    meta_total: float
    progreso: float
    semaforo: dict
    bolsillos: list
    proyeccion_escenarios: dict
    cdt: dict
    dias_restantes: int

app = FastAPI(title="Sistema Financiero Migratorio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

estado_usuario = {
    "fondo_migratorio": 4_200_000,
    "saldo_bolsillos": {
        "migracion": 4_200_000,
        "vida_diaria": 1_200_000,
        "liquidez": 240_000,
        "disfrute": 120_000,
    },
    "ultimo_ingreso_mensual": 2_400_000,
}

@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    meta_total = 15_000_000
    fondo_actual = estado_usuario["fondo_migratorio"]

    semaforo_info = semaforo.obtener_semaforo(fondo_actual, meta_total)
    bolsillos_info = bolsillos.obtener_estado_bolsillos(estado_usuario["saldo_bolsillos"])
    
    tasa_ahorro_mensual = estado_usuario["saldo_bolsillos"].get("migracion", 0) * 0.7
    if tasa_ahorro_mensual <= 0:
        tasa_ahorro_mensual = 500_000
    proyecciones = proyeccion.generar_escenarios(fondo_actual, meta_total, tasa_ahorro_mensual)
    
    cdt_info = inversion.calcular_cdt(capital=1_500_000, tasa_ea=12.4, meses=12)
    
    meses_actual = proyecciones.get("actual", 0)
    if isinstance(meses_actual, (int, float)):
        dias_restantes = round(meses_actual * 30)
    else:
        dias_restantes = 0

    return DashboardResponse(
        fondo_migratorio=fondo_actual,
        meta_total=meta_total,
        progreso=round((fondo_actual / meta_total) * 100, 1),
        semaforo=semaforo_info,
        bolsillos=bolsillos_info["bolsillos"],
        proyeccion_escenarios=proyecciones,
        cdt=cdt_info,
        dias_restantes=dias_restantes,
    )

@app.post("/ingreso")
async def registrar_ingreso(ingreso: IngresoRequest):
    if ingreso.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a cero")
    
    distribucion = bolsillos.distribuir_ingreso(ingreso.monto)
    
    for bolsillo, monto in distribucion.items():
        estado_usuario["saldo_bolsillos"][bolsillo] = estado_usuario["saldo_bolsillos"].get(bolsillo, 0) + monto
    
    estado_usuario["fondo_migratorio"] = estado_usuario["saldo_bolsillos"]["migracion"]
    estado_usuario["ultimo_ingreso_mensual"] = ingreso.monto
    
    return {"status": "ok", "distribucion": distribucion}

@app.post("/gasto")
async def registrar_gasto(gasto: GastoRequest):
    if gasto.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a cero")
    
    if gasto.bolsillo not in estado_usuario["saldo_bolsillos"]:
        raise HTTPException(status_code=400, detail=f"Bolsillo {gasto.bolsillo} no válido")
    
    if estado_usuario["saldo_bolsillos"][gasto.bolsillo] < gasto.monto:
        raise HTTPException(status_code=400, detail="Fondos insuficientes en el bolsillo")
    
    estado_usuario["saldo_bolsillos"][gasto.bolsillo] -= gasto.monto
    
    if gasto.bolsillo == "migracion":
        estado_usuario["fondo_migratorio"] = estado_usuario["saldo_bolsillos"]["migracion"]
    
    return {"status": "ok", "nuevo_saldo": estado_usuario["saldo_bolsillos"][gasto.bolsillo]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)