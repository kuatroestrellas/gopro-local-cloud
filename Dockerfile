# Usamos Python ligero
FROM python:3.9-slim

# Evita que Python guarde archivos .pyc y fuerza logs inmediatos
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema (útiles para depurar)
RUN apt-get update && apt-get install -y \
    curl \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Instalar librerías de Python
# (Flask y Requests son las únicas que usamos)
RUN pip install --no-cache-dir flask requests

# Copiar el código (El .gitignore evita copiar basura si usas git, 
# pero Docker tiene su propio .dockerignore, asume que copias todo lo limpio)
COPY . /app

# Puerto web
EXPOSE 5000

# Comando de arranque: Usamos el launcher que creamos
CMD ["python", "main.py"]