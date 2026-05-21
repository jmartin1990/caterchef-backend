import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Esto le dice a Python: "Ve a buscar el archivo .env y carga sus variables"
load_dotenv()

# Aquí Python lee la URL que acabas de guardar en el .env y la guarda en una variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Creamos el Motor de conexión a Neon
engine = create_engine(DATABASE_URL)

# Preparamos las sesiones para las consultas a la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependencia para inyectar la BBDD en cada petición
# Esta función es la que usaremos en main.py para acceder a los datos de Neon
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()