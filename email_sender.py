#!/usr/bin/env python3
# email_sender.py - Envía email con link al PORTAL (no directo a Drive)

import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURACIÓN
# ============================================

GMAIL_USER = os.environ.get('GMAIL_USER', 'najarrox.exe@gmail.com')
GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD', 'azqi nwuq wyfs ksla')

# URL del portal de descarga (no el link directo de Drive)
PORTAL_URL = "https://najarroxvjsetmail.onrender.com/descargar"

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def enviar_email(destinatario, nombre_cliente, contrasena):
    """
    Envía email con link al PORTAL (no al link directo de Drive)
    """
    
    if not GMAIL_USER or not GMAIL_PASSWORD:
        logger.error("❌ Credenciales de Gmail no configuradas")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = destinatario
    msg['Subject'] = "🎬 NAJARRO X - Tu bundle ya está listo para descargar"
    
    html = f"""
    <html>
      <body style="font-family: 'Space Mono', monospace; background: #fafafa; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border: 3px solid black; padding: 30px; box-shadow: 8px 8px 0 black;">
          
          <h1 style="font-size: 2rem; border-left: 8px solid #8b5cf6; padding-left: 20px;">
            ¡Gracias por tu compra, {nombre_cliente}!
          </h1>
          
          <p>Tu <strong>INFINITESCOUTS VJ LOOP BUNDLE</strong> (100 loops en Full HD) está lista para descargar.</p>
          
          <div style="background: black; color: white; padding: 20px; margin: 20px 0;">
            <p>🔗 LINK PARA DESCARGAR (portal seguro):</p>
            <p><a href="{PORTAL_URL}" style="color: #8b5cf6; word-break: break-all;">{PORTAL_URL}</a></p>
            
            <p style="margin-top: 15px;">🔐 TU CONTRASEÑA ÚNICA:</p>
            <p style="font-size: 1.5rem; font-weight: bold; letter-spacing: 2px;">{contrasena}</p>
          </div>
          
          <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #8b5cf6;">
            <p><strong>Instrucciones:</strong></p>
            <p>1. Abre el link de arriba</p>
            <p>2. Ingresa tu email y la contraseña única</p>
            <p>3. Haz clic en "Validar y descargar"</p>
            <p>4. Descarga el archivo ZIP completo</p>
            <p>5. Descomprime y usa tus loops</p>
          </div>
          
          <p style="font-size: 0.7rem; color: #666; margin-top: 30px;">
            ⚠️ El enlace de descarga caduca en 7 días.<br>
            ⚠️ No compartas tu contraseña con nadie.<br>
            NAJARRO X ESTUDIO · Panamá · 2026
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
        logger.error(f"❌ Error enviando email: {e}")
        return False
