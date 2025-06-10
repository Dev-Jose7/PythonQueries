import requests
import pandas as pd
from fastapi import HTTPException

from utils.serverCRUD import validar_token_con_tipo, server

def docente_obtener_estudiantes_en_riesgo_asistencia_two(docenteId: int, authorization: str, tipo_usuario: str):

    headers = {"Authorization": authorization}

    try:
        # Paso 1: Obtener clases del docente
        url_clases = f"{server}/clase/docente/{docenteId}"
        response_clases = requests.get(url_clases, headers=headers)
        if response_clases.status_code != 200:
            raise HTTPException(status_code=500, detail="No se pudieron obtener las clases del docente")
        data_clases = response_clases.json()

        # Paso 2: Obtener código de grupo (usamos el primero que tenga grupo válido)
        codigoGrupo = None
        for clase in data_clases:
            if "grupo" in clase:
                codigoGrupo = clase["grupo"]
                break

        if not codigoGrupo:
            return {"mensaje": "No se encontró ningún grupo asignado al docente."}

        # Paso 3: Obtener grupo por código
        url_grupo = f"{server}/grupo/buscar/codigo/{codigoGrupo}"
        response_grupo = requests.get(url_grupo, headers=headers)
        if response_grupo.status_code != 200:
            raise HTTPException(status_code=500, detail="No se pudo obtener el grupo por código.")

        data_grupo = response_grupo.json()
        if not isinstance(data_grupo, list) or not data_grupo or 'id' not in data_grupo[0]:
            return {"mensaje": "No se encontró el grupo con el código especificado."}

        idGrupo = data_grupo[0]['id']

        # Paso 4: Obtener estudiantes del grupo
        url_estudiantes = f"{server}/grupo-estudiante/grupo/{idGrupo}"
        response_estudiantes = requests.get(url_estudiantes, headers=headers)

        if response_estudiantes.status_code != 200:
            raise HTTPException(status_code=500, detail="No se pudieron obtener los estudiantes del grupo.")

        data_estudiantes = response_estudiantes.json()
        if not isinstance(data_estudiantes, list) or not data_estudiantes:
            return {"mensaje": "No hay estudiantes asignados a este grupo."}

        df_estudiantes = pd.DataFrame(data_estudiantes)

        if 'estudianteId' not in df_estudiantes.columns:
            return {"mensaje": "La respuesta de estudiantes no contiene el campo 'estudianteId'."}

        lista_estudiantes_ids = df_estudiantes["estudianteId"].dropna().tolist()

        if not lista_estudiantes_ids:
            return {"mensaje": "No se encontraron IDs de estudiantes válidos."}

        # Paso 5: Obtener asistencias por estudiante
        df_Asistencias_total = []
        for estudianteId in lista_estudiantes_ids:
            url_asistencias = f"{server}/asistencia/estudiante/{estudianteId}"
            response = requests.get(url_asistencias, headers=headers)

            if response.status_code == 200:
                try:
                    data_asistencias = response.json()
                    if isinstance(data_asistencias, list) and data_asistencias:
                        df_asistencias = pd.DataFrame(data_asistencias)
                        if 'estado' in df_asistencias.columns:
                            df_asistencias["estudianteId"] = estudianteId
                            df_Asistencias_total.append(df_asistencias)
                except ValueError:
                    continue

        # Paso 6: Validar asistencias
        if not df_Asistencias_total:
            return {"mensaje": "No se encontraron asistencias para ningún estudiante."}

        try:
            df_final = pd.concat(df_Asistencias_total, ignore_index=True)
        except ValueError:
            return {"mensaje": "Error al procesar las asistencias."}

        if 'estado' not in df_final.columns or 'estudianteId' not in df_final.columns:
            return {"mensaje": "Las asistencias no tienen la estructura esperada."}

        # Paso 7: Filtrar inasistencias
        df_inasistencias = df_final[df_final["estado"] == "INASISTENCIA"]

        if df_inasistencias.empty:
            return {"mensaje": "Ningún estudiante tiene inasistencias registradas."}

        # Paso 8: Contar inasistencias por estudiante
        df_inasistencias_count = df_inasistencias.groupby("estudianteId").size().reset_index(name="cantidad_inasistencias")

        # Paso 9: Filtrar estudiantes en riesgo
        umbral = 1
        df_en_riesgo = df_inasistencias_count[df_inasistencias_count["cantidad_inasistencias"] > umbral]

        if df_en_riesgo.empty:
            return {"mensaje": "No hay estudiantes en riesgo de inasistencia."}

        return df_en_riesgo.to_dict(orient="records")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
