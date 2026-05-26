# test_main.py
# =========================================================================
# PROYECTO TFG DAW: CaterChef Fusión
# BANCO DE PRUEBAS UNITARIAS AUTOMATIZADAS (Sprint 6)
# =========================================================================

import pytest
from fastapi.testclient import TestClient
from main import app

# Inicializamos el cliente de pruebas sobre la instancia nativa de la API
client = TestClient(app)

def test_estado_servidor():
    """
    1. Verificación del Endpoint Raíz (Sanity Check)
    Comprueba que el orquestador responde correctamente y el servidor está operativo.
    """
    respuesta = client.get("/")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"mensaje": "API de CaterChef Fusion funcionando correctamente"}

def test_login_credenciales_invalidas():
    """
    2. Prueba de Seguridad Crítica (Fallo de Autenticación)
    Verifica que el middleware OAuth2 bloquea el acceso si el usuario o contraseña no existen.
    """
    # Simulamos el envío del formulario estructurado x-www-form-urlencoded
    payload_falso = {
        "username": "usuario_fantasma_tfg@caterchef.com",
        "password": "PasswordIncorrecto123"
    }
    respuesta = client.post("/api/login", data=payload_falso)
    
    # Debe denegar el acceso con un error HTTP 401 Unauthorized
    assert respuesta.status_code == 401
    assert "incorrectos" in respuesta.json()["detail"]

def test_obtener_perfil_sin_token():
    """
    3. Prueba de Control de Acceso (Rutas Protegidas)
    Verifica que el endpoint /api/me bloquea a peticiones que omitan la cabecera 'Authorization'.
    """
    respuesta = client.get("/api/me")
    
    # Al no inyectar un Bearer Token JWT válido, el sistema debe responder 401
    assert respuesta.status_code == 401