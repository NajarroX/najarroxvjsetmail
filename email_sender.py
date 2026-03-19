#!/usr/bin/env python3
# email_sender.py - Versión mejorada con logging

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

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURACIÓN (LEER DE VARIABLES DE ENTORNO)
# ============================================

RECURRENTE_API_KEY = os.environ.get('RECURRENTE_API_KEY', '')
RECURRENTE_API_URL = "https://app.recurrente.com/api"  # Ajusta según documentación real

GMAIL_USER = os.environ.get('GMAIL_USER', '')
GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD', '')
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Archivo para llevar registro de ventas ya procesadas (en /tmp/ para Render)
PROCESSED_FILE = "/tmp/ventas_procesadas.txt"

# Mapeo de packs a links de descarga (CÁMBIALO POR TUS URLs REALES)
PACK_LINKS = {
    "sci-fi": "https://sites.google.com/view/nx-descargas/sci-fi",
    "glitch": "https://sites.google.com/view/nx-descargas/glitch",
    "brutalismo": "https://sites.google.com/view/nx-descargas/brutalismo",
    "psicodelia": "https://sites.google.com/view/nx-descargas/psicodelia",
    "astral": "https://sites.google.com/view/nx-descargas/astral",
    "esencial": "https://sites.google.com/view/nx-descargas/esencial",
    "pro": "https://sites.google.com/view/nx-descargas/pro",
    "ultimate": "https://sites.google.com/view/nx-descargas/ultimate",
}

# ============================================
# FUNCIONES
# ============================================

def generar_contrasena(pack, email_cliente):
    """
    Genera una contraseña única para cada compra.
    Formato: NX-[PACK]-[HASH 6 CARACTERES]
    Ejemplo: NX-SCI-8F3K25
    """
    base = f"{pack}-{email_cliente}-{datetime.now().strftime('%Y%m%d%H')}"
    hash_obj = hashlib.md5(base.encode())
    hash_str = hash_obj.hexdigest()[:6].upper()
    
    # Obtener prefijo del pack
    if pack in ["sci-fi", "glitch", "brutalismo", "psicodelia", "astral"]:
        prefijo = pack[:3].upper()
    elif pack == "esencial":
        prefijo = "ESC"
    elif pack == "pro":
        prefijo = "PRO"
    elif pack == "ultimate":
        prefijo = "ULT"
    else:
        prefijo = "PK"
    
    extras = ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
    
    return f"NX-{prefijo}-{hash_str}{extras}"

def cargar_procesados():
    """Carga IDs de ventas ya procesadas desde archivo"""
    try:
        with open(PROCESSED_FILE, 'r') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def guardar_procesado(venta_id):
    """Guarda ID de venta procesada"""
    try:
        with open(PROCESSED_FILE, 'a') as f:
            f.write(f"{venta_id}\n")
    except Exception as e:
        logger.error(f"Error guardando ID procesado: {e}")

