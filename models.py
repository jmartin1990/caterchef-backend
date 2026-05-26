# MODELOS DE BASE DE DATOS (ORM - SQLAlchemy)

from sqlalchemy import Column, Integer, String, Numeric, Boolean, TIMESTAMP, func, Date, ForeignKey, Text
from database import Base

class PlatoORM(Base):
    __tablename__ = "platos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150))
    descripcion = Column(String)
    precio = Column(Numeric(10, 2))
    categoria = Column(String(100))
    alergenos = Column(String(255))
    disponible = Column(Boolean, default=True)
    imagen_url = Column(String(255), nullable=True) 

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
    nombre_invitado = Column(String(100), nullable=True)
    apellidos_invitado = Column(String(100), nullable=True)
    email_invitado = Column(String(150), nullable=True)
    creado_en = Column(TIMESTAMP, server_default=func.now())

class DetallePedidoORM(Base):
    __tablename__ = "detalles_pedido"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"))
    plato_id = Column(Integer, ForeignKey("platos.id", ondelete="RESTRICT"))
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)

class MensajeContactoORM(Base):
    __tablename__ = "mensajes_contacto"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=True)
    numero_pedido = Column(String(50), nullable=True) 
    tipo_evento = Column(String(100), nullable=True)
    mensaje = Column(Text, nullable=False)
    leido = Column(Boolean, default=False) 
    acepta_privacidad = Column(Boolean, nullable=False, default=False) 
    acepta_comerciales = Column(Boolean, default=False) 
    creado_en = Column(TIMESTAMP, server_default=func.now())