import requests
import pandas as pd
from fastapi import HTTPException

from utils.serverCRUD import validar_token_con_tipo, server

def docente_promedios_grupo_one(docenteId: int, authorization: str, tipo_usuario: str):

    headers = {"Authorization": authorization}

    # 2. Obtener clases del docente
    url_clases = f"{server}/clase/docente/{docenteId}"
    response_clases = requests.get(url_clases, headers=headers)

    if response_clases.status_code != 200:
        raise HTTPException(status_code=500, detail="No se pudieron obtener las clases del docente")

    try:
        data_clases = response_clases.json()
    except ValueError:
        raise HTTPException(status_code=500, detail="Respuesta JSON inválida al obtener clases")

    if not isinstance(data_clases, list) or not data_clases:
        return {"mensaje": "El docente no tiene clases asignadas"}

    codigos_grupo = list(set(clase.get("grupo") for clase in data_clases if clase.get("grupo")))

    if not codigos_grupo:
        return {"mensaje": "No se encontraron códigos de grupo en las clases"}

    # 3. Obtener IDs de grupo
    ids_grupo = []
    for codigo in codigos_grupo:
        url_grupo = f"{server}/grupo/buscar/codigo/{codigo}"
        response_grupo = requests.get(url_grupo, headers=headers)

        if response_grupo.status_code == 200:
            try:
                grupo_data = response_grupo.json()
                if isinstance(grupo_data, list) and grupo_data:
                    grupo_id = grupo_data[0].get("id")
                    if grupo_id:
                        ids_grupo.append((codigo, grupo_id))
            except ValueError:
                continue

    if not ids_grupo:
        return {"mensaje": "No se encontraron IDs para los grupos del docente"}

    # 4. Obtener estudiantes por grupo
    estudiantes_total = []
    for codigo, grupo_id in ids_grupo:
        url_estudiantes = f"{server}/grupo-estudiante/grupo/{grupo_id}"
        response_estudiantes = requests.get(url_estudiantes, headers=headers)

        if response_estudiantes.status_code == 200:
            try:
                estudiantes = response_estudiantes.json()
                if isinstance(estudiantes, list):
                    for est in estudiantes:
                        est["grupo_codigo"] = codigo
                        est["grupo_id"] = grupo_id
                    estudiantes_total.extend(estudiantes)
            except ValueError:
                continue

    if not estudiantes_total:
        return {"mensaje": "No se encontraron estudiantes en los grupos del docente"}

    # 5. Obtener calificaciones por estudiante
    dfs_notas = []
    for est in estudiantes_total:
        estudiante_id = est.get("estudianteId")
        grupo_codigo = est.get("grupo_codigo")

        if not estudiante_id or not grupo_codigo:
            continue

        url_notas = f"{server}/calificacion/estudiante/{estudiante_id}"
        response_notas = requests.get(url_notas, headers=headers)

        if response_notas.status_code == 200:
            try:
                data = response_notas.json()
                if isinstance(data, list) and data:
                    df = pd.DataFrame(data)
                    if 'nota' in df.columns:
                        df["estudianteId"] = estudiante_id
                        df["grupo_codigo"] = grupo_codigo
                        dfs_notas.append(df)
            except ValueError:
                continue

    if not dfs_notas:
        return {"mensaje": "No hay calificaciones registradas para los estudiantes"}

    try:
        df_notas = pd.concat(dfs_notas, ignore_index=True)
    except ValueError:
        return {"mensaje": "Error al procesar las calificaciones"}

    if df_notas.empty or 'nota' not in df_notas.columns:
        return {"mensaje": "No se pudieron calcular promedios por falta de notas"}

    resumen = df_notas.groupby(["grupo_codigo", "estudianteId"]).agg(
        cantidad_notas=pd.NamedAgg(column="nota", aggfunc="count"),
        promedio_nota=pd.NamedAgg(column="nota", aggfunc="mean")
    ).reset_index()

    return resumen.to_dict(orient="records")
