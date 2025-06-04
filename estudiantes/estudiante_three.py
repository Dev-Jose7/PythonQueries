import requests
import pandas as pd
from fastapi import HTTPException

from utils.serverCRUD import validar_token_con_tipo, server

def analizar_calificaciones_estudiante_three(id: int, token: str, tipo_usuario: str) -> dict:
    # 1. Validar token
    if not validar_token_con_tipo(token, tipo_usuario):
        raise HTTPException(status_code=403, detail="Token inválido o sin permisos para este tipo de usuario")

    # 2. Consultar calificaciones
    endpoint = f"{server}/calificacion/estudiante/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 204 or not response.content:
        return {"mensaje": "No hay calificaciones registradas para el estudiante."}

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error al obtener calificaciones del estudiante")

    try:
        data = response.json()
    except ValueError:
        raise HTTPException(status_code=500, detail="Respuesta JSON inválida al obtener calificaciones")

    if not isinstance(data, list) or not data:
        return {"mensaje": "No hay calificaciones registradas para el estudiante."}

    # 3. Procesamiento con pandas
    df = pd.DataFrame(data)

    if 'fecha' not in df.columns or 'nota' not in df.columns or 'actividad' not in df.columns:
        return {"mensaje": "Datos incompletos: faltan columnas esperadas."}

    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    df = df.dropna(subset=['fecha'])

    if df.empty:
        return {"mensaje": "Las fechas de calificaciones no son válidas."}

    df = df.sort_values('fecha')

    resultado = df[['fecha', 'nota', 'actividad']].to_dict(orient='records')
    return resultado
