import requests
import pandas as pd
from fastapi import HTTPException

from utils.serverCRUD import validar_token_con_tipo, server

def analizar_estudiante_two(id: int, authorization: str, tipo_usuario: str) -> dict:
    # 1. Validar token antes de continuar
    if not validar_token_con_tipo(authorization, tipo_usuario):
        raise HTTPException(status_code=403, detail="Token inválido o sin permisos para este tipo de usuario")

    # 2. Realizar petición autenticada
    endpoint = f"{server}/asistencia/estudiante/{id}"
    headers = {"Authorization": authorization}
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 204 or not response.content:
        return {}  # No hay contenido

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error al obtener asistencias del estudiante")

    try:
        data = response.json()
    except ValueError:
        raise HTTPException(status_code=500, detail="Respuesta JSON inválida")

    if not isinstance(data, list) or not data:
        return {}

    df = pd.DataFrame(data)

    if 'fecha' not in df.columns or 'estado' not in df.columns:
        return {}

    # Procesamiento
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    df = df.dropna(subset=['fecha'])

    inasistencias = df[df['estado'] == 'INASISTENCIA']
    if inasistencias.empty:
        return {}

    conteo_por_fecha = inasistencias.groupby('fecha').size()

    conteo_dict = {
        fecha.strftime('%Y-%m-%d'): int(cantidad)
        for fecha, cantidad in conteo_por_fecha.items()
    }

    return conteo_dict
