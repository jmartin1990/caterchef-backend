import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Importación moderna y robusta para SQLAlchemy 2.0+
from sqlalchemy.orm import DeclarativeBase

# Esto le dice a Python: "Ve a buscar el archivo .env y carga sus variables de entorno"
load_dotenv()

# Recupera de forma segura la cadena de conexión SSL a la base de datos de Neon DB
DATABASE_URL = os.getenv("DATABASE_URL")

# --- ACTUALIZADO: CONFIGURACIÓN DE RESILIENCIA DEL POOL DE CONEXIONES (TFG: Optimización Serverless) ---
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # Envía un micro-test interno ("ping") antes de lanzar consultas.
    pool_recycle=300      # Recicla y renueva de forma automática cualquier hilo de conexión que supere los 5 minutos.
)

# Preparamos las factorías de sesiones encargadas de coordinar los ciclos de vida transaccionales con la DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Instanciamos la clase base declarativa con la sintaxis oficial moderna de SQLAlchemy 2.0
class Base(DeclarativeBase):
    pass

# Middleware inyector de dependencias empleado en las rutas distribuidas de main.py
def get_db():
    """
    Patrón de aislamiento de transacciones por ciclo de petición/respuesta (Unit of Work).
    Garantiza la apertura atómica de la conexión y obliga a su desasignación limpia en el
    bloque 'finally' para impedir fugas de memoria (memory leaks) en el pool.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()