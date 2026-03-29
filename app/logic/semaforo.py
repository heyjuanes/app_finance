def obtener_semaforo(fondo_actual, meta_total=15000000):
    porcentaje = (fondo_actual / meta_total) * 100
    if porcentaje < 20:
        estado = "rojo"
        mensaje = "riesgo crítico, ajusta tus hábitos"
    elif porcentaje < 60:
        estado = "amarillo"
        mensaje = "vas bien, pero puedes acelerar"
    else:
        estado = "verde"
        mensaje = "vas en buen camino"
    return {"estado": estado, "mensaje": mensaje, "progreso": round(porcentaje, 1)}