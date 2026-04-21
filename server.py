#!/usr/bin/env python3
# server.py - Servidor Flask con webhook para Recurrente

from flask import Flask, request, jsonify
import threading
import time
import os
import logging
import hashlib
import random
import string
from datetime import datetime
from email_sender import enviar_email

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============================================
# FUNCIONES PARA GENERAR CONTRASEÑA
# ============================================

def generar_contrasena(email_cliente):
    """Genera una contraseña única para cada compra"""
    base = f"{email_cliente}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    hash_obj = hashlib.md5(base.encode())
    hash_str = hash_obj.hexdigest()[:8].upper()
    extras = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"NX-{hash_str}{extras}"

# ============================================
# WEBHOOK - DONDE RECURRENTE NOS LLAMA
# ============================================

@app.route('/webhook', methods=['POST'])
def webhook_recurrente():
    """
    Recurrente llama a este endpoint cuando ocurre un evento.
    Es importante verificar que el evento sea 'payment.succeeded'
    """
    try:
        # Obtener los datos que envía Recurrente
        data = request.get_json()
        
        if not data:
            logger.warning("Webhook recibido sin datos")
            return jsonify({"status": "error", "message": "No data"}), 400
        
        logger.info(f"📨 Webhook recibido: {data.get('type', 'unknown')}")
        
        # Verificar que sea un pago exitoso
        if data.get('type') == 'payment.succeeded':
            
            # Extraer información del cliente (AJUSTA SEGÚN LA RESPUESTA REAL)
            payment_data = data.get('data', {})
            customer = payment_data.get('customer', {})
            
            email = customer.get('email')
            nombre = customer.get('name', 'Cliente')
            
            # También puede venir en otra estructura, por si acaso
            if not email:
                email = payment_data.get('customer_email')
            
            if not email:
                logger.error("Webhook: No se pudo obtener el email del cliente")
                return jsonify({"status": "error", "message": "No email"}), 400
            
            # Generar contraseña única
            contrasena = generar_contrasena(email)
            
            # Enviar email con el link de descarga
            exito = enviar_email(email, nombre, contrasena)
            
            if exito:
                logger.info(f"✅ Email enviado a {email}")
                return jsonify({"status": "ok", "message": "Email sent"}), 200
            else:
                logger.error(f"❌ Falló envío de email a {email}")
                return jsonify({"status": "error", "message": "Email failed"}), 500
        
        # Si el evento no es un pago exitoso, lo ignoramos
        logger.info(f"Evento ignorado: {data.get('type')}")
        return jsonify({"status": "ignored"}), 200
        
    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================
# ENDPOINTS DE ESTADO (para monitoreo)
# ============================================

@app.route('/')
def home():
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
            <p class="status">✅ SISTEMA ACTIVO CON WEBHOOK</p>
            <p>📧 Envío automático de credenciales vía webhook</p>
            <p>⚡ Tiempo de respuesta: inmediato</p>
            <p>📊 <a href="/status">Ver estado</a></p>
        </div>
    </body>
    </html>
    """

@app.route('/status')
def status():
    return jsonify({
        "status": "activo",
        "modo": "webhook",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "version": "2.0"
    })

@app.route('/health')
def health():
    return "OK", 200

# ============================================
# EJECUCIÓN PRINCIPAL
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Iniciando servidor con webhook en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
