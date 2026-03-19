#!/usr/bin/env python3
from flask import Flask, jsonify
import threading
import time
import os
import logging
from email_sender import procesar_ventas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
background_thread_started = False

def tarea_cada_5_minutos():
    ciclo = 0
    logger.info("🚀 Hilo iniciado")
    while True:
        try:
            ciclo += 1
            logger.info(f"🔄 Ciclo #{ciclo}")
            nuevas = procesar_ventas()
            if nuevas > 0:
                logger.info(f"📊 {nuevas} nuevas ventas")
        except Exception as e:
            logger.error(f"Error: {e}")
        time.sleep(300)

@app.before_request
def iniciar_hilo():
    global background_thread_started
    if not background_thread_started:
        thread = threading.Thread(target=tarea_cada_5_minutos, daemon=True)
        thread.start()
        background_thread_started = True

@app.route('/')
def home():
    return "NAJARRO X - Sistema activo"

@app.route('/status')
def status():
    return jsonify({"status": "activo", "bundle": "COLECCIÓN COMPLETA 2026"})

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)