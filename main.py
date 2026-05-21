from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String, Numeric, Boolean, TIMESTAMP, func, Date, ForeignKey, Text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime, timedelta, timezone 
from database import Base, get_db

# --- LIBRERÍAS DE AUTENTICACIÓN Y SEGURIDAD ---
from passlib.context import CryptContext
import jwt
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

app = FastAPI(title="CaterChef Fusion API")

# --- CONFIGURACIÓN PARA JWT Y HASHEO ---
SECRET_KEY = "clave_super_secreta_para_el_tfg_de_daw"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- MIDDLEWARE OAUTH2: Desactivamos el auto_error para dar soporte legítimo a Invitados ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)

# --- Esquemas de validación (Pydantic / DTOs) ---
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
    apellidos: str | None = None 
    email: str
    password: str
    telefono: str 
    acepta_privacidad: bool # --- Validación obligatoria de conformidad RGPD ---

# --- NUEVO: ESQUEMAS PARA LA EXTRANET DE CLIENTE (TFG: Modificación de Datos) ---
class PerfilUpdate(BaseModel):
    nombre: str
    apellidos: Optional[str] = None
    telefono: str

class PasswordUpdate(BaseModel):
    password_actual: str
    password_nueva: str

# --- DTO PARA AUDITORÍA DE CREDENCIALES (TFG: Opción 5 - Flujo de Seguridad) ---
class RecuperarPasswordRequest(BaseModel):
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str

# --- ESQUEMAS PARA PROCESAR EL CHECKOUT REAL (TFG: Opción 3 - Estructuras de Datos Compuestas) ---
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
    notas_cliente: Optional[str] = None # Corregido para coincidir con la DB y Next.js

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Modelos de Base de Datos (ORM - SQLAlchemy) ---
class PlatoORM(Base):
    __tablename__ = "platos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150))
    descripcion = Column(String)
    precio = Column(Numeric(10, 2))
    categoria = Column(String(100))
    alergenos = Column(String(255))
    disponible = Column(Boolean, default=True)

class ListaEsperaORM(Base):
    __tablename__ = "lista_espera"
    id = Column(Integer, primary_key=True, index=True)
    plato_id = Column(Integer)
    email_usuario = Column(String(255))
    fecha_solicitud = Column(TIMESTAMP, server_default=func.now())

class ReservaORM(Base):
    __tablename__ = "reservas_chef"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150))
    email = Column(String(255))
    fecha = Column(Date)
    tipo_evento = Column(String(100))
    tipo_chef = Column(String(100))
    comensales = Column(Integer)
    fecha_solicitud = Column(TIMESTAMP, server_default=func.now())

class UsuarioORM(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100))
    apellidos = Column(String(150))
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    rol = Column(String(50), default="cliente")
    activo = Column(Boolean, default=True)
    telefono = Column(String(20), nullable=True) 
    acepta_privacidad = Column(Boolean, default=False) 
    creado_en = Column(TIMESTAMP, server_default=func.now())

# --- MODELOS ORM ACOPLADOS A NEON DB (TFG: Relaciones de Entidad e Integridad Referencial) ---
class PedidoORM(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=True) 
    tipo_servicio = Column(String(50), nullable=False)
    fecha_servicio = Column(TIMESTAMP, nullable=False)
    estado = Column(String(50), default="pendiente_pago")
    total = Column(Numeric(10, 2), nullable=False, default=0.00)
    direccion_calle = Column(String(255), nullable=False)
    ciudad = Column(String(100), nullable=False)
    codigo_postal = Column(String(10), nullable=False)
    provincia = Column(String(50), nullable=False)
    distrito = Column(String(100), nullable=False) 
    telefono = Column(String(20), nullable=False) 
    notas_cliente = Column(Text)
    creado_en = Column(TIMESTAMP, server_default=func.now())

class DetallePedidoORM(Base):
    __tablename__ = "detalles_pedido"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"))
    plato_id = Column(Integer, ForeignKey("platos.id", ondelete="RESTRICT"))
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)

