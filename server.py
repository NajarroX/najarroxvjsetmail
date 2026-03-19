#!/usr/bin/env python3
# server.py - Servidor Flask con tarea en segundo plano

from flask import Flask, jsonify
import threading
import time
import os
from email_sender import procesar_ventas  # Importa tu función

app = Flask(__name__)

# Variable para controlar el estado
procesos_activos = True

def tarea_cada_5_minutos():
    """Esta función corre en segundo plano 24/7"""
    ciclo = 0
    while procesos_activos:
        try:
            ciclo += 1
            print(f"\n🔄 Ciclo #{ciclo} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            nuevas = procesar_ventas()
            
            if nuevas > 0:
                print(f"📊 {nuevas} nuevas ventas procesadas")
            else:
                print("ℹ️ Sin ventas nuevas")
                
        except Exception as e:
            print(f"❌ Error en ciclo: {e}")
        
        # Esperar 5 minutos (300 segundos)
        for _ in range(300):
            if not procesos_activos:
                break
            time.sleep(1)

@app.route('/')
def home():
    """Página principal que muestra estado"""
    return """
    <html>
    <head>
        <style>
            body { font-family: monospace; background: #0a0a0a; color: white; padding: 40px; }
            .container { max-width: 600px; margin: 0 auto; border: 3px solid #8b5cf6; padding: 30px; }
            h1 { border-left: 8px solid #8b5cf6; padding-left: 20px; }
            .status { color: #00c853; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 NAJARRO X STUDIO</h1>
            <p class="status">✅ SISTEMA ACTIVO 24/7</p>
            <p>📧 Envío automático de credenciales</p>
            <p>⏰ Verificando ventas cada 5 minutos</p>
            <p>📊 <a href="/status" style="color: #8b5cf6;">Ver estado detallado</a></p>
        </div>
    </body>
    </html>
    """

@app.route('/status')
def status():
    """Endpoint para verificar que el sistema funciona"""
    return jsonify({
        "status": "activo",
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "procesos_activos": procesos_activos,
        "version": "1.0"
    })

@app.route('/health')
def health():
    """Para monitoreo de Render"""
    return "OK", 200

# Este bloque se ejecuta UNA SOLA VEZ cuando Render inicia la app
if __name__ == '__main__':
    # Iniciar el hilo en segundo plano
    hilo = threading.Thread(target=tarea_cada_5_minutos, daemon=True)
    hilo.start()
    print("🚀 Hilo de tareas iniciado")
    
    # Iniciar servidor Flask
    port = int(os.environ.get('PORT', 10000))  # Render asigna el puerto automáticamente
    app.run(host='0.0.0.0', port=port)