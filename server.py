#!/usr/bin/env python3
# server.py - Versión CORREGIDA para la estructura real de Recurrente

from flask import Flask, request, jsonify
import os
import logging
import hashlib
import random
import string
import json
from datetime import datetime
from email_sender import enviar_email

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============================================
# CONFIGURACIÓN
# ============================================
PRODUCTO_ID_PERMITIDO = "prod_hvmtars6"
LINK_DESCARGA = "https://drive.google.com/uc?export=download&id=1MX2gjwNU6JfEWGVkXnrueZUQMKBSyRcW"

# ============================================
# FUNCIONES
# ============================================

def generar_contrasena(email_cliente):
    base = f"{email_cliente}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    hash_obj = hashlib.md5(base.encode())
    hash_str = hash_obj.hexdigest()[:8].upper()
    extras = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"NX-{hash_str}{extras}"

# ============================================
# WEBHOOK
# ============================================

@app.route('/webhook', methods=['POST'])
def webhook_recurrente():
    try:
        # Obtener JSON
        data = request.get_json()
        
        if not data:
            logger.warning("Webhook sin datos")
            return jsonify({"status": "error"}), 400
        
        # Extraer tipo de evento (está en 'event_type')
        event_type = data.get('event_type')
        logger.info(f"📨 Evento: {event_type}")
        
        # Solo procesar payment_intent.succeeded
        if event_type == 'payment_intent.succeeded':
            logger.info("✅ Procesando pago exitoso")
            
            # ========================================
            # EXTRAER DATOS (según la estructura real)
            # ========================================
            
            # 1. ID del producto (está en 'product.id')
            producto_id = data.get('product', {}).get('id')
            
            if not producto_id:
                logger.error("❌ No se encontró ID del producto")
                return jsonify({"status": "error", "message": "No product ID"}), 400
            
            # 2. Verificar producto
            if producto_id != PRODUCTO_ID_PERMITIDO:
                logger.warning(f"⚠️ Producto no autorizado: {producto_id}")
                return jsonify({"status": "ignored", "reason": "invalid product"}), 200
            
            logger.info(f"✅ Producto verificado: {producto_id}")
            
            # 3. Email del cliente (está en 'customer.email')
            customer = data.get('customer', {})
            email = customer.get('email')
            
            if not email:
                logger.error("❌ No se encontró email del cliente")
                return jsonify({"status": "error", "message": "No email"}), 400
            
            # 4. Nombre del cliente (está en 'customer.full_name')
            nombre = customer.get('full_name', 'Cliente')
            
            logger.info(f"📧 Cliente: {nombre} <{email}>")
            
            # ========================================
            # ENVIAR EMAIL
            # ========================================
            contrasena = generar_contrasena(email)
            exito = enviar_email(email, nombre, contrasena, LINK_DESCARGA)
            
            if exito:
                logger.info(f"✅ Email enviado a {email}")
                return jsonify({"status": "ok", "message": "Email sent"}), 200
            else:
                logger.error(f"❌ Falló envío a {email}")
                return jsonify({"status": "error", "message": "Email failed"}), 500
        
        # Otros eventos
        logger.info(f"Evento ignorado: {event_type}")
        return jsonify({"status": "ignored"}), 200
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================
# ENDPOINTS DE ESTADO
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
            <p class="status">✅ SISTEMA ACTIVO</p>
            <p>📧 Envío automático de credenciales</p>
            <p>🔒 Producto: prod_hvmtars6</p>
            <p>📊 <a href="/status">Ver estado</a></p>
        </div>
    </body>
    </html>
    """

@app.route('/status')
def status():
    return jsonify({
        "status": "activo",
        "producto_id": PRODUCTO_ID_PERMITIDO,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "version": "4.0-final"
    })

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Servidor iniciado en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
