#!/usr/bin/env python3
# server.py - Servidor Flask con webhook para Recurrente
# VERSIÓN CON DIAGNÓSTICO - Registra todo lo que llega

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

# ============================================
# WEBHOOK - CON DIAGNÓSTICO COMPLETO
# ============================================

@app.route('/webhook', methods=['POST'])
def webhook_recurrente():
    """Endpoint que Recurrente (Svix) llama cuando hay un evento"""
    
    # ========================================
    # DIAGNÓSTICO: Registrar TODO lo que llega
    # ========================================
    logger.info("=" * 60)
    logger.info("🔍 DIAGNÓSTICO: Webhook recibido")
    logger.info(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Registrar headers
    logger.info("📋 HEADERS:")
    for key, value in dict(request.headers).items():
        logger.info(f"    {key}: {value}")
    
    # 2. Registrar cuerpo raw (texto plano)
    raw_data = request.get_data(as_text=True)
    logger.info(f"📄 CUERPO RAW (texto): {raw_data[:500]}{'...' if len(raw_data) > 500 else ''}")
    
    # 3. Intentar parsear como JSON
    data = None
    try:
        data = request.get_json()
        logger.info("✅ JSON parseado correctamente")
        logger.info(f"📊 JSON COMPLETO:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        logger.error(f"❌ Error parseando JSON: {e}")
    
    # 4. Si no hay datos, responder
    if not data:
        logger.warning("⚠️ No se pudo obtener JSON válido")
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400
    
    # ========================================
    # PROCESAR EL EVENTO
    # ========================================
    
    # Extraer el tipo de evento (puede estar en diferentes lugares)
    event_type = data.get('type')
    if not event_type:
        event_type = data.get('event')
    if not event_type:
        event_type = data.get('event_type')
    
    logger.info(f"📨 Tipo de evento detectado: {event_type}")
    
    # Solo procesar pagos exitosos
    if event_type == 'payment_intent.succeeded':
        logger.info("✅ Evento es 'payment_intent.succeeded', procesando...")
        
        # Extraer los datos del pago (pueden estar en diferentes lugares)
        payment_data = data.get('data', {})
        if not payment_data:
            payment_data = data.get('payload', {})
        if not payment_data:
            payment_data = data
        
        logger.info(f"📦 Datos del pago: {list(payment_data.keys())}")
        
        # ========================================
        # EXTRAER ID DEL PRODUCTO
        # ========================================
        producto_comprado_id = None
        
        # Buscar en items
        items = payment_data.get('items', [])
        if items and len(items) > 0:
            item = items[0]
            producto_comprado_id = item.get('product_id')
            if not producto_comprado_id:
                producto_comprado_id = item.get('id')
            if not producto_comprado_id:
                producto_comprado_id = item.get('product')
            if not producto_comprado_id and 'product' in item:
                producto_comprado_id = item['product'].get('id') if isinstance(item['product'], dict) else item['product']
        
        # Buscar en product
        if not producto_comprado_id:
            product = payment_data.get('product', {})
            producto_comprado_id = product.get('id')
        
        # Buscar en price
        if not producto_comprado_id:
            price = payment_data.get('price', {})
            producto_comprado_id = price.get('product_id')
        
        logger.info(f"🏷️ ID del producto extraído: {producto_comprado_id}")
        
        # ========================================
        # VERIFICAR PRODUCTO
        # ========================================
        if producto_comprado_id != PRODUCTO_ID_PERMITIDO:
            logger.warning(f"⚠️ Producto NO autorizado: {producto_comprado_id} (Esperado: {PRODUCTO_ID_PERMITIDO})")
            return jsonify({"status": "ignored", "reason": "invalid product"}), 200
        
        logger.info(f"✅ Producto verificado: {producto_comprado_id}")
        
        # ========================================
        # EXTRAER EMAIL DEL CLIENTE
        # ========================================
        email = None
        
        # Buscar en customer
        customer = payment_data.get('customer', {})
        email = customer.get('email')
        
        # Buscar directamente
        if not email:
            email = payment_data.get('customer_email')
        if not email:
            email = payment_data.get('email')
        
        # Buscar en metadata
        if not email:
            metadata = payment_data.get('metadata', {})
            email = metadata.get('email')
        
        # Buscar en payload
        if not email:
            payload = data.get('payload', {})
            customer = payload.get('customer', {})
            email = customer.get('email')
        
        # ========================================
        # EXTRAER NOMBRE DEL CLIENTE
        # ========================================
        nombre = "Cliente"
        
        if customer:
            nombre = customer.get('name', nombre)
        if not nombre or nombre == "Cliente":
            nombre = payment_data.get('customer_name', nombre)
        if not nombre or nombre == "Cliente":
            nombre = payment_data.get('name', nombre)
        
        # ========================================
        # VERIFICAR EMAIL
        # ========================================
        if not email:
            logger.error("❌ No se pudo extraer el email del cliente")
            logger.info(f"Datos disponibles en payment_data: {list(payment_data.keys())}")
            return jsonify({"status": "error", "message": "No email found"}), 400
        
        logger.info(f"📧 Cliente: {nombre} <{email}>")
        
        # ========================================
        # GENERAR CONTRASEÑA Y ENVIAR EMAIL
        # ========================================
        contrasena = generar_contrasena(email)
        
        exito = enviar_email(email, nombre, contrasena, LINK_DESCARGA)
        
        if exito:
            logger.info(f"✅ Email enviado exitosamente a {email}")
            return jsonify({"status": "ok", "message": "Email sent"}), 200
        else:
            logger.error(f"❌ Falló el envío de email a {email}")
            return jsonify({"status": "error", "message": "Email failed"}), 500
    
    # Evento no es payment.succeeded
    logger.info(f"Evento ignorado (no es payment.succeeded): {event_type}")
    return jsonify({"status": "ignored", "event": event_type}), 200

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
            <p class="status">✅ SISTEMA ACTIVO CON WEBHOOK</p>
            <p>📧 Envío automático de credenciales</p>
            <p>⚡ Respuesta inmediata</p>
            <p>🔒 Producto permitido: prod_hvmtars6</p>
            <p>🔍 Modo diagnóstico activo</p>
            <p>📊 <a href="/status">Ver estado</a></p>
        </div>
    </body>
    </html>
    """

@app.route('/status')
def status():
    return jsonify({
        "status": "activo",
        "modo": "diagnostico",
        "producto_id": PRODUCTO_ID_PERMITIDO,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "version": "3.0-diagnostico"
    })

@app.route('/health')
def health():
    return "OK", 200

# ============================================
# EJECUCIÓN PRINCIPAL
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO SERVIDOR CON DIAGNÓSTICO")
    logger.info(f"🌐 Puerto: {port}")
    logger.info(f"🔒 Producto permitido: {PRODUCTO_ID_PERMITIDO}")
    logger.info("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False)
