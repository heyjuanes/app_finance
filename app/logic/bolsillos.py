PORCENTAJES = {
    "migracion": 0.35,
    "vida_diaria": 0.50,
    "liquidez": 0.10,
    "disfrute": 0.05,
}

def distribuir_ingreso(ingreso_mensual):
    if ingreso_mensual <= 0:
        return {nombre: 0 for nombre in PORCENTAJES}
    
    distribucion = {}
    for nombre, porcentaje in PORCENTAJES.items():
        distribucion[nombre] = round(ingreso_mensual * porcentaje)
    
    total_distribuido = sum(distribucion.values())
    if total_distribuido != ingreso_mensual:
        diferencia = ingreso_mensual - total_distribuido
        distribucion["migracion"] += diferencia
    
    return distribucion

def obtener_estado_bolsillos(saldo_actual):
    return {
        "bolsillos": [
            {"nombre": "Migración", "monto": saldo_actual.get("migracion", 0), "porcentaje": 35},
            {"nombre": "Vida Diaria", "monto": saldo_actual.get("vida_diaria", 0), "porcentaje": 50},
            {"nombre": "Liquidez", "monto": saldo_actual.get("liquidez", 0), "porcentaje": 10},
            {"nombre": "Disfrute", "monto": saldo_actual.get("disfrute", 0), "porcentaje": 5},
        ]
    }