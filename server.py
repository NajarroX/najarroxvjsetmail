#!/usr/bin/env python3
# server.py - Servidor Flask con webhook para Recurrente
# Versión mejorada: extrae correctamente el ID del producto

from flask import Flask, request, jsonify
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

# Link de descarga (actualiza con tu link real de Drive)
LINK_DESCARGA = "https://drive.google.com/uc?export=download&id=1MX2gjwNU6JfEWGVkXnrueZUQMKBSyRcW"

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

def extraer_producto_id(payment_data):
    """
    Extrae el ID del producto del JSON de Recurrente.
    Busca en múltiples ubicaciones posibles.
    """
    # 1. Buscar en items[0].product_id
    items = payment_data.get('items', [])
    if items and len(items) > 0:
        item = items[0]
        
        # Probar diferentes campos
        product_id = item.get('product_id')
        if product_id:
            return product_id
        
        product_id = item.get('id')
        if product_id:
            return product_id
        
        product_id = item.get('product')
        if product_id:
            return product_id
        
        # Buscar dentro de price
        price = item.get('price', {})
        product_id = price.get('product_id')
        if product_id:
            return product_id
    
    # 2. Buscar en data.product_id
    product_id = payment_data.get('product_id')
    if product_id:
        return product_id
    
    # 3. Buscar en data.metadata
    metadata = payment_data.get('metadata', {})
    product_id = metadata.get('product_id')
    if product_id:
        return product_id
    
    return None

def extraer_email_cliente(payment_data):
    """
    Extrae el email del cliente del JSON de Recurrente.
    Busca en múltiples ubicaciones posibles.
    """
    # 1. Buscar en customer.email
    customer = payment_data.get('customer', {})
    email = customer.get('email')
    if email:
        return email
    
    # 2. Buscar directamente en customer_email
    email = payment_data.get('customer_email')
    if email:
        return email
    
    # 3. Buscar en email
    email = payment_data.get('email')
    if email:
        return email
    
    # 4. Buscar en metadata
    metadata = payment_data.get('metadata', {})
    email = metadata.get('email')
    if email:
        return email
    
    return None

def extraer_nombre_cliente(payment_data):
    """
    Extrae el nombre del cliente del JSON de Recurrente.
    """
    customer = payment_data.get('customer', {})
    nombre = customer.get('name')
    if nombre:
        return nombre
    
    nombre = payment_data.get('customer_name')
    if nombre:
        return nombre
    
    nombre = payment_data.get('name')
    if nombre:
        return nombre
    
    return "Cliente"

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
        # Verificar que el Content-Type sea application/json
        if not request.is_json:
            logger.error(f"Content-Type no es JSON: {request.content_type}")
            return jsonify({"status": "error", "message": "Expected JSON"}), 415
        
        # Obtener los datos que envía Recurrente
        data = request.get_json()
        
        if not data:
            logger.warning("Webhook recibido sin datos")
            return jsonify({"status": "error", "message": "No data"}), 400
        
        event_type = data.get('type')
        logger.info(f"📨 Webhook recibido: {event_type}")
        
        # Verificar que sea un pago exitoso
        if event_type == 'payment.succeeded':
            
            payment_data = data.get('data', {})
            
            # ========================================
            # EXTRAER EL ID DEL PRODUCTO COMPRADO
            # ========================================
            producto_comprado_id = extraer_producto_id(payment_data)
            
            if not producto_comprado_id:
                # Si no se pudo extraer, mostrar la estructura para depurar
                logger.warning("No se pudo extraer el ID del producto")
                logger.info(f"Estructura de payment_data: {list(payment_data.keys())}")
                items = payment_data.get('items', [])
                if items:
                    logger.info(f"Primer item: {items[0]}")
                return jsonify({"status": "error", "message": "Product ID not found"}), 400
            
            # ========================================
            # VERIFICAR QUE SEA EL PRODUCTO CORRECTO
            # ========================================
            if producto_comprado_id != PRODUCTO_ID_PERMITIDO:
                logger.warning(f"⚠️ Producto no autorizado: {producto_comprado_id}. Esperado: {PRODUCTO_ID_PERMITIDO}")
                return jsonify({"status": "ignored", "reason": "invalid product"}), 200
            
            logger.info(f"✅ Producto verificado: {producto_comprado_id}")
            
            # ========================================
            # EXTRAER DATOS DEL CLIENTE
            # ========================================
            email = extraer_email_cliente(payment_data)
            nombre = extraer_nombre_cliente(payment_data)
            
            if not email:
                logger.error("❌ No se pudo obtener el email del cliente")
                logger.info(f"Datos disponibles: {list(payment_data.keys())}")
                return jsonify({"status": "error", "message": "No email"}), 400
            
            logger.info(f"📧 Cliente: {nombre} <{email}>")
            
            # ========================================
            # GENERAR CONTRASEÑA Y ENVIAR EMAIL
            # ========================================
            contrasena = generar_contrasena(email)
            
            # Enviar email
            exito = enviar_email(email, nombre, contrasena, LINK_DESCARGA)
            
            if exito:
                logger.info(f"✅ Email enviado a {email}")
                return jsonify({"status": "ok", "message": "Email sent"}), 200
            else:
                logger.error(f"❌ Falló envío de email a {email}")
                return jsonify({"status": "error", "message": "Email failed"}), 500
        
        # Si el evento no es un pago exitoso, lo ignoramos
        logger.info(f"Evento ignorado: {event_type}")
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
            .container { max-width: 600px; margin: 0 auto; border: 3px solid #8b5cf6; padding: 30px; background: rgba(0,0,0,0.5); }
            h1 { border-left: 8px solid #8b5cf6; padding-left: 20px; }
            .status { color: #00c853; font-size: 1.2rem; }
            a { color: #8b5cf6; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 NAJARRO X STUDIO</h1>
            <p class="status">✅ SISTEMA ACTIVO CON WEBHOOK</p>
            <p>📧 Envío automático de credenciales</p>
            <p>⚡ Respuesta inmediata</p>
            <p>🔒 Producto permitido: prod_hvmtars6</p>
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
        "producto_id": PRODUCTO_ID_PERMITIDO,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "version": "2.1"
    })

@app.route('/health')
def health():
    return "OK", 200

# ============================================
# EJECUCIÓN PRINCIPAL
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Iniciando servidor en puerto {port}")
    logger.info(f"🔒 Producto permitido: {PRODUCTO_ID_PERMITIDO}")
    app.run(host='0.0.0.0', port=port, debug=False)
