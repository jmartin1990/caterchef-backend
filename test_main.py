# test_main.py
# =========================================================================
# PROYECTO TFG DAW: CaterChef Fusión
# BANCO DE PRUEBAS UNITARIAS AUTOMATIZADAS STANDARD (Sprint 6)
# =========================================================================

import pytest
from fastapi.testclient import TestClient
from main import app

# --- CONFIGURACIÓN PARA GITHUB ACTIONS Y SQLITE EN MEMORIA ---
from database import Base, engine 

# IMPORTACIÓN CRÍTICA: Forzamos la carga del modelo para que SQLAlchemy registre la tabla 'usuarios'
try:
    # Si tus modelos están en un archivo models.py, esto registrará todo automáticamente
    from models import UsuarioORM
except ImportError:
    # Si tu archivo ORM se llama diferente o está dentro de otra carpeta, 
    # desactiva o ajusta esta importación según tu estructura real.
    pass

# Forzamos la creación física de las tablas mapeadas en la base de datos temporal
Base.metadata.create_all(bind=engine)
# ====================================================================

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