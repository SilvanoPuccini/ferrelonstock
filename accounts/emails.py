import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _site_url():
    """URL absoluta del sitio para usar en los templates de bienvenida."""
    try:
        return f'https://{Site.objects.get_current().domain}'
    except Exception:
        return 'https://ferrelonstock.onrender.com'


def send_welcome_email(user):
    """Email de bienvenida al registrarse (adicional al de confirmación).

    Nunca rompe el flujo de signup: cualquier fallo de envío se loguea
    como warning y se ignora (mismo patrón que orders/emails.py).
    """
    subject = '¡Bienvenido a FerrelonStock!'
    if not user.email:
        return
    try:
        context = {
            'user': user,
            'first_name': user.first_name or user.email.split('@')[0],
            'site_url': _site_url(),
        }
        html_body = render_to_string('emails/welcome.html', context)
        text_body = render_to_string('emails/welcome.txt', context)
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_body, 'text/html')
        email.send()
    except Exception:
        logger.warning(
            'No se pudo enviar el email de bienvenida a %s',
            user.email,
            exc_info=True,
        )
