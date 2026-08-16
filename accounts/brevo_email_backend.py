"""Backend de email Django que envía por la API HTTP de Brevo.

POR QUÉ: el SMTP de Brevo (smtp-relay.brevo.com:587) bloquea a nivel TCP las
conexiones desde IPs de datacenter como las de Render — el connect se cuelga,
gunicorn mata al worker con SystemExit y el signup/login explotan en 500.
La API HTTP (https://api.brevo.com/v3/smtp/email, puerto 443) NO está
bloqueada desde ningún lugar.

Este backend implementa django.core.mail.backends.base.BaseEmailBackend, así
que TODO el código existente (EmailMultiAlternatives + .send()) funciona sin
cambios: Django construye los mensajes y este backend los manda por la API.

Configuración (settings.py):
    BREVO_API_KEY = env('BREVO_API_KEY', default='')
    if BREVO_API_KEY:
        EMAIL_BACKEND = 'accounts.brevo_email_backend.BrevoEmailBackend'

Errores: si la API falla, se lanza la excepción (como haría el backend SMTP)
para que el blindaje de accounts/emails.py, orders/emails.py y
accounts/adapters.py la degrade a warning sin romper el flujo.
"""
import logging

import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address
from email.utils import parseaddr

logger = logging.getLogger(__name__)

BREVO_API_URL = 'https://api.brevo.com/v3/smtp/email'


def _split_address(addr):
    """'FerrelonStock <no-reply@x.com>' -> {'name': ..., 'email': ...}"""
    name, email = parseaddr(addr)
    if not email:
        email = str(addr)
    if not name:
        name = email.split('@')[0]
    return {'name': name, 'email': email}


def _addresses(addrs):
    return [_split_address(str(a)) for a in addrs]


class BrevoEmailBackend(BaseEmailBackend):
    """Envía emails por la API REST de Brevo en vez de SMTP."""

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        sent = 0
        for message in email_messages:
            if self._send(message):
                sent += 1
        return sent

    def _send(self, message):
        # Extraer el cuerpo HTML de las alternativas (EmailMultiAlternatives
        # guarda el HTML en message.alternatives como (content, 'text/html')).
        html = None
        for content, mimetype in getattr(message, 'alternatives', []):
            if mimetype == 'text/html':
                html = content
                break

        sender = _split_address(message.from_email)
        payload = {
            'sender': sender,
            'to': _addresses(message.to),
            'subject': message.subject,
            'textContent': message.body,
        }
        if html:
            payload['htmlContent'] = html
        if getattr(message, 'cc', None):
            payload['cc'] = _addresses(message.cc)
        if getattr(message, 'bcc', None):
            payload['bcc'] = _addresses(message.bcc)
        if getattr(message, 'reply_to', None):
            payload['replyTo'] = _split_address(message.reply_to[0])

        api_key = getattr(message, 'brevo_api_key', None) or self._get_api_key()
        headers = {
            'api-key': api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        try:
            resp = requests.post(
                BREVO_API_URL,
                json=payload,
                headers=headers,
                timeout=10,
            )
        except requests.RequestException as exc:
            logger.warning('Brevo API: error de red al enviar a %s: %s', message.to, exc, exc_info=True)
            raise

        if resp.status_code not in (200, 201):
            logger.warning(
                'Brevo API: error %s enviando a %s: %s',
                resp.status_code, message.to, resp.text[:300],
            )
            raise ConnectionError(f'Brevo API respondió {resp.status_code}')

        return True

    def _get_api_key(self):
        from django.conf import settings
        return getattr(settings, 'BREVO_API_KEY', '')