# --- MÉTODOS DE SERVICIO AUXILIARES (SEGURIDAD Y CIFRADO) ---
def obtener_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verificar_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def crear_token_acceso(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- MIDDLEWARE INYECTOR DE DEPENDENCIA ADAPTADO A FLUJO DE INVITADOS ---
def obtener_usuario_actual(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Si no se suministra un token de cabecera, retorna None permitiendo el paso de Invitados. Si expira o es corrupto lanza 401."""
    if not token:
        return None 
        
    excepcion_credenciales = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la sesión o el token ha expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise excepcion_credenciales
    except jwt.PyJWTError:
        raise excepcion_credenciales
    
    usuario = db.query(UsuarioORM).filter(UsuarioORM.email == email).first()
    if usuario is None:
        raise excepcion_credenciales
    return usuario

# --- Rutas (Endpoints) ---

@app.get("/")
def estado_servidor():
    return {"mensaje": "API de CaterChef Fusion funcionando correctamente"}

@app.get("/api/platos")
def obtener_platos(db: Session = Depends(get_db)):
    return db.query(PlatoORM).all()

@app.post("/api/lista-espera")
def crear_solicitud(solicitud: ListaEsperaCreate, db: Session = Depends(get_db)):
    try:
        nueva_solicitud = ListaEsperaORM(plato_id=solicitud.plato_id, email_usuario=solicitud.email_usuario)
        db.add(nueva_solicitud)
        db.commit()
        return {"mensaje": "Solicitud de aviso guardada"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/reservas")
def crear_reserva(reserva: ReservaCreate, db: Session = Depends(get_db)):
    try:
        nueva_reserva = ReservaORM(**reserva.model_dump())
        db.add(nueva_reserva)
        db.commit()
        return {"mensaje": "Reserva confirmada"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/registro", response_model=Token)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    usuario_existente = db.query(UsuarioORM).filter(UsuarioORM.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="Este email ya está registrado")
    
    hashed_password = obtener_password_hash(usuario.password)
    
    nuevo_usuario = UsuarioORM(
        nombre=usuario.nombre, 
        apellidos=usuario.apellidos, 
        email=usuario.email,
        password_hash=hashed_password, 
        rol="cliente", 
        activo=True, 
        telefono=usuario.telefono,
        acepta_privacidad=usuario.acepta_privacidad
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    access_token = crear_token_acceso(data={"sub": nuevo_usuario.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(UsuarioORM).filter(UsuarioORM.email == form_data.username).first()
    if not usuario or not verificar_password(form_data.password, usuario.password_hash) or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email, contraseña incorrectos o cuenta inactiva",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = crear_token_acceso(data={"sub": usuario.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --- ACTUALIZADO: ENDPOINT DE PERFIL E INYECCIÓN DE DATOS PARA FORMULARIOS (Extranet) ---
@app.get("/api/me")
def obtener_perfil_actual(db: Session = Depends(get_db), usuario_actual: UsuarioORM = Depends(obtener_usuario_actual)):
    """Retorna los datos del usuario. Se añaden 'email' y 'telefono' para rellenar automáticamente la vista de Mi Cuenta."""
    if not usuario_actual:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ausente o sesión inválida."
        )
    
    total_pedidos = db.query(PedidoORM).filter(PedidoORM.usuario_id == usuario_actual.id).count()
    
    return {
        "nombre": usuario_actual.nombre,
        "apellidos": usuario_actual.apellidos,
        "email": usuario_actual.email,       # Añadido para el panel "Mi Cuenta"
        "telefono": usuario_actual.telefono, # Añadido para el panel "Mi Cuenta"
        "rol": usuario_actual.rol,
        "es_primera_compra": total_pedidos == 0 
    }

# --- NUEVAS RUTAS: EXTRANET DEL CLIENTE (TFG: Panel de Auto-Gestión y Seguridad) ---
@app.get("/api/reservas/me")
def obtener_mis_reservas(db: Session = Depends(get_db), usuario_actual: UsuarioORM = Depends(obtener_usuario_actual)):
    """Busca las solicitudes de Chef Privado aislando los datos por el email del usuario activo."""
    if not usuario_actual:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Se requiere sesión activa.")
    
    return db.query(ReservaORM).filter(ReservaORM.email == usuario_actual.email).order_by(ReservaORM.fecha_solicitud.desc()).all()

@app.put("/api/me")
def actualizar_perfil(perfil: PerfilUpdate, db: Session = Depends(get_db), usuario_actual: UsuarioORM = Depends(obtener_usuario_actual)):
    """Actualiza la información básica del usuario (nombre, apellidos, teléfono)."""
    if not usuario_actual:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Se requiere sesión activa.")
    
    usuario_actual.nombre = perfil.nombre
    usuario_actual.apellidos = perfil.apellidos
    usuario_actual.telefono = perfil.telefono
    db.commit()
    return {"mensaje": "Perfil actualizado correctamente"}

@app.put("/api/me/password")
def actualizar_password(datos: PasswordUpdate, db: Session = Depends(get_db), usuario_actual: UsuarioORM = Depends(obtener_usuario_actual)):
    """Valida la contraseña vigente y re-encripta la nueva contraseña en Neon DB."""
    if not usuario_actual:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Se requiere sesión activa.")
    
    if not verificar_password(datos.password_actual, usuario_actual.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La contraseña actual es incorrecta.")
    
    usuario_actual.password_hash = obtener_password_hash(datos.password_nueva)
    db.commit()
    return {"mensaje": "Contraseña actualizada de forma segura"}

@app.post("/api/recuperar-password")
def recuperar_password(solicitud: RecuperarPasswordRequest, db: Session = Depends(get_db)):
    """Flujo seguro de recuperación: Valida la existencia en Neon DB y emula el despacho TLS/SMTP por consola."""
    usuario = db.query(UsuarioORM).filter(UsuarioORM.email == solicitud.email).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se ha encontrado ninguna cuenta vinculada a este correo electrónico."
        )
    
    print(f"\n================ [SMTP OUTBOUND SIMULATOR] ================")
    print(f"DESTINATARIO: {usuario.email}")
    print(f"ASUNTO: Restablecimiento de contraseña - CaterChef Fusión")
    print(f"TOKEN TEMPORAL GENERADO: temporal_tfg_{func.now()}")
    print(f"ESTADO: Canal TLS de pruebas completado con éxito")
    print(f"===========================================================\n")
    
    return {"mensaje": "Instrucciones de recuperación despachadas."}

# --- ENDPOINTS TRANSACCIONALES Y PROTEGIDOS (TFG: Lógica de Compra y Roles Administrativos) ---
@app.post("/api/pedidos")
def crear_pedido(pedido: PedidoCreate, db: Session = Depends(get_db), usuario_actual: Optional[UsuarioORM] = Depends(obtener_usuario_actual)):
    """Transacción relacional atómica en dos pasos: Registra cabecera (mapeando si es usuario o invitado) e inserta detalles."""
    try:
        id_usuario = usuario_actual.id if usuario_actual else None

        nuevo_pedido = PedidoORM(
            usuario_id=id_usuario,
            tipo_servicio=pedido.tipo_servicio,
            fecha_servicio=pedido.fecha_servicio,
            total=pedido.total,
            direccion_calle=pedido.direccion_calle,
            ciudad=pedido.ciudad,
            codigo_postal=pedido.codigo_postal,
            provincia=pedido.provincia,
            distrito=pedido.distrito,   
            telefono=pedido.telefono,   
            notas_cliente=pedido.notas_cliente
        )
        db.add(nuevo_pedido)
        db.flush() 

        for item in pedido.items:
            detalle = DetallePedidoORM(
                pedido_id=nuevo_pedido.id,
                plato_id=item.plato_id,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario
            )
            db.add(detalle)
        
        db.commit() 
        return {"mensaje": "Pedido procesado correctamente", "pedido_id": nuevo_pedido.id}
    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=400, detail=f"No se pudo completar el pedido: {str(e)}")

@app.get("/api/pedidos/me")
def obtener_mis_pedidos(db: Session = Depends(get_db), usuario_actual: UsuarioORM = Depends(obtener_usuario_actual)):
    """Retorna únicamente los tickets asociados al ID del cliente autenticado mediante su JWT."""
    if not usuario_actual:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere sesión activa para consultar el historial."
        )
    return db.query(PedidoORM).filter(PedidoORM.usuario_id == usuario_actual.id).order_by(PedidoORM.creado_en.desc()).all()

@app.get("/api/admin/pedidos")
def obtener_todos_los_pedidos(db: Session = Depends(get_db), usuario_actual: Optional[UsuarioORM] = Depends(obtener_usuario_actual)):
    """Control de acceso basado en roles (RBAC). Restringe accesos anónimos o clientes sin rol de administración."""
    if not usuario_actual or usuario_actual.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acceso restringido. Se requieren privilegios de administración."
        )
    return db.query(PedidoORM).order_by(PedidoORM.creado_en.desc()).all()