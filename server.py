#!/usr/bin/env python3
# server.py - Servidor Flask con webhook y portal de descarga protegido

from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import os
import logging
import hashlib
import random
import string
import secrets
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

# LINK PRIVADO DE GOOGLE DRIVE (NO COMPARTIR, solo lo usa el servidor)
# Cambia TU_ID_AQUI por el ID real de tu archivo
LINK_PRIVADO_DRIVE = "https://drive.google.com/uc?export=download&id=1MX2gjwNU6JfEWGVkXnrueZUQMKBSyRcW"

# Diccionario temporal para guardar contraseñas y tokens
# Estructura: {email: {"contrasena": "NX-...", "timestamp": 1234567890, "token": "..."}}
descargas_autorizadas = {}

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
            # GENERAR CONTRASEÑA Y GUARDAR
            # ========================================
            contrasena = generar_contrasena(email)
            
            # Guardar en el diccionario temporal
            descargas_autorizadas[email] = {
                "contrasena": contrasena,
                "timestamp": datetime.now().timestamp(),
                "nombre": nombre
            }
            logger.info(f"🔐 Contraseña generada para {email}: {contrasena}")
            
            # ========================================
            # ENVIAR EMAIL
            # ========================================
            exito = enviar_email(email, nombre, contrasena)
            
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
# PORTAL DE DESCARGA PROTEGIDO
# ============================================