def enviar_email(destinatario, nombre_cliente, pack_seleccionado, contrasena):
    """
    Envía email con link de descarga y contraseña
    """
    
    link_descarga = PACK_LINKS.get(pack_seleccionado, "https://sites.google.com/view/nx-descargas")
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = destinatario
    msg['Subject'] = f"🎬 NAJARRO X - Tu pack {pack_seleccionado} está listo"
    
    html = f"""
    <html>
      <body style="font-family: 'Space Mono', monospace; background: #fafafa; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border: 3px solid black; padding: 30px; box-shadow: 8px 8px 0 black;">
          
          <h1 style="font-size: 2rem; letter-spacing: -1px; border-left: 8px solid #8b5cf6; padding-left: 20px;">
            ¡Gracias por tu compra, {nombre_cliente}!
          </h1>
          
          <p style="font-family: monospace; font-size: 0.9rem; margin: 20px 0;">
            Tu pack <strong>{pack_seleccionado}</strong> está listo para descargar.
          </p>
          
          <div style="background: black; color: white; padding: 20px; margin: 20px 0;">
            <p style="margin: 5px 0;">🔗 LINK DE DESCARGA:</p>
            <p style="margin: 5px 0; font-size: 0.8rem; word-break: break-all;">
              <a href="{link_descarga}" style="color: #8b5cf6;">{link_descarga}</a>
            </p>
            
            <p style="margin: 15px 0 5px 0;">🔐 CONTRASEÑA DE ACCESO:</p>
            <p style="margin: 5px 0; font-size: 1.5rem; font-weight: bold; letter-spacing: 2px;">
              {contrasena}
            </p>
          </div>
          
          <div style="font-family: monospace; font-size: 0.85rem; background: #f5f5f5; padding: 15px; border-left: 4px solid #8b5cf6;">
            <p><strong>Instrucciones:</strong></p>
            <p>1. Abre el link de descarga</p>
            <p>2. Ingresa la contraseña exacta (respetar mayúsculas)</p>
            <p>3. Haz clic en los archivos para descargar</p>
          </div>
          
          <p style="font-size: 0.7rem; color: #666; margin-top: 30px;">
            ⚠️ Este link y contraseña son personales e intransferibles.<br>
            NAJARRO X ESTUDIO · Panamá · 2026
          </p>
        </div>
      </body>
    </html>
    """
    
    msg.attach(MIMEText(html, 'html'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"✅ Email enviado a {destinatario}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enviando email: {e}")
        return False

def obtener_ventas_recientes():
    """
    Consulta la API de Recurrente para obtener ventas de las últimas 24h
    AJUSTA ESTO SEGÚN LA DOCUMENTACIÓN REAL DE RECURRENTE
    """
    if not RECURRENTE_API_KEY:
        logger.error("❌ RECURRENTE_API_KEY no configurada")
        return []
    
    headers = {
        "Authorization": f"Bearer {RECURRENTE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    desde = (datetime.now() - timedelta(hours=24)).isoformat()
    
    try:
        # ESTE ENDPOINT DEBE SER AJUSTADO SEGÚN LA API REAL DE RECURRENTE
        response = requests.get(
            f"{RECURRENTE_API_URL}/sales",
            headers=headers,
            params={"created_after": desde, "status": "paid"},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error API {response.status_code}: {response.text}")
            return []
            
    except Exception as e:
        logger.error(f"Error conectando con API: {e}")
        return []

def procesar_ventas():
    """Función principal que se ejecuta cada 5 minutos"""
    
    logger.info("🔍 Verificando nuevas ventas...")
    
    # Cargar ventas ya procesadas
    procesadas = cargar_procesados()
    
    # Obtener ventas de la API
    ventas = obtener_ventas_recientes()
    
    if not ventas:
        logger.info("ℹ️ No hay ventas nuevas o error en API")
        return 0
    
    nuevas_procesadas = 0
    
    for venta in ventas:
        venta_id = venta.get('id')
        
        # Si ya fue procesada, saltar
        if venta_id in procesadas:
            continue
        
        # Extraer datos del cliente (AJUSTA SEGÚN RESPUESTA REAL)
        cliente = venta.get('customer', {})
        email = cliente.get('email')
        nombre = cliente.get('name', 'Cliente')
        
        if not email:
            logger.warning(f"Venta {venta_id} sin email, saltando")
            continue
        
        # Extraer producto comprado (AJUSTA SEGÚN RESPUESTA REAL)
        items = venta.get('items', [])
        if not items:
            continue
        
        primer_item = items[0]
        producto = primer_item.get('product', {})
        
        # MAPEO - AJUSTA SEGÚN TUS IDs REALES DE RECURRENTE
        mapeo_productos = {
            "prod_sci_fi": "sci-fi",
            "prod_glitch": "glitch",
            "prod_brutalismo": "brutalismo",
            "prod_psicodelia": "psicodelia",
            "prod_astral": "astral",
            "prod_esencial": "esencial",
            "prod_pro": "pro",
            "prod_ultimate": "ultimate",
        }
        
        pack_id = producto.get('id', '')
        pack = mapeo_productos.get(pack_id, "esencial")
        
        # Generar contraseña única
        contrasena = generar_contrasena(pack, email)
        
        # Enviar email
        exito = enviar_email(email, nombre, pack, contrasena)
        
        if exito:
            guardar_procesado(venta_id)
            nuevas_procesadas += 1
            logger.info(f"✅ Venta {venta_id} procesada: {email} - Pack: {pack}")
    
    if nuevas_procesadas > 0:
        logger.info(f"📊 Total procesadas: {nuevas_procesadas}")
    
    return nuevas_procesadas

# Si se ejecuta directamente, hacer una prueba
if __name__ == "__main__":
    print("🧪 Probando email_sender.py directamente...")
    procesar_ventas()