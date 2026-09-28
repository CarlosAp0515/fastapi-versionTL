# 1. Usamos una versión ligera de Python 3.12 (la que vienes usando)
FROM python:3.12-slim

# 2. Instalamos 'uv' dentro del contenedor
RUN pip install uv

# 3. Creamos una carpeta llamada /app donde vivirá nuestro código
WORKDIR /app

# 4. Copiamos tus archivos de dependencias primero
COPY pyproject.toml uv.lock ./

# 5. Instalamos las librerías (FastAPI, SQLModel, etc.)
RUN uv sync

# 6. Copiamos el resto de tu código (main.py, src, alembic, etc.)
COPY . .

# 7. Exponemos el puerto 8000 para poder entrar desde el navegador
EXPOSE 8000

# 8. El comando final para encender el servidor cuando el contenedor arranque
CMD ["uv", "run", "fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]