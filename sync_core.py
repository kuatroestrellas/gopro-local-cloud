import requests
import os
import time
import json
import sys
import platform
import urllib.parse

# TRUCO DEL ALMENDRUCO:
# Usamos el directorio donde está corriendo el script.
# Esto NUNCA falla. Siempre tienes permiso de escribir en tu propia carpeta.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATH = os.path.join(BASE_DIR, "G_CLOUD_MEDIA")

# Si no existe la carpeta default, la creamos suavemente
if not os.path.exists(DEFAULT_PATH):
    try:
        os.makedirs(DEFAULT_PATH)
    except:
        # Si por alguna razón satánica no podemos crear carpeta, usamos el directorio actual
        DEFAULT_PATH = BASE_DIR

ARCHIVO_INVENTARIO = "inventario_camaras.json"
ARCHIVO_ESTADO = "estado_sistema.json"
ARCHIVO_CONFIG = "config.json"
GOPRO_IP = "172.20.170.51"
BASE_URL = f"http://{GOPRO_IP}:8080"

# --- UTILIDADES ---
def cargar_config():
    if not os.path.exists(ARCHIVO_CONFIG):
        # Crear config default si no existe
        conf = {"ruta_destino": DEFAULT_PATH, "borrar_al_terminar": False, "apagar_al_terminar": False, "whatsapp_enable": False}
        with open(ARCHIVO_CONFIG, 'w') as f: json.dump(conf, f, indent=4)
        return conf
    try:
        with open(ARCHIVO_CONFIG, 'r') as f: return json.load(f)
    except: return {}

def actualizar_estado(estado, detalle, progreso=0, meta_data=None):
    datos = {
        "timestamp": time.time(),
        "estado_global": estado,
        "mensaje": detalle,
        "progreso_porcentaje": progreso,
        "meta": meta_data or {}
    }
    try:
        with open(ARCHIVO_ESTADO, 'w') as f: json.dump(datos, f)
    except: pass

def registrar_en_inventario(datos):
    """Guarda la cámara en el inventario si es nueva"""
    serial = datos['serial']
    modelo = datos['modelo']
    
    # Cargar inventario existente
    if os.path.exists(ARCHIVO_INVENTARIO):
        try:
            with open(ARCHIVO_INVENTARIO, 'r') as f:
                inv = json.load(f)
        except: inv = {}
    else:
        inv = {}
    
    # Si no existe, la creamos con datos default
    if serial not in inv:
        print(f"✨ Nueva cámara registrada: {serial}")
        inv[serial] = {
            "alias": f"{modelo}", # Nombre por defecto
            "modelo": modelo,
            "primera_vez": time.time(),
            "ultima_vez": time.time()
        }
        with open(ARCHIVO_INVENTARIO, 'w') as f:
            json.dump(inv, f, indent=4)
    else:
        # Si ya existe, actualizamos la última vez que la vimos
        inv[serial]['ultima_vez'] = time.time()
        with open(ARCHIVO_INVENTARIO, 'w') as f:
            json.dump(inv, f, indent=4)

def enviar_whatsapp(mensaje):
    c = cargar_config()
    if c.get("whatsapp_enable") and c.get("whatsapp_phone") and c.get("whatsapp_apikey"):
        try:
            msg = urllib.parse.quote(mensaje)
            requests.get(f"https://api.callmebot.com/whatsapp.php?phone={c['whatsapp_phone']}&text={msg}&apikey={c['whatsapp_apikey']}", timeout=5)
        except: pass

# --- CORE GOPRO ---
def obtener_telemetria():
    """Obtiene datos vitales. Si falla, retorna None (Señala desconexión)"""
    meta = {"bateria": 0, "espacio_gb": 0, "nombre_wifi": "GoPro", "modelo": "Detectando...", "serial": None, "firmware": "-"}
    try:
        # 1. Info Básica
        r = requests.get(f"{BASE_URL}/gopro/camera/info", timeout=2)
        r.raise_for_status()
        info = r.json()
        info = info.get('info', info) # Compatibilidad versiones
        
        meta["modelo"] = info.get('model_name', 'GoPro')
        meta["serial"] = info.get('serial_number')
        meta["firmware"] = info.get('firmware_version')

        # 2. Estado (Batería/SD)
        r2 = requests.get(f"{BASE_URL}/gopro/camera/state", timeout=2)
        r2.raise_for_status()
        status = r2.json().get('status', {})
        
        meta["bateria"] = status.get('70', status.get('2', 0)) # ID 70 es % exacto
        meta["espacio_gb"] = round(int(status.get('54', 0)) / (1024 * 1024), 1) # KB -> GB
        meta["nombre_wifi"] = status.get('30', meta["modelo"])
        
        return meta
    except Exception:
        return None # Retornar None dispara el "Freno de Mano"

def obtener_lista():
    try:
        r = requests.get(f"{BASE_URL}/gopro/media/list", timeout=5)
        r.raise_for_status()
        data = r.json()
        lista = []
        if 'media' in data:
            for d in data['media']:
                for f in d['fs']:
                    lista.append({
                        'url': f"{BASE_URL}/videos/DCIM/{d['d']}/{f['n']}",
                        'nombre': f['n'],
                        'ruta_remota': f"{d['d']}/{f['n']}",
                        'tamano': int(f['s'])
                    })
        return lista
    except: return None

