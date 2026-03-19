#!/usr/bin/env python3
# email_sender.py - Versión para ser llamada desde server.py

import requests
import smtplib
import hashlib
import random
import string
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ============================================
# CONFIGURACIÓN (MISMA QUE ANTES)
# ============================================
RECURRENTE_API_KEY = "pk_live_eCN782t92ueN50AKk81roQth9SN7TfLACERJ6JPH7hKs0EBrgmYv7bmMy"
RECURRENTE_API_URL = "https://app.recurrente.com/api"
GMAIL_USER = "najarrox@gmail.com"
GMAIL_PASSWORD = "Ch4p1n4frnkt1m0th!"
PROCESSED_FILE = "/tmp/ventas_procesadas.txt"  # Cambiado a /tmp/ para Render

PACK_LINKS = {
    "esencial": "https://sites.google.com/view/nx-descargas/pack-esencial",
    "pro": "https://sites.google.com/view/nx-descargas/pack-pro",
    "ultimate": "https://sites.google.com/view/nx-descargas/pack-ultimate",
    "sci-fi": "https://sites.google.com/view/nx-descargas/sci-fi",
    "glitch": "https://sites.google.com/view/nx-descargas/glitch",
    "brutalismo": "https://sites.google.com/view/nx-descargas/brutalismo",
    "psicodelia": "https://sites.google.com/view/nx-descargas/psicodelia",
    "astral": "https://sites.google.com/view/nx-descargas/astral",
}

def generar_contrasena(pack, email_cliente):
    """Genera contraseña única"""
    base = f"{pack}-{email_cliente}-{datetime.now().strftime('%Y%m%d%H')}"
    hash_obj = hashlib.md5(base.encode())
    hash_str = hash_obj.hexdigest()[:6].upper()
    
    prefijo = pack[:3].upper() if pack in ["sci-fi", "glitch", "brutalismo", "psicodelia", "astral"] else pack[:3].upper()
    extras = ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
    return f"NX-{prefijo}-{hash_str}{extras}"

def cargar_procesados():
    """Carga IDs procesados"""
    try:
        with open(PROCESSED_FILE, 'r') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def guardar_procesado(venta_id):
    """Guarda ID procesado"""
    with open(PROCESSED_FILE, 'a') as f:
        f.write(f"{venta_id}\n")

def enviar_email(destinatario, nombre_cliente, pack_seleccionado, contrasena):
    """Envía email con credenciales"""
    link_descarga = PACK_LINKS.get(pack_seleccionado, "https://sites.google.com/view/nx-descargas")
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = destinatario
    msg['Subject'] = f"🎬 NAJARRO X - Tu pack {pack_seleccionado} está listo"
    
    html = f"""
    <html>
      <body style="font-family: monospace; background: #fafafa; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border: 3px solid black; padding: 30px;">
          <h1 style="border-left: 8px solid #8b5cf6; padding-left: 20px;">
            ¡Gracias, {nombre_cliente}!
          </h1>
          <p>Tu pack <strong>{pack_seleccionado}</strong> está listo.</p>
          <div style="background: black; color: white; padding: 20px;">
            <p>🔗 LINK: <a href="{link_descarga}" style="color: #8b5cf6;">{link_descarga}</a></p>
            <p style="font-size: 1.5rem;">🔐 {contrasena}</p>
          </div>
          <p style="font-size: 0.7rem;">⚠️ Uso personal e intransferible</p>
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
        return True
    except Exception as e:
        print(f"Error email: {e}")
        return False

def obtener_ventas_recientes():
    """Consulta API Recurrente"""
    headers = {"Authorization": f"Bearer {RECURRENTE_API_KEY}"}
    desde = (datetime.now() - timedelta(hours=24)).isoformat()
    
    try:
        response = requests.get(f"{RECURRENTE_API_URL}/sales", headers=headers, params={"created_after": desde, "status": "paid"})
        return response.json() if response.status_code == 200 else []
    except:
        return []

def procesar_ventas():
    """Función principal que se ejecuta cada 5 minutos"""
    print(f"[{datetime.now()}] Verificando ventas...")
    
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
        
        items = venta.get('items', [])
        if not items:
            continue
            
        producto = items[0].get('product', {})
        pack_id = producto.get('id')
        
        # MAPEO - AJUSTA SEGÚN TUS IDs
        mapeo = {
            "prod_123456": "sci-fi",
            "prod_123457": "glitch",
            "prod_123458": "brutalismo",
            "prod_123459": "psicodelia",
            "prod_123460": "astral",
            "prod_123461": "esencial",
            "prod_123462": "pro",
            "prod_123463": "ultimate",
        }
        
        pack = mapeo.get(producto.get('id'), "esencial")
        contrasena = generar_contrasena(pack, email)
        
        if enviar_email(email, nombre, pack, contrasena):
            guardar_procesado(venta_id)
            nuevas += 1
            print(f"✅ Enviado a {email} - Pack: {pack}")
    
    return nuevas