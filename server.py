#!/usr/bin/env python3
# server.py - Servidor Flask para Render con hilo en segundo plano

from flask import Flask, jsonify
import threading
import time
import os
import logging
from email_sender import procesar_ventas

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Variable para controlar que el hilo se inicie solo una vez
background_thread_started = False

def tarea_cada_5_minutos():
    """Esta función corre en segundo plano 24/7"""
    ciclo = 0
    logger.info("🚀 Hilo de tareas iniciado")
    
    while True:
        try:
            ciclo += 1
            logger.info(f"🔄 Ciclo #{ciclo} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            nuevas = procesar_ventas()
            
            if nuevas > 0:
                logger.info(f"📊 {nuevas} nuevas ventas procesadas en este ciclo")
                
        except Exception as e:
            logger.error(f"❌ Error en ciclo: {e}")
        
        # Esperar 5 minutos (300 segundos)
        time.sleep(300)

@app.before_request
def iniciar_hilo():
    """Inicia el hilo UNA SOLA VEZ cuando llega la primera petición"""
    global background_thread_started
    if not background_thread_started:
        thread = threading.Thread(target=tarea_cada_5_minutos, daemon=True)
        thread.start()
        background_thread_started = True
        logger.info("✅ Hilo de fondo iniciado correctamente")

@app.route('/')
def home():
    return """
    <html>
    <head>
        <style>
            body { font-family: 'Space Mono', monospace; background: #0a0a0a; color: white; padding: 40px; }
            .container { max-width: 600px; margin: 0 auto; border: 3px solid #8b5cf6; padding: 30px; background: rgba(0,0,0,0.5); }
            h1 { border-left: 8px solid #8b5cf6; padding-left: 20px; }
            .status { color: #00c853; font-size: 1.2rem; }
            .info { margin: 20px 0; }
            a { color: #8b5cf6; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 NAJARRO X STUDIO</h1>
            <p class="status">✅ SISTEMA ACTIVO 24/7</p>
            <div class="info">
                <p>📧 Envío automático de credenciales</p>
                <p>⏰ Verificando ventas cada 5 minutos</p>
                <p>📊 <a href="/status">Ver estado detallado</a></p>
                <p>❤️ <a href="/health">Health check</a></p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/status')
def status():
    return jsonify({
        "status": "activo",
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "hilo_activo": background_thread_started,
        "version": "1.0",
        "servicio": "NAJARRO X - Email Automator"
    })

@app.route('/health')
def health():
    """Endpoint para monitoreo de Render"""
    return "OK", 200

# Este bloque SOLO se ejecuta si corres python server.py directamente (desarrollo local)
if __name__ == '__main__':
    # En desarrollo local, iniciamos el hilo manualmente
    if not background_thread_started:
        thread = threading.Thread(target=tarea_cada_5_minutos, daemon=True)
        thread.start()
        background_thread_started = True
    
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Iniciando servidor en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)