@app.route('/descargar', methods=['GET'])
def mostrar_formulario_descarga():
    """Muestra el formulario para ingresar email y contraseña"""
    html_form = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>NAJARRO X - Descarga tu pack</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Space Mono', monospace; 
                background: #0a0a0a; 
                color: white; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh;
                padding: 20px;
            }
            .card { 
                background: #1a1a1a; 
                padding: 40px; 
                border: 3px solid #8b5cf6; 
                max-width: 450px; 
                width: 100%;
                box-shadow: 10px 10px 0 rgba(139,92,246,0.3);
            }
            h1 { 
                font-size: 1.8rem; 
                margin-bottom: 20px; 
                border-left: 4px solid #8b5cf6; 
                padding-left: 15px;
            }
            p { margin-bottom: 25px; color: #aaa; font-size: 0.9rem; }
            input { 
                width: 100%; 
                padding: 12px; 
                margin: 10px 0; 
                background: #2a2a2a; 
                border: 1px solid #444; 
                color: white; 
                font-family: monospace;
                font-size: 0.9rem;
            }
            input:focus { outline: none; border-color: #8b5cf6; }
            button { 
                background: #8b5cf6; 
                color: black; 
                padding: 12px; 
                border: none; 
                cursor: pointer; 
                width: 100%; 
                font-weight: bold; 
                font-size: 1rem;
                margin-top: 10px;
                font-family: monospace;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            button:hover { background: #a078f8; }
            .error { color: #ff4444; margin-top: 15px; text-align: center; }
            footer { margin-top: 30px; text-align: center; font-size: 0.7rem; color: #555; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🔐 DESCARGAR PACK</h1>
            <p>Ingresa los datos que recibiste en tu correo electrónico.</p>
            <form method="POST" action="/descargar">
                <input type="email" name="email" placeholder="Tu email" required>
                <input type="password" name="contrasena" placeholder="Contraseña (ej: NX-XXXXXXXX)" required>
                <button type="submit">VALIDAR Y DESCARGAR</button>
            </form>
            <footer>NAJARRO X ESTUDIO · 2026</footer>
        </div>
    </body>
    </html>
    """
    return html_form, 200

@app.route('/descargar', methods=['POST'])
def procesar_descarga():
    """Valida email y contraseña, y redirige al link de descarga"""
    email = request.form.get('email')
    contrasena = request.form.get('contrasena')
    
    # Buscar en el diccionario temporal
    datos = descargas_autorizadas.get(email)
    
    if not datos:
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Error</title><meta http-equiv="refresh" content="3;url=/descargar"></head>
        <body style="background:#0a0a0a; color:white; font-family:monospace; text-align:center; padding-top:50px;">
            <div style="background:#1a1a1a; padding:30px; border:3px solid #ff4444; max-width:400px; margin:auto;">
                <h2>❌ EMAIL NO ENCONTRADO</h2>
                <p>No hay ninguna compra asociada a este email.</p>
                <p>Redirigiendo al formulario...</p>
            </div>
        </body>
        </html>
        """, 403
    
    if datos["contrasena"] != contrasena:
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Error</title><meta http-equiv="refresh" content="3;url=/descargar"></head>
        <body style="background:#0a0a0a; color:white; font-family:monospace; text-align:center; padding-top:50px;">
            <div style="background:#1a1a1a; padding:30px; border:3px solid #ff4444; max-width:400px; margin:auto;">
                <h2>❌ CONTRASEÑA INCORRECTA</h2>
                <p>La contraseña ingresada no es válida.</p>
                <p>Redirigiendo al formulario...</p>
            </div>
        </body>
        </html>
        """, 403
    
    # Verificar que no haya expirado (7 días)
    if datetime.now().timestamp() - datos["timestamp"] > 7 * 24 * 3600:
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Expirado</title><meta http-equiv="refresh" content="3;url=/descargar"></head>
        <body style="background:#0a0a0a; color:white; font-family:monospace; text-align:center; padding-top:50px;">
            <div style="background:#1a1a1a; padding:30px; border:3px solid #ff4444; max-width:400px; margin:auto;">
                <h2>⏰ ENLACE EXPIRADO</h2>
                <p>Este enlace de descarga expiró después de 7 días.</p>
                <p>Contacta a soporte para obtener ayuda.</p>
            </div>
        </body>
        </html>
        """, 403
    
    # Generar token único para esta sesión
    token = secrets.token_urlsafe(32)
    descargas_autorizadas[email]["token"] = token
    
    # Redirigir a la página de descarga con token
    return redirect(url_for('mostrar_link_descarga', token=token))

@app.route('/descargar/<token>')
def mostrar_link_descarga(token):
    """Muestra el link de descarga por única vez (o por tiempo limitado)"""
    # Buscar el email por el token
    email_encontrado = None
    for email, datos in descargas_autorizadas.items():
        if datos.get("token") == token:
            email_encontrado = email
            break
    
    if not email_encontrado:
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Error</title><meta http-equiv="refresh" content="3;url=/descargar"></head>
        <body style="background:#0a0a0a; color:white; font-family:monospace; text-align:center; padding-top:50px;">
            <div style="background:#1a1a1a; padding:30px; border:3px solid #ff4444; max-width:400px; margin:auto;">
                <h2>❌ ENLACE INVÁLIDO</h2>
                <p>El enlace que usaste no es válido o ya fue utilizado.</p>
                <p>Redirigiendo al formulario...</p>
            </div>
        </body>
        </html>
        """, 404
    
    datos = descargas_autorizadas[email_encontrado]
    
    # Opcional: eliminar el token para que no se pueda reutilizar (descarga única)
    # del datos["token"]
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>NAJARRO X - Descarga tu pack</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Space Mono', monospace; 
                background: #0a0a0a; 
                color: white; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh;
                padding: 20px;
            }}
            .card {{ 
                background: #1a1a1a; 
                padding: 40px; 
                border: 3px solid #00c853; 
                max-width: 550px; 
                width: 100%;
                text-align: center;
                box-shadow: 10px 10px 0 rgba(0,200,83,0.3);
            }}
            h1 {{ color: #00c853; margin-bottom: 20px; }}
            p {{ margin: 15px 0; color: #ddd; }}
            .link-descarga {{
                display: inline-block;
                background: #00c853;
                color: black;
                padding: 15px 30px;
                text-decoration: none;
                font-weight: bold;
                font-size: 1.2rem;
                margin: 20px 0;
                border: none;
                cursor: pointer;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
            .link-descarga:hover {{ background: #00e060; }}
            .aviso {{ font-size: 0.75rem; color: #888; margin-top: 20px; }}
            footer {{ margin-top: 30px; font-size: 0.7rem; color: #555; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>✅ ¡DESCARGA LISTA!</h1>
            <p>Hola <strong>{datos.get('nombre', 'Cliente')}</strong>, tu pack está listo.</p>
            <p>Haz clic en el botón para descargar el archivo ZIP.</p>
            <a href="{LINK_PRIVADO_DRIVE}" class="link-descarga">📦 DESCARGAR ZIP</a>
            <p class="aviso">⚠️ Este enlace caducará en 7 días desde tu compra.<br>No lo compartas con nadie.</p>
            <footer>NAJARRO X ESTUDIO · 2026</footer>
        </div>
    </body>
    </html>
    """

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
            <p>🔒 Portal de descarga protegido</p>
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
        "descargas_activas": len(descargas_autorizadas),
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "version": "5.0-portal"
    })

@app.route('/health')
def health():
    return "OK", 200

# ============================================
# EJECUCIÓN PRINCIPAL
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Servidor iniciado en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
