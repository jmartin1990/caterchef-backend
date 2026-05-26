# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta, timezone 
from database import get_db

# --- NUEVO: IMPORTACIÓN ATÓMICA DE MODELOS DESACOPLADOS (TFG: Patrón de Diseño Arquitectónico) ---
from models import (
    PlatoORM, ListaEsperaORM, ReservaORM, UsuarioORM, 
    PedidoORM, DetallePedidoORM, MensajeContactoORM
)

# --- IMPORTACIÓN MAESTRA DE ESQUEMAS MODULARES (TFG: Separación de Responsabilidades) ---
import schemas

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

# --- MIDDLEWARE OAUTH2 ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)


# --- CONFIGURACIÓN DE CORS PARA EL TFG (Seguridad de Orígenes Cruzados) ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.72:3000",  # IP de tu red local detectada por Next.js
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permite métodos estándar (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Permite adjuntar cabeceras como Content-Type o Authorization
)


# =========================================================================
# --- MÉTODOS DE SERVICIO AUXILIARES (SEGURIDAD Y CIFRADO) ---
# =========================================================================

def obtener_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verificar_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def crear_token_acceso(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def obtener_usuario_actual(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        return None 
        
    excepcion_credenciales = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
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

# =========================================================================
# --- CONTROLADORES / RUTAS DE LA API (Endpoints RESTful) ---
# =========================================================================

@app.get("/")
def estado_servidor():
    return {"mensaje": "API de CaterChef Fusion funcionando correctamente"}

@app.get("/api/platos", response_model=List[schemas.PlatoResponse])
def obtener_platos(db: Session = Depends(get_db)):
    return db.query(PlatoORM).all()

@app.post("/api/lista-espera")
def crear_solicitud(solicitud: schemas.ListaEsperaCreate, db: Session = Depends(get_db)):
    try:
        nueva_solicitud = ListaEsperaORM(plato_id=solicitud.plato_id, email_usuario=solicitud.email_usuario)
        db.add(nueva_solicitud)
        db.commit()
        return {"mensaje": "Solicitud de aviso guardada"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/reservas")
def crear_reserva(reserva: schemas.ReservaCreate, db: Session = Depends(get_db)):
    try:
        nueva_reserva = ReservaORM(**reserva.model_dump())
        db.add(nueva_reserva)
        db.commit()
        return {"mensaje": "Reserva confirmada"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/registro", response_model=schemas.Token)
def registrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
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

@app.post("/api/login", response_model=schemas.Token)
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

@app.get("/api/me")
def obtener_perfil_actual(db: Session = Depends(get_db), usuario_actual: UsuarioORM = Depends(obtener_usuario_actual)):
    if not usuario_actual:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente o sesión inválida.")
    
    total_pedidos = db.query(PedidoORM).filter(PedidoORM.usuario_id == usuario_actual.id).count()
    return {
        "nombre": usuario_actual.nombre,
        "apellidos": usuario_actual.apellidos,
        "email": usuario_actual.email,      
        "telefono": usuario_actual.telefono, 
        "rol": usuario_actual.rol,
        "es_primera_compra": total_pedidos == 0 
    }

@app.get("/api/reservas/me")
def obtener_mis_reservas(db: Session = Depends(get_db), usuario_actual: UsuarioORM = Depends(obtener_usuario_actual)):
    if not usuario_actual:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Se requiere sesión activa.")
    return db.query(ReservaORM).filter(ReservaORM.email == usuario_actual.email).order_by(ReservaORM.fecha_solicitud.desc()).all()

@app.put("/api/me")
def actualizar_perfil(perfil: schemas.PerfilUpdate, db: Session = Depends(get_db), usuario_actual: UsuarioORM = Depends(obtener_usuario_actual)):
    if not usuario_actual:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Se requiere sesión activa.")
    
    usuario_actual.nombre = perfil.nombre
    usuario_actual.apellidos = perfil.apellidos
    usuario_actual.telefono = perfil.telefono
    db.commit()
    return {"mensaje": "Perfil actualizado correctamente"}

@app.put("/api/me/password")
def actualizar_password(datos: schemas.PasswordUpdate, db: Session = Depends(get_db), usuario_actual: UsuarioORM = Depends(obtener_usuario_actual)):
    if not usuario_actual:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Se requiere sesión activa.")
    
    if not verificar_password(datos.password_actual, usuario_actual.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La contraseña actual es incorrecta.")
    
    usuario_actual.password_hash = obtener_password_hash(datos.password_nueva)
    db.commit()
    return {"mensaje": "Contraseña actualizada de forma segura"}

@app.post("/api/recuperar-password")
def recuperar_password(solicitud: schemas.RecuperarPasswordRequest, db: Session = Depends(get_db)):
    usuario = db.query(UsuarioORM).filter(UsuarioORM.email == solicitud.email).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se ha encontrado ninguna cuenta vinculada.")
    
    print(f"\n================ [SMTP OUTBOUND SIMULATOR] ================")
    print(f"DESTINATARIO: {usuario.email}")
    print(f"ASUNTO: Restablecimiento de contraseña")
    print(f"===========================================================\n")
    return {"mensaje": "Instrucciones de recuperación despachadas."}

# --- ENDPOINT PARA DETECTAR CONCURRENCIA LOGÍSTICA (TFG: Control de Franjas Ocupadas) ---
@app.get("/api/horarios-ocupados")
def obtener_horarios_ocupados(fecha: date, db: Session = Depends(get_db)):
    pedidos_fecha = db.query(PedidoORM).filter(func.date(PedidoORM.fecha_servicio) == fecha).all()
    horas_bloqueadas = [p.fecha_servicio.strftime("%H:%M") for p in pedidos_fecha]
    return {"horas_ocupadas": horas_bloqueadas}

@app.post("/api/pedidos")
def crear_pedido(pedido: schemas.PedidoCreate, db: Session = Depends(get_db), usuario_actual: Optional[UsuarioORM] = Depends(obtener_usuario_actual)):
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
            notas_cliente=pedido.notes_cliente,
            nombre_invitado=getattr(pedido, "nombre_invitado", None),
            apellidos_invitado=getattr(pedido, "apellidos_invitado", None),
            email_invitado=getattr(pedido, "email_invitado", None)
        )
        db.add(nuevo_pedido)
        db.flush() 

        for item in pedido.items:
            detalle = DetallePedidoORM(
                pedido_id=nuevo_pedido.id, plato_id=item.plato_id, cantidad=item.cantidad, precio_unitario=item.precio_unitario
            )
            db.add(detalle)
        
        db.commit() 
        return {"mensaje": "Pedido processed correctamente", "pedido_id": nuevo_pedido.id}
    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=400, detail=f"No se pudo completar el pedido: {str(e)}")

@app.get("/api/pedidos/me")
def obtener_mis_pedidos(db: Session = Depends(get_db), usuario_actual: UsuarioORM = Depends(obtener_usuario_actual)):
    if not usuario_actual:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Se requiere sesión activa.")
    return db.query(PedidoORM).filter(PedidoORM.usuario_id == usuario_actual.id).order_by(PedidoORM.creado_en.desc()).all()

@app.get("/api/admin/pedidos")
def obtener_todos_los_pedidos(db: Session = Depends(get_db), usuario_actual: Optional[UsuarioORM] = Depends(obtener_usuario_actual)):
    if not usuario_actual or usuario_actual.rol != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido.")
    return db.query(PedidoORM).order_by(PedidoORM.creado_en.desc()).all()

@app.put("/api/admin/pedidos/{pedido_id}/estado")
def actualizar_estado_pedido(pedido_id: int, datos: schemas.EstadoPedidoUpdate, db: Session = Depends(get_db), usuario_actual: Optional[UsuarioORM] = Depends(obtener_usuario_actual)):
    if not usuario_actual or usuario_actual.rol != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")
    
    pedido = db.query(PedidoORM).filter(PedidoORM.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    
    pedido.estado = datos.estado
    db.commit()
    return {"mensaje": "Estado del pedido actualizado con éxito", "pedido_id": pedido_id, "nuevo_estado": pedido.estado}

@app.post("/api/contacto", status_code=status.HTTP_201_CREATED)
def enviar_mensaje_contacto(mensaje: schemas.ContactoCreate, db: Session = Depends(get_db)):
    try:
        nuevo_mensaje = MensajeContactoORM(
            nombre=mensaje.nombre, email=mensaje.email, telefono=mensaje.telefono,
            numero_pedido=mensaje.numero_pedido, tipo_evento=mensaje.tipo_evento, mensaje=mensaje.mensaje,
            acepta_privacidad=mensaje.acepta_privacidad, acepta_comerciales=mensaje.acepta_comerciales
        )
        db.add(nuevo_mensaje)
        db.commit()
        db.refresh(nuevo_mensaje)
        return {"mensaje": "Mensaje almacenado correctamente", "ticket_id": nuevo_mensaje.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Fallo crítico al indexar el lead: {str(e)}")

@app.get("/api/admin/contacto")
def obtener_todos_los_mensajes(db: Session = Depends(get_db), usuario_actual: Optional[UsuarioORM] = Depends(obtener_usuario_actual)):
    if not usuario_actual or usuario_actual.rol != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido.")
    return db.query(MensajeContactoORM).order_by(MensajeContactoORM.creado_en.desc()).all()

@app.put("/api/admin/contacto/{mensaje_id}/leer")
def marcar_mensaje_como_leido(mensaje_id: int, db: Session = Depends(get_db), usuario_actual: Optional[UsuarioORM] = Depends(obtener_usuario_actual)):
    if not usuario_actual or usuario_actual.rol != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido.")
        
    mensaje = db.query(MensajeContactoORM).filter(MensajeContactoORM.id == mensaje_id).first()
    if not mensaje:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El ticket especificado no existe.")
        
    mensaje.leido = True
    db.commit()
    return {"mensaje": "El ticket de contacto ha sido marcado como atendido", "ticket_id": mensaje_id}