import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _order_context(order):
    """Contexto compartido por los templates de email de pedidos."""
    items = list(order.items.all())
    subtotal = sum(item.get_total for item in items)
    return {
        'order': order,
        'items': items,
        'subtotal': subtotal,
        'shipping_price': order.shipping_price,
        'total': order.total,
        'status_display': order.get_status_display(),
    }


def _send_email(subject, to_emails, template_name, context):
    """Envía un email con alternativa HTML y texto.

    Nunca rompe el flujo principal: cualquier fallo (SMTP caído, template
    roto, etc.) se loguea como warning y se ignora.
    """
    if not to_emails:
        return
    try:
        html_body = render_to_string(f'emails/{template_name}.html', context)
        text_body = render_to_string(f'emails/{template_name}.txt', context)
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=to_emails,
        )
        email.attach_alternative(html_body, 'text/html')
        email.send()
    except BaseException:
        # BaseException, NO Exception: un SMTP colgado sin timeout hace que
        # gunicorn mate al worker con SystemExit, que NO hereda de Exception
        # y escapa de `except Exception` → 500 en checkout. Con EMAIL_TIMEOUT
        # el fallo normal es socket.timeout (Exception), pero esto garantiza
        # que el checkout NUNCA explote por un email (visto en producción).
        logger.warning(
            'No se pudo enviar el email "%s" a %s',
            subject, to_emails, exc_info=True,
        )


def send_order_confirmation(order):
    """Email al cliente confirmando que su pedido fue creado."""
    subject = f'Pedido #{order.pk} confirmado'
    _send_email(subject, [order.email], 'order_confirmation', _order_context(order))


def send_payment_confirmation(order):
    """Email al cliente avisando que el pago fue recibido y el pedido está en preparación."""
    subject = f'¡Pago recibido! Pedido #{order.pk}'
    _send_email(subject, [order.email], 'payment_confirmation', _order_context(order))


def send_order_status_update(order):
    """Email al cliente cuando cambia el estado de su pedido.

    Si el pedido ya tiene un shipment, el contexto incluye el tracking number
    y la URL del carrier para que el cliente pueda seguir el envío.
    """
    context = _order_context(order)
    shipment = getattr(order, 'shipment', None)
    context['shipment'] = shipment
    context['carrier_tracking_url'] = shipment.tracking_url if shipment else ''
    subject = f'Tu pedido #{order.pk} cambió de estado'
    _send_email(subject, [order.email], 'order_status_update', context)


def send_new_order_admin_notification(order):
    """Notificación al staff cuando se crea un pedido nuevo.

    Usa settings.NOTIFICATION_EMAIL (acepta varios separados por coma).
    Si no está configurado, no envía nada.
    """
    raw = settings.NOTIFICATION_EMAIL or ''
    recipients = [email.strip() for email in raw.split(',') if email.strip()]
    if not recipients:
        return
    subject = f'Nuevo pedido #{order.pk}'
    _send_email(subject, recipients, 'new_order_admin', _order_context(order))
