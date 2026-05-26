# Usa una imagen oficial de Python ligera como base
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Evita que Python escriba archivos .pyc en el disco y asegura que los logs salgan directos
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependencias del sistema necesarias para compilar ciertas librerías si hiciese falta
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia primero el archivo de requerimientos para aprovechar la caché de Docker
COPY requirements.txt /app/

# Instala las dependencias de Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copia todo el resto del código del backend al contenedor
COPY . /app/

# Expone el puerto nativo en el que corre FastAPI
EXPOSE 8000

# Comando por defecto para arrancar la API con Uvicorn apuntando a producción
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]