def descargar_con_resume(url, ruta_local, tamano_remoto):
    """
    Descarga robusta. Retorna:
    True: Completado éxito.
    False: Error crítico (Desconexión).
    """
    descargado = 0
    modo = 'wb'

    # 1. Verificar si existe parcial
    if os.path.exists(ruta_local):
        descargado = os.path.getsize(ruta_local)
        if descargado == tamano_remoto:
            print(f"   [✓] {os.path.basename(ruta_local)} ya existe completo.")
            return True
        elif descargado > tamano_remoto:
            descargado = 0 # Archivo local corrupto/mayor, reiniciar
        else:
            modo = 'ab' # Append Binary
            print(f"   [↺] Reanudando {os.path.basename(ruta_local)} ({descargado//1024} KB)...")

    # 2. Configurar Headers
    headers = {'Range': f"bytes={descargado}-"} if descargado > 0 else {}

    # 3. Descargar Stream
    try:
        # TIMEOUT es vital aquí. Si se desconecta, debe lanzar error rápido.
        with requests.get(url, headers=headers, stream=True, timeout=10) as r:
            r.raise_for_status()
            with open(ruta_local, modo) as f:
                for chunk in r.iter_content(chunk_size=1024*1024): # 1MB chunks
                    if chunk:
                        f.write(chunk)
    except Exception as e:
        print(f"   [X] Error descarga: {e}")
        return False # ESTO ACTIVARÁ EL FRENO

    return True

def borrar_remoto(ruta):
    try: requests.get(f"{BASE_URL}/gopro/media/delete/file?path={ruta}", timeout=2)
    except: pass

def apagar_remoto():
    try: requests.get(f"{BASE_URL}/gopro/command/system/sleep", timeout=2)
    except: pass

# --- BUCLE MAESTRO ---
def main():
    print("--- G-CLOUD CORE REPARADO (RESUME FIXED) ---")
    
    while True:
        # 1. Configuración
        conf = cargar_config()
        ruta_base = conf.get("ruta_destino", DEFAULT_PATH)

        # 2. Polling (Buscando cámara)
        actualizar_estado("ESPERANDO", "Buscando conexión USB...", 0)
        telemetria = obtener_telemetria()

        if telemetria and telemetria["serial"]:
            # --- CONEXIÓN ESTABLECIDA ---
            print(f"\n🎥 CONECTADO: {telemetria['nombre_wifi']} ({telemetria['bateria']}%)")
            # --- [AGREGADO] REGISTRAR CÁMARA ---
            registrar_en_inventario(telemetria) 
            # -----------------------------------
            actualizar_estado("CONECTADO", "Analizando archivos...", 0, telemetria)

            # Crear carpeta UUID (o NombreWifi si prefieres, aquí dejé Serial por seguridad)
            carpeta_destino = os.path.join(ruta_base, telemetria["serial"])
            if not os.path.exists(carpeta_destino): os.makedirs(carpeta_destino)

            # Obtener lista
            lista_archivos = obtener_lista()
            if lista_archivos is None:
                print("⚠️ Error leyendo lista de archivos.")
                time.sleep(2)
                continue # Volver a buscar

            total_archivos = len(lista_archivos)
            copiados_sesion = 0
            hubo_error_critico = False

            # --- BUCLE DE DESCARGA ---
            for i, archivo in enumerate(lista_archivos):
                # 1. Verificar si seguimos conectados antes de cada archivo
                telemetria_live = obtener_telemetria()
                if not telemetria_live:
                    print("⚠️ DESCONEXIÓN DETECTADA ANTES DE ARCHIVO.")
                    hubo_error_critico = True
                    break # ROMPER EL FOR

                # 2. Actualizar UI
                porcentaje_total = int((i / total_archivos) * 100)
                msg_ui = f"Copiando {i+1}/{total_archivos}: {archivo['nombre']}"
                print(msg_ui)
                actualizar_estado("COPIANDO", msg_ui, porcentaje_total, telemetria_live)

                # 3. INTENTAR DESCARGA
                ruta_final = os.path.join(carpeta_destino, archivo['nombre'])
                exito = descargar_con_resume(archivo['url'], ruta_final, archivo['tamano'])

                if not exito:
                    print("⚠️ DESCONEXIÓN DURANTE DESCARGA.")
                    hubo_error_critico = True
                    break # ROMPER EL FOR (EL FRENO DE MANO)
                
                # 4. Si éxito: Borrar (si config) y contar
                copiados_sesion += 1
                if conf.get("borrar_al_terminar"):
                    borrar_remoto(archivo['ruta_remota'])

            # --- FIN DEL BUCLE ---
            if hubo_error_critico:
                # Si salimos por break, volvemos inmediato al While True a buscar
                actualizar_estado("ERROR", "Conexión perdida. Reintentando...", 0)
                time.sleep(1) # Pequeña pausa
            else:
                # Éxito total
                actualizar_estado("FINALIZADO", "Respaldo completado.", 100, telemetria)
                print("✅ Todo respaldado correctamente.")
                
                if copiados_sesion > 0:
                    enviar_whatsapp(f"✅ G-Cloud: {telemetria['nombre_wifi']} finalizó. {copiados_sesion} archivos nuevos.")
                
                if conf.get("apagar_al_terminar"):
                    apagar_remoto()

                # Esperar a que el usuario desconecte físicamente
                print("⏳ Esperando desconexión física...")
                while obtener_telemetria():
                    time.sleep(3)
                print("👋 Cámara retirada.\n")

        else:
            # No hay cámara, dormir un poco
            time.sleep(3)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: pass