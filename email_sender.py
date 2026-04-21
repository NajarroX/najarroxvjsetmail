#!/usr/bin/env python3
# email_sender.py - Envía emails con el link de descarga

import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURACIÓN (LEER DE VARIABLES DE ENTORNO)
# ============================================

GMAIL_USER = os.environ.get('GMAIL_USER', '')
GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD', '')

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def enviar_email(destinatario, nombre_cliente, contrasena, link_descarga):
    """
    Envía email con link de descarga y contraseña
    """
    
    if not GMAIL_USER or not GMAIL_PASSWORD:
        logger.error("❌ Credenciales de Gmail no configuradas")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = destinatario
    msg['Subject'] = "🎬 NAJARRO X - Tu pack ya está listo"
    
    html = f"""
    <html>
      <body style="font-family: 'Space Mono', monospace; background: #fafafa; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border: 3px solid black; padding: 30px; box-shadow: 8px 8px 0 black;">
          
          <h1 style="font-size: 2rem; border-left: 8px solid #8b5cf6; padding-left: 20px;">
            ¡Gracias por tu compra, {nombre_cliente}!
          </h1>
          
          <p>Tu <strong>INFINITESCOUTS VJ LOOP BUNDLE</strong> está lista para descargar.</p>
          <p><small>100 loops de video en HD</small></p>
          
          <div style="background: black; color: white; padding: 20px; margin: 20px 0;">
            <p>🔗 LINK DE DESCARGA (haz clic para descargar el ZIP):</p>
            <p><a href="{link_descarga}" style="color: #8b5cf6; word-break: break-all;">
              {link_descarga}
            </a></p>
            
            <p style="margin-top: 15px;">🔐 CONTRASEÑA DE ACCESO (si es necesaria):</p>
            <p style="font-size: 1.5rem; font-weight: bold;">{contrasena}</p>
          </div>
          
          <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #8b5cf6;">
            <p><strong>Instrucciones:</strong></p>
            <p>1. Haz clic en el link de arriba</p>
            <p>2. Si Google Drive pide acceso, ingresa la contraseña</p>
            <p>3. Descarga el archivo ZIP completo</p>
            <p>4. Descomprime y usa tus loops</p>
          </div>
          
          <p style="font-size: 0.7rem; color: #666; margin-top: 30px;">
            ⚠️ Este link es personal e intransferible<br>
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
