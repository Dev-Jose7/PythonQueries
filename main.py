from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from estudiantes.estudiante_one import analizar_estudiante_one
from estudiantes.estudiante_two import analizar_estudiante_two
from estudiantes.estudiante_three import analizar_calificaciones_estudiante_three

from docentes.docente_one import docente_promedios_grupo_one
from docentes.docente_two import docente_obtener_estudiantes_en_riesgo_asistencia_two
from docentes.docente_three import docentes_porcentajes_de_estado_por_grupo_three

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cesde-academic.netlify.app", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estudiante asistencia ONE (requiere token y tipo)
@app.get("/estudiantes/{id}/asistencias/one/{tipo}")
def get_estudiante_asistencias_one(
    id: int,
    tipo: str,
    authorization: str = Header(..., alias="Authorization")
):
    return analizar_estudiante_one(id, authorization, tipo)

# Estudiante asistencia TWO (requiere token y tipo)
@app.get("/estudiantes/{id}/asistencias/two/{tipo}")
def get_estudiantes_asistencias_two(
    id: int,
    tipo: str,
    authorization: str = Header(..., alias="Authorization")
):
    return analizar_estudiante_two(id, authorization, tipo)

# Estudiante calificaciones THREE (requiere token y tipo)
@app.get("/estudiantes/{id}/calificaciones/three/{tipo}")
def get_estudiante_calificaciones_three(
    id: int,
    tipo: str,
    authorization: str = Header(..., alias="Authorization")
):
    return analizar_calificaciones_estudiante_three(id, authorization, tipo)

# Docente notas grupo ONE (requiere token y tipo)
@app.get("/docentes/{id}/notas/one/{tipo}")
def get_docentes_notas_grupo_one(
    id: int,
    tipo: str,
    authorization: str = Header(..., alias="Authorization")
):
    return docente_promedios_grupo_one(id, authorization, tipo)

# Docente asistencia riesgo TWO (requiere token y tipo)
@app.get("/docentes/{id}/asistencia/two/{tipo}")
def get_docentes_riesgo_asistencia(
    id: int,
    tipo: str,
    authorization: str = Header(..., alias="Authorization")
):
    token = authorization.replace("Bearer ", "")
    return docente_obtener_estudiantes_en_riesgo_asistencia_two(id, token, tipo)

# Docente porcentaje estados asistencia THREE (requiere token y tipo)
@app.get("/docentes/{id}/asistencias/porcentajes/three/{tipo}")
def get_porcentaje_estado_asistencias_three(
    id: int,
    tipo: str,
    authorization: str = Header(..., alias="Authorization")
):
    token = authorization.replace("Bearer ", "")
    return docentes_porcentajes_de_estado_por_grupo_three(id, token, tipo)

# Servidor Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
