# schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

# =========================================================================
# --- Esquemas de validación (Pydantic v2 / DTOs - Data Transfer Objects) ---
# =========================================================================

# --- ESQUEMA DE SERIALIZACIÓN PARA EL CATÁLOGO GOURMET (TFG: Fase 2) ---
class PlatoResponse(BaseModel):
    """Garantiza el contrato de API enviando de forma segura las URLs multimedia a Next.js"""
    id: int
    nombre: str
    descripcion: str
    precio: float
    categoria: str
    alergenos: str
    disponible: bool
    imagen_url: Optional[str] = None  # 👈 Incorporación de metadatos multimedia

    class Config:
        # Permite a Pydantic leer los atributos directamente desde el modelo ORM de SQLAlchemy
        from_attributes = True

class ListaEsperaCreate(BaseModel):
    plato_id: int
    email_usuario: str

class ReservaCreate(BaseModel):
    nombre: str
    email: str
    fecha: date
    tipo_evento: str
    tipo_chef: str
    comensales: int

class UsuarioCreate(BaseModel):
    nombre: str
    apellidos: Optional[str] = None 
    email: str
    password: str
    telefono: str 
    acepta_privacidad: bool # --- Validación obligatoria de conformidad RGPD ---

# --- EXTRANET DE CLIENTE: Modificación de Datos Perfil ---
class PerfilUpdate(BaseModel):
    nombre: str
    apellidos: Optional[str] = None
    telefono: str

class PasswordUpdate(BaseModel):
    password_actual: str
    password_nueva: str

# --- GESTIÓN OPERATIVA EN PANEL DE ADMINISTRACIÓN ---
class EstadoPedidoUpdate(BaseModel):
    """DTO para validar el payload de mutación de estado enviado desde el Dashboard de Next.js"""
    estado: str

# --- AUDITORÍA DE CREDENCIALES ---
class RecuperarPasswordRequest(BaseModel):
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str

# --- CHECKOUT REAL: Estructuras de Datos Compuestas ---
class ItemCarritoCreate(BaseModel):
    plato_id: int
    cantidad: int
    precio_unitario: float

class PedidoCreate(BaseModel):
    items: List[ItemCarritoCreate]
    total: float
    tipo_servicio: str
    fecha_servicio: datetime
    direccion_calle: str
    provincia: str 
    ciudad: str
    distrito: str 
    telefono: str 
    codigo_postal: str
    notes_cliente: Optional[str] = None 
    
    # --- NUEVO: PROPIEDADES DE IDENTIFICACIÓN LOGÍSTICA PARA INVITADOS (TFG: Desacoplamiento Híbrido) ---
    # Al definirse como opcionales con valor None, no rompen las peticiones de los usuarios logueados
    nombre_invitado: Optional[str] = None
    apellidos_invitado: Optional[str] = None
    email_invitado: Optional[str] = None

# --- GESTIÓN DE ATENCIÓN AL CLIENTE ---
class ContactoCreate(BaseModel):
    """DTO para validar y tipar de forma estricta los leads entrantes del formulario de contacto"""
    nombre: str
    email: str
    telefono: Optional[str] = None
    numero_pedido: Optional[str] = None 
    tipo_evento: Optional[str] = None
    mensaje: str
    acepta_privacidad: bool   # --- Fuerza la validación explícita del consentimiento RGPD ---
    accepta_comerciales: bool  # --- Almacena la conformidad o rechazo de campañas de marketing ---