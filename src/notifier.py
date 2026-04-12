import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class Notifier:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', False)
        self.email_config = config.get('email', {})
    
    def send_notification(self, publications: List[Dict[str, Any]]) -> bool:
        """Send notification about new publications"""
        if not self.enabled:
            logger.info("Notificaciones deshabilitadas")
            return False
        
        if not publications:
            logger.info("No hay publicaciones para notificar")
            return False
        
        try:
            subject = f"Nuevas Publicaciones Normativas ({len(publications)})"
            body = self._format_email_body(publications)
            
            return self._send_email(subject, body)
        except Exception as e:
            logger.error(f"Error al enviar notificación: {e}")
            return False
    
    def _format_email_body(self, publications: List[Dict[str, Any]]) -> str:
        """Format email body with publications"""
        body = """
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        .header { background-color: #2c3e50; color: white; padding: 20px; }
        .pub { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .source { font-weight: bold; color: #3498db; }
        .category { background-color: #ecf0f1; padding: 3px 8px; border-radius: 3px; font-size: 12px; }
        .date { color: #7f8c8d; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h2>Legislación Monitor - Nuevas Publicaciones</h2>
    </div>
    <p>Se han detectado las siguientes nuevas publicaciones normativas:</p>
"""
        
        for pub in publications:
            body += f"""
    <div class="pub">
        <span class="source">{pub.get('source', 'N/A').upper()}</span>
        <span class="category">{pub.get('category', 'N/A')}</span>
        <h3>{pub.get('title', 'Sin título')}</h3>
        <p class="date">Fecha: {pub.get('date', 'N/A')}</p>
        <p>{pub.get('summary', 'Sin descripción')}</p>
        <p><a href="{pub.get('url', '#')}">Ver publicación completa</a></p>
    </div>
"""
        
        body += """
    <hr>
    <p style="color: #7f8c8d; font-size: 12px;">
        Este mensaje ha sido enviado automáticamente por Legislación Monitor.
        Para configurar las notificaciones, edite el archivo config.yaml
    </p>
</body>
</html>
"""
        return body
    
    def _send_email(self, subject: str, body: str) -> bool:
        """Send email via SMTP"""
        smtp_server = self.email_config.get('smtp_server')
        smtp_port = self.email_config.get('smtp_port', 587)
        use_tls = self.email_config.get('use_tls', True)
        sender = self.email_config.get('sender')
        recipients = self.email_config.get('recipients', [])
        
        if not all([smtp_server, sender, recipients]):
            logger.error("Configuración de email incompleta")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                server.starttls()
            
            password = os.environ.get('SMTP_PASSWORD') or self.email_config.get('password')
            if password:
                server.login(sender, password)
            
            server.sendmail(sender, recipients, msg.as_string())
            server.quit()
            
            logger.info(f"Notificación enviada a {len(recipients)} destinatarios")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar email: {e}")
            return False
