# test_main.py
# =========================================================================
# PROYECTO TFG DAW: CaterChef Fusión
# BANCO DE PRUEBAS UNITARIAS AUTOMATIZADAS - ENTORNO AISLADO (CI/CD)
# =========================================================================

import pytest
from fastapi.testclient import TestClient
import unittest.mock as mock

# --- ESTRATEGIA DE DECOUPLED TESTING (TFG: Aislamiento de Entorno de Calidad) ---
# Forzamos un mock de la sesión de la base de datos antes de importar la app
# Esto evita que la máquina virtual de GitHub Actions intente conectar a Neon DB sin credenciales
with mock.patch("database.SessionLocal"), mock.patch("database.engine"):
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
    payload_falso = {
        "username": "usuario_fantasma_tfg@caterchef.com",
        "password": "PasswordIncorrecto123"
    }
    
    # Mockeamos el comportamiento interno del controlador de autenticación para que simule una denegación segura
    with mock.patch("main.db") as mock_db:
        # Simulamos que la consulta a la base de datos devuelve None (usuario no encontrado)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
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