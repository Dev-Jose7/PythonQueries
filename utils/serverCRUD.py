import requests;

server = "https://cesde-academic-app-production.up.railway.app"

def validar_token_con_tipo(token: str, tipo_usuario: str) -> bool:
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        response = requests.get(f"{server}/auth/validate/{tipo_usuario}", headers=headers)
        print("Respuesta", response)
        return response.status_code == 200
    except Exception as e:
        print(f"Error al validar token: {e}")
        return False