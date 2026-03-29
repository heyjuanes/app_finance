from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class IngresoRequest(BaseModel):
    monto: float
    descripcion: Optional[str] = None

class GastoRequest(BaseModel):
    bolsillo: str
    monto: float
    descripcion: Optional[str] = None

class TransaccionResponse(BaseModel):
    id: int
    tipo: str
    bolsillo: Optional[str]
    monto: int
    descripcion: Optional[str]
    fecha: datetime

class DashboardResponse(BaseModel):
    fondo_migratorio: int
    meta_total: int
    progreso: float
    semaforo: dict
    bolsillos: list
    proyeccion_escenarios: dict
    cdt: dict
    dias_restantes: int