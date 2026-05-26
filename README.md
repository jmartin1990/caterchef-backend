# CaterChef Backend - API RESTful (FastAPI)

Este repositorio contiene el núcleo lógico de la aplicación **CaterChef**, encargado de la gestión de usuarios, reservas de chefs a domicilio, pedidos de catering y pasarela.

## 🛠️ Stack Tecnológico

- **Framework:** FastAPI (Python 3.11+)
- **Base de Datos:** PostgreSQL (Neon DB en producción) / SQLite (Entorno de pruebas)
- **ORM:** SQLAlchemy con operaciones asíncronas
- **Autenticación:** Seguridad basada en OAuth2 y JSON Web Tokens (JWT)
- **Testing:** Pytest con base de datos en memoria (`sqlite:///:memory:`)

## 🐳 Arquitectura Docker (Producción)

El backend utiliza un archivo `Dockerfile` optimizado con una **build multi-etapa (multi-stage build)** basada en Python Alpine para reducir drásticamente el peso de la imagen final:

### Comandos de Terminal para Gestión Manual de Docker:

````bash
# 1. Construir la imagen del backend de forma aislada
docker build -t caterchef-backend:latest .

# 2. Levantar el contenedor mapeando el puerto de la API
docker run -d -p 8000:8000 --name container-backend caterchef-backend:latest

# 3. Ver los logs de la API en tiempo real
docker logs -f container-backend

Suite de Testing Automatizado
Se ha implementado una arquitectura de pruebas unitarias que no ensucia la base de datos de producción mediante el uso de un entorno aislado.

Comandos de Ejecución de Tests:

# Activar el entorno virtual si se trabaja en local
source venv/Scripts/activate  # En Windows (Git Bash)

# Ejecutar la suite completa con reporte detallado (Verbose)
python -m pytest -v

Pipeline de Integración Continua (CI/CD)
El repositorio incluye un flujo automatizado en GitHub Actions (.github/workflows/backend-ci.yml) que se dispara en cada push o pull_request hacia las ramas main y dev, realizando las siguientes tareas:

Levanta un entorno Ubuntu con Python.

Instala de forma limpia las dependencias (pip install).

Ejecuta de manera obligatoria la suite de pytest. Si un test falla, el pipeline se bloquea y no permite el despliegue.

---

### 2. 📁 En la raíz de `caterchef-frontend/README.md`

```markdown
# CaterChef Frontend - Interfaz Web (Next.js)

Este repositorio contiene la interfaz de usuario interactiva de **CaterChef**, diseñada para ofrecer una experiencia fluida (UX) en la contratación de catering y chefs.

## 🛠️ Stack Tecnológico
- **Framework:** Next.js 16 (App Router & Turbopack)
- **Lenguaje:** TypeScript (Tipado estricto adaptado para configuraciones asíncronas)
- **Estilos:** Tailwind CSS (Diseño responsive y adaptativo)
- **Testing:** Jest + React Testing Library

## 🐳 Arquitectura Docker
El frontend está dockerizado de forma independiente y preparado para servir la aplicación compilada.

### Comandos de Terminal para Gestión Manual de Docker:
```bash
# 1. Construir la imagen del frontend
docker build -t caterchef-frontend:latest .

# 2. Levantar el contenedor en el puerto de Next.js
docker run -d -p 3000:3000 --name container-frontend caterchef-frontend:latest

Suite de Testing y Mocking
Para las pruebas unitarias del frontend, se utiliza Jest. Debido al uso de hooks avanzados de Next.js (useRouter, useSearchParams), se ha implementado un sistema de Mocking para emular el comportamiento del App Router sin necesidad de levantar un navegador real.

Comandos de Ejecución de Tests:

# 1. Situarse en la carpeta del frontend
cd caterchef-frontend

# 2. Ejecutar la suite de pruebas unitarias en el DOM virtual
npm run test

Pipeline de Integración Continua (CI/CD)
Automatizado mediante GitHub Actions (.github/workflows/frontend-ci.yml):

Realiza una instalación limpia con npm ci.

Ejecuta npm run build verificando que no existan errores de compilación ni conflictos estrictos en las interfaces de TypeScript (next.config.ts), garantizando que la versión subida sea 100% estable.

---

### 3. 📁 En la raíz del proyecto principal `Proyecto_TFG/README.md`

```markdown
# 🏆 Proyecto Fin de Grado: CaterChef Fusion

**Autor:** Juan Martín Campos
**Especialidad:** Técnico Superior en Desarrollo de Aplicaciones Web (DAW)

Este repositorio actúa como el **Orquestador Central** del proyecto **CaterChef**, un gestor integral full-stack para empresas de catering y chefs a domicilio que fusiona la gastronomía peruana y española.

## 🏗️ Arquitectura de Red y Orquestación Global
El sistema completo se gestiona de manera unificada mediante **Docker Compose**, aislando los servicios en una red privada de tipo puente (`bridge`) llamada `caterchef_network`. Esto permite que el Frontend y el Backend se comuniquen de forma segura sin exponer puertos innecesarios al exterior.

## 🚀 Manual de Arranque Rápido (Terminal Unificada)

Para arrancar todo el ecosistema (Base de datos, API y Servidor Web) en un solo comando y sin configurar entornos locales, sigue estos pasos:

```bash
# 1. Clonar el proyecto y situarse en la raíz del mismo
cd ~/Documents/Proyectos/Proyecto_TFG

# 2. Levantar y compilar todos los servicios en segundo plano
docker-compose up --build -d

# 3. Comprobar que los contenedores están corriendo correctamente
docker-compose ps

Puntos de Acceso del Sistema:
Aplicación Web (Frontend): http://localhost:3000

Documentación Interactiva de la API (Swagger): http://localhost:8000/docs

Resumen del Control de Calidad (DevOps)
El proyecto sigue la filosofía de desarrollo moderna mediante la automatización completa de los flujos de trabajo:

Doble validación en la nube: Repositorios protegidos por pipelines independientes en GitHub Actions que impiden subir código roto.

Ecosistema Multiplataforma: Gracias a Docker, el proyecto funciona exactamente igual en el ordenador de desarrollo (Windows 11 Pro) que en los servidores de despliegue de GitHub.
````
