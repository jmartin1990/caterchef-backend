# BANCO DE PRUEBAS UNITARIAS AUTOMATIZADAS STANDARD

import pytest
from fastapi.testclient import TestClient
from main import app
from database import Base, engine 

# Forzamos la creación física de las tablas en el archivo compartido de pruebas
Base.metadata.create_all(bind=engine)

# Inicializamos el cliente de pruebas sobre la instancia nativa de la API
client = TestClient(app)

def test_estado_servidor():
    """
    1. Verificación del Endpoint Raíz (Sanity Check)
    """
    respuesta = client.get("/")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"mensaje": "API de CaterChef Fusion funcionando correctamente"}

def test_login_credenciales_invalidas():
    """
    2. Prueba de Seguridad Crítica (Fallo de Autenticación)
    """
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
    """
    respuesta = client.get("/api/me")
    assert respuesta.status_code == 401