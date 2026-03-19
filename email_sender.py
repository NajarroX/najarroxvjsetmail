#!/usr/bin/env python3
# email_sender.py - Versión para 1 SOLO BUNDLE

import requests
import smtplib
import hashlib
import random
import string
import logging
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURACIÓN
# ============================================
RECURRENTE_API_KEY = os.environ.get('RECURRENTE_API_KEY', '')
RECURRENTE_API_URL = "https://app.recurrente.com/api"

GMAIL_USER = os.environ.get('GMAIL_USER', '')
GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD', '')

# Archivo para registrar ventas procesadas
PROCESSED_FILE = "/tmp/ventas_procesadas.txt"

# ============================================
# DATOS DEL ÚNICO BUNDLE (CÁMBIALO UNA VEZ)
# ============================================
BUNDLE_INFO = {
    "id": "prod_hvmtars6",  # ID del producto en Recurrente
    "nombre": "INFINITESCOUTS VJ LOOP BUNDLE",
    "precio": 33,
    "link_descarga": "https://drive.google.com/file/d/1CI9OWiF7OZIyvBp-IckKsgBP80mO2RPo/view?usp=drive_link",  # LINK DIRECTO AL ZIP
    "contiene": "99 loops en HDcon estética exclusiva"
}

# ============================================
# FUNCIONES
# ============================================

def generar_contrasena(email_cliente):
    """Genera una contraseña única para cada compra"""
    base = f"{email_cliente}-{datetime.now().strftime('%Y%m%d%H')}"
    hash_obj = hashlib.md5(base.encode())
    hash_str = hash_obj.hexdigest()[:8].upper()
    extras = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"NX-{hash_str}{extras}"

def cargar_procesados():
    try:
        with open(PROCESSED_FILE, 'r') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def guardar_procesado(venta_id):
    try:
        with open(PROCESSED_FILE, 'a') as f:
            f.write(f"{venta_id}\n")
    except Exception as e:
        logger.error(f"Error guardando: {e}")

def enviar_email(destinatario, nombre_cliente, contrasena):
    """Envía email con link de descarga del ZIP"""
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = destinatario
    msg['Subject'] = f"🎬 NAJARRO X - {BUNDLE_INFO['nombre']} está listo"
    
    html = f"""
    <html>
      <body style="font-family: monospace; background: #fafafa; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border: 3px solid black; padding: 30px;">
          
          <h1 style="border-left: 8px solid #8b5cf6; padding-left: 20px;">
            ¡Gracias por tu compra, {nombre_cliente}!
          </h1>
          
          <p>Tu <strong>{BUNDLE_INFO['nombre']}</strong> está listo para descargar.</p>
          <p><small>{BUNDLE_INFO['contiene']}</small></p>
          
          <div style="background: black; color: white; padding: 20px; margin: 20px 0;">
            <p>🔗 LINK DE DESCARGA (solo 1 archivo ZIP):</p>
            <p><a href="{BUNDLE_INFO['link_descarga']}" style="color: #8b5cf6; word-break: break-all;">
              {BUNDLE_INFO['link_descarga']}
            </a></p>
            
            <p style="margin-top: 15px;">🔐 CONTRASEÑA DEL LINK (si es necesario):</p>
            <p style="font-size: 1.5rem; font-weight: bold;">{contrasena}</p>
          </div>
          
          <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #8b5cf6;">
            <p><strong>Instrucciones:</strong></p>
            <p>1. Haz clic en el link de arriba</p>
            <p>2. Si Google Drive pide acceso, ingresa la contraseña</p>
            <p>3. Descarga el archivo ZIP completo</p>
            <p>4. Descomprime en tu computadora</p>
          </div>
          
          <p style="font-size: 0.7rem; color: #666; margin-top: 30px;">
            ⚠️ Link personal e intransferible · Expira en 7 días<br>
            NAJARRO X ESTUDIO · Panamá
          </p>
        </div>
      </body>
    </html>
    """
    
    msg.attach(MIMEText(html, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"✅ Email enviado a {destinatario}")
        return True
    except Exception as e:
        logger.error(f"❌ Error email: {e}")
        return False

def obtener_ventas_recientes():
    """Consulta SOLO ventas de tu único producto"""
    if not RECURRENTE_API_KEY:
        logger.error("❌ API key no configurada")
        return []
    
    headers = {"Authorization": f"Bearer {RECURRENTE_API_KEY}"}
    desde = (datetime.now() - timedelta(hours=24)).isoformat()
    
    try:
        # Busca ventas del producto específico
        response = requests.get(
            f"{RECURRENTE_API_URL}/sales",
            headers=headers,
            params={
                "created_after": desde, 
                "status": "paid",
                "product_id": BUNDLE_INFO["id"]  # Filtra por tu bundle
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error API: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error conexión: {e}")
        return []

def procesar_ventas():
    """Versión simplificada para 1 producto"""
    logger.info("🔍 Verificando nuevas ventas...")
    
    procesadas = cargar_procesados()
    ventas = obtener_ventas_recientes()
    
    if not ventas:
        return 0
    
    nuevas = 0
    for venta in ventas:
        venta_id = venta.get('id')
        if venta_id in procesadas:
            continue
        
        cliente = venta.get('customer', {})
        email = cliente.get('email')
        nombre = cliente.get('name', 'Cliente')
        
        if not email:
            continue
        
        # Generar contraseña única
        contrasena = generar_contrasena(email)
        
        # Enviar email con el link fijo del ZIP
        exito = enviar_email(email, nombre, contrasena)
        
        if exito:
            guardar_procesado(venta_id)
            nuevas += 1
            logger.info(f"✅ Venta {venta_id}: {email}")
    
    return nuevas

if __name__ == "__main__":
    procesar_ventas()