import threading
import webbrowser
import socket
import customtkinter as ctk
from werkzeug.serving import make_server

# Importamos directo de tus motores
from app import app 
import sync_core  #<-- (Descomenta cuando lo vayas a usar)

servidor_flask = None

def obtener_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def arrancar_servidor():
    global servidor_flask
    # Usamos make_server para poder apagarlo a voluntad después
    servidor_flask = make_server('0.0.0.0', 5000, app)
    servidor_flask.serve_forever()

def toggle_evento():
    global servidor_flask
    estado = switch_var.get()
    
    if estado == "on":
        # --- ENCENDER ---
        hilo_flask = threading.Thread(target=arrancar_servidor, daemon=True)
        hilo_flask.start()
        
        # Si tienes tu script de copia, lo arrancas aquí también:
        hilo_sync = threading.Thread(target=sync_core.main, daemon=True)
        hilo_sync.start()
        
        ip = obtener_ip_local()
        lbl_estado.configure(text=f"✅ Online:\nhttp://{ip}:5000", text_color="#2ecc71")
        switch_servidor.configure(text="Stop Server")
        btn_abrir.configure(state="normal")
    else:
        # --- APAGAR ---
        if servidor_flask:
            servidor_flask.shutdown() # Apagado limpio
            
        lbl_estado.configure(text="🔴 Server Stopped", text_color="#e74c3c")
        switch_servidor.configure(text="Start Server")
        btn_abrir.configure(state="disabled")

def abrir_navegador():
    ip = obtener_ip_local()
    webbrowser.open(f"http://{ip}:5000")

# --- DISEÑO DE LA VENTANA (Estilo Fachero) ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ventana = ctk.CTk()
ventana.title("GoPro Local Cloud")
ventana.geometry("350x300")
ventana.resizable(False, False)

# Título
lbl_titulo = ctk.CTkLabel(ventana, text="☁️ GoPro Local Cloud", font=("Segoe UI", 22, "bold"))
lbl_titulo.pack(pady=(25, 5))

# Estado
lbl_estado = ctk.CTkLabel(ventana, text="🔴 Server Stopped", text_color="#e74c3c", font=("Segoe UI", 14))
lbl_estado.pack(pady=(0, 20))

# Switch estilo iPhone/Google
switch_var = ctk.StringVar(value="off")
switch_servidor = ctk.CTkSwitch(
    ventana, 
    text="Start Server", 
    command=toggle_evento,
    variable=switch_var, 
    onvalue="on", 
    offvalue="off",
    font=("Segoe UI", 14, "bold")
)
switch_servidor.pack(pady=10)

# Botón del navegador
btn_abrir = ctk.CTkButton(
    ventana, 
    text="Open in Browser", 
    command=abrir_navegador, 
    state="disabled",
    fg_color="#2980b9",
    hover_color="#3498db"
)
btn_abrir.pack(pady=15)

# Créditos
lbl_creditos = ctk.CTkLabel(
    ventana, 
    text="Developed by @kuatroestrellas | TikTok: @casicomosen", 
    font=("Segoe UI", 10), 
    text_color="gray"
)
lbl_creditos.pack(side="bottom", pady=10)

ventana.mainloop()