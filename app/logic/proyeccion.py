def calcular_tiempo_restante(meta_total, fondo_actual, tasa_ahorro_mensual):
    if tasa_ahorro_mensual <= 0:
        return "No estimado"
    monto_faltante = max(meta_total - fondo_actual, 0)
    meses = monto_faltante / tasa_ahorro_mensual
    return round(meses, 1)

def generar_escenarios(fondo_actual, meta_total=15000000, tasa_actual_mensual=500000):
    escenarios = {
        "conservador": tasa_actual_mensual * 0.8,
        "actual": tasa_actual_mensual,
        "optimo": tasa_actual_mensual * 1.2,
    }
    resultado = {}
    for nombre, tasa in escenarios.items():
        meses = calcular_tiempo_restante(meta_total, fondo_actual, tasa)
        resultado[nombre] = meses
    return resultado