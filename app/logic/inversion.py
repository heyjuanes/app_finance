def calcular_cdt(capital, tasa_ea, meses=12):
    tasa_decimal = tasa_ea / 100
    monto_final = capital * (1 + tasa_decimal) ** (meses / 12)
    interes = monto_final - capital
    return {
        "capital": capital,
        "tasa": tasa_ea,
        "meses": meses,
        "interes_proyectado": round(interes),
        "monto_final": round(monto_final),
    }