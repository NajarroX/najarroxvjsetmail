#!/usr/bin/env python3
# server.py - Servidor Flask con webhook para Recurrente
# Versión con filtro por ID de producto

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
# CONFIGURACIÓN DEL PRODUCTO
# ============================================
PRODUCTO_ID_PERMITIDO = "prod_hvmtars6"  # ← TU ID DEL BUNDLE

# Link de descarga (también se puede pasar desde email_sender.py)
# Pero lo dejamos aquí por claridad
LINK_DESCARGA = "https://drive.google.com/uc?export=download&id=TU_ID_DEL_ARCHIVO"

# ============================================
# FUNCIONES
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
    Solo procesa pagos exitosos del producto permitido.
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
            
            payment_data = data.get('data', {})
            
            # ========================================
            # EXTRAER EL ID DEL PRODUCTO COMPRADO
            # ========================================
            items = payment_data.get('items', [])
            producto_comprado_id = None
            
            if items and len(items) > 0:
                # El ID del producto puede venir en diferentes campos
                producto_comprado_id = items[0].get('product_id') or items[0].get('id') or items[0].get('product')
            
            # ========================================
            # VERIFICAR QUE SEA EL PRODUCTO CORRECTO
            # ========================================
            if producto_comprado_id != PRODUCTO_ID_PERMITIDO:
                logger.warning(f"⚠️ Producto no autorizado: {producto_comprado_id}. Esperado: {PRODUCTO_ID_PERMITIDO}")
                return jsonify({"status": "ignored", "reason": "invalid product"}), 200
            
            # ========================================
            # EXTRAER DATOS DEL CLIENTE
            # ========================================
            customer = payment_data.get('customer', {})
            email = customer.get('email')
            nombre = customer.get('name', 'Cliente')
            
            # Si no viene en 'customer', buscar en otros lugares
            if not email:
                email = payment_data.get('customer_email')
            if not email:
                email = payment_data.get('email')
            
            if not email:
                logger.error("Webhook: No se pudo obtener el email del cliente")
                logger.info(f"Datos recibidos: {payment_data.keys()}")
                return jsonify({"status": "error", "message": "No email"}), 400
            
            # ========================================
            # GENERAR CONTRASEÑA Y ENVIAR EMAIL
            # ========================================
            contrasena = generar_contrasena(email)
            
            # Llamar a la función de envío de email
            exito = enviar_email(email, nombre, contrasena, LINK_DESCARGA)
            
            if exito:
                logger.info(f"✅ Email enviado a {email} para producto {producto_comprado_id}")
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
            <p class="status">✅ SISTEMA ACTIVO CON WEBHOOK</p>
            <div class="info">
                <p>📧 Envío automático de credenciales vía webhook</p>
                <p>⚡ Tiempo de respuesta: inmediato</p>
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
        "modo": "webhook",
        "producto_id": PRODUCTO_ID_PERMITIDO,
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
    logger.info(f"🔒 Producto permitido: {PRODUCTO_ID_PERMITIDO}")
    app.run(host='0.0.0.0', port=port, debug=False)
