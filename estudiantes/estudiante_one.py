import requests
import pandas as pd

from fastapi import HTTPException

from utils.serverCRUD import validar_token_con_tipo
from utils.serverCRUD import server

def analizar_estudiante_one(id: int, token: str, tipo_usuario: str) -> dict:
    # Validar token antes de continuar
    if not validar_token_con_tipo(token, tipo_usuario):
        raise HTTPException(status_code=403, detail="Token inválido o sin permisos para este tipo de usuario")

    # Realizar petición a la API de asistencia con el token
    endpoint = f"{server}/asistencia/estudiante/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 204 or not response.content:
        return {}

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error al obtener datos de asistencia")

    try:
        data = response.json()
    except ValueError:
        raise HTTPException(status_code=500, detail="Respuesta JSON inválida")

    if not isinstance(data, list) or not data:
        return {}

    df = pd.DataFrame(data)

    if 'fecha' not in df.columns or 'estado' not in df.columns:
        return {}

    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    df = df.dropna(subset=['fecha'])

    inicio = pd.Timestamp('2025-01-01')
    fin = pd.Timestamp('2025-06-30')
    df_filtrado = df[(df['fecha'] >= inicio) & (df['fecha'] <= fin)]

    conteo_estados = df_filtrado['estado'].value_counts().to_dict()

    return conteo_estados
