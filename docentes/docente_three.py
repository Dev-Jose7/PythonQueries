import requests
import pandas as pd
from fastapi import HTTPException

from utils.serverCRUD import validar_token_con_tipo, server

def docentes_porcentajes_de_estado_por_grupo_three(docenteId: int, authorization: str, tipo_usuario: str):

    headers = {"Authorization": authorization}

    try:
        # Paso 1: Obtener clases del docente
        url_clases = f"{server}/clase/docente/{docenteId}"
        response_clases = requests.get(url_clases, headers=headers)
        if response_clases.status_code != 200:
            raise HTTPException(status_code=500, detail="No se pudieron obtener las clases del docente.")
        data_clases = response_clases.json()

        # Paso 2: Tomar el primer grupo válido encontrado
        codigo_grupo = None
        for clase in data_clases:
            if "grupo" in clase:
                codigo_grupo = clase["grupo"]
                break

        if not codigo_grupo:
            return {"mensaje": "No se encontró ningún grupo asignado al docente."}

        # Paso 3: Buscar grupo por código
        url_grupo_codigo = f"{server}/grupo/buscar/codigo/{codigo_grupo}"
        response_grupo = requests.get(url_grupo_codigo, headers=headers)
        if response_grupo.status_code != 200:
            return {"mensaje": "No se pudo encontrar el grupo con el código proporcionado."}

        data_grupo = response_grupo.json()
        if not isinstance(data_grupo, list) or not data_grupo or 'id' not in data_grupo[0]:
            return {"mensaje": "El grupo no contiene un ID válido."}

        id_grupo = data_grupo[0]['id']

        # Paso 4: Obtener estudiantes del grupo
        url_estudiantes = f"{server}/grupo-estudiante/grupo/{id_grupo}"
        response_estudiantes = requests.get(url_estudiantes, headers=headers)
        if response_estudiantes.status_code != 200:
            return {"mensaje": "No se pudieron obtener los estudiantes del grupo."}

        data_estudiantes = response_estudiantes.json()
        if not isinstance(data_estudiantes, list) or not data_estudiantes:
            return {"mensaje": "No se encontraron estudiantes en el grupo."}

        df_estudiantes = pd.DataFrame(data_estudiantes)
        if 'estudianteId' not in df_estudiantes.columns:
            return {"mensaje": "Falta la columna 'estudianteId' en los datos de estudiantes."}

        lista_estudiantes_ids = df_estudiantes["estudianteId"].dropna().tolist()
        if not lista_estudiantes_ids:
            return {"mensaje": "No se encontraron IDs de estudiantes válidos."}

        # Paso 5: Obtener asistencias por estudiante
        df_asistencias_total = []
        for estudiante_id in lista_estudiantes_ids:
            url_asistencias = f"{server}/asistencia/estudiante/{estudiante_id}"
            response = requests.get(url_asistencias, headers=headers)
            if response.status_code == 200:
                try:
                    data_asistencias = response.json()
                    if isinstance(data_asistencias, list) and data_asistencias:
                        df = pd.DataFrame(data_asistencias)
                        if 'estado' in df.columns:
                            df["estudianteId"] = estudiante_id
                            df_asistencias_total.append(df)
                except ValueError:
                    continue  # JSON inválido

        if not df_asistencias_total:
            return {"mensaje": "No se encontraron registros de asistencia para ningún estudiante."}

        try:
            df_final = pd.concat(df_asistencias_total, ignore_index=True)
        except ValueError:
            return {"mensaje": "Error al unir los datos de asistencia."}

        if df_final.empty or 'estado' not in df_final.columns:
            return {"mensaje": "No hay datos suficientes o falta la columna 'estado'."}

        # Paso 6: Calcular porcentaje por estado
        conteo_estados = df_final["estado"].value_counts(normalize=True) * 100
        conteo_estados = conteo_estados.round(2)

        return conteo_estados.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
