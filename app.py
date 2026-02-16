from flask import Flask, render_template, jsonify, request
import json
import os
import platform
import string

app = Flask(__name__)
ARCHIVO_ESTADO = "estado_sistema.json"
ARCHIVO_CONFIG = "config.json"

def leer_json(archivo):
    if not os.path.exists(archivo): return {}
    try: 
        with open(archivo, 'r') as f: return json.load(f)
    except: return {}

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/status')
def get_status(): return jsonify(leer_json(ARCHIVO_ESTADO))

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        with open(ARCHIVO_CONFIG, 'w') as f:
            json.dump(request.json, f, indent=4)
        return jsonify({"success": True})
    return jsonify(leer_json(ARCHIVO_CONFIG))

# API Explorador de Carpetas (La mantenemos para el selector)
@app.route('/api/drives')
def get_drives():
    drives = ["/", "/media", "/mnt", "/home"] if platform.system() != "Windows" else [f"{d}:/" for d in string.ascii_uppercase if os.path.exists(f"{d}:")]
    return jsonify(drives)

@app.route('/api/browse', methods=['POST'])
def browse_folder():
    path = request.json.get('path', '/')
    try:
        items = [e.name for e in os.scandir(path) if e.is_dir()]
        return jsonify({"current": path, "folders": sorted(items)})
    except Exception as e: return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)