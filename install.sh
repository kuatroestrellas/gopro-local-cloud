#!/bin/bash
echo "🚀 Iniciando instalación de GoPro Local Cloud..."

# 1. Actualizar el sistema
sudo apt-get update -y

# 2. Instalar Docker si no existe
if ! command -v docker &> /dev/null; then
    echo "🐳 Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
else
    echo "✅ Docker ya está instalado."
fi

# 3. Asegurar que el demonio de Docker arranque con la Pi
echo "⚙️ Configurando el auto-arranque del sistema..."
sudo systemctl enable docker
sudo systemctl enable containerd

# 4. Clonar el repositorio
echo "📥 Descargando el código..."
# (Asegúrate de cambiar 'tu-usuario' por tu usuario real de GitHub)
git clone https://github.com/kuatroestrellas/gopro-local-cloud.git
cd gopro-local-cloud

# 5. Crear carpeta de datos por si acaso
mkdir -p data

# 6. Levantar el sistema
echo "🔥 Construyendo y levantando el servidor..."
sudo docker compose up -d --build

echo "🎉 ¡Listo! El sistema correrá en automático incluso si reinicias."
echo "🌐 Abre tu navegador en la IP de esta Raspberry Pi por el puerto 5000."