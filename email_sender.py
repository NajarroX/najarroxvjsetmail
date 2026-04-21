#!/usr/bin/env python3
# email_sender.py

import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GMAIL_USER = os.environ.get('GMAIL_USER', 'najarrox.exe@gmail.com')
GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD', 'obpg ctik ngcn ipqf')

def enviar_email(destinatario, nombre_cliente, contrasena, link_descarga):
    if not GMAIL_USER or not GMAIL_PASSWORD:
        logger.error("❌ Credenciales de Gmail no configuradas")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = destinatario
    msg['Subject'] = "🎬 NAJARRO X - Tu Bundle ya está listo"
    
    html = f"""
    <html>
      <body style="font-family: monospace;">
        <div style="max-width: 600px; margin: 0 auto; border: 3px solid black; padding: 30px;">
          <h1>¡Gracias por tu compra, {nombre_cliente}!</h1>
          <p>Tu <strong>INFINITESCOUTS VJ LOOP BUNDLE</strong> está lista.</p>
          <div style="background: black; color: white; padding: 20px;">
            <p>🔗 LINK DE DESCARGA:</p>
            <p><a href="{link_descarga}" style="color: #8b5cf6;">{link_descarga}</a></p>
            <p>🔐 CONTRASEÑA: {contrasena}</p>
          </div>
          <p>NAJARRO X ESTUDIO · Panamá · 2026</p>
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
        logger.error(f"❌ Error: {e}")
        return False
