import subprocess
import time
import sys

print("🚀 INICIANDO SISTEMA G-CLOUD...")

# Lanzamos el Servidor Web (Flask)
# stdout=subprocess.DEVNULL hace que no llene la pantalla de logs basura de flask
web = subprocess.Popen([sys.executable, "app.py"])
print("✅ Interfaz Web: http://localhost:5000")

# Esperamos un segundito
time.sleep(2)

# Lanzamos el Core (Backend)
core = subprocess.Popen([sys.executable, "sync_core.py"])
print("✅ Core de Sincronización: ACTIVO")

try:
    # Mantiene el script vivo mientras los hijos vivan
    web.wait()
    core.wait()
except KeyboardInterrupt:
    print("\n🛑 Apagando todo...")
    web.terminate()
    core.terminate()