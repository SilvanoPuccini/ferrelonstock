import logging

from allauth.account.adapter import DefaultAccountAdapter

logger = logging.getLogger(__name__)


class AccountAdapter(DefaultAccountAdapter):
    """Adapter de allauth que nunca rompe el flujo si falla el envío de email.

    Con ACCOUNT_EMAIL_VERIFICATION='mandatory', allauth envía el email de
    confirmación DURANTE el signup. Si el SMTP falla (credenciales inválidas,
    proveedor caído, etc.) sin este blindaje el registro entero explota con
    un 500. Acá capturamos el error, lo logueamos y dejamos que el flujo
    continúe: el usuario queda registrado y puede pedir un reenvío.
    """

    def send_mail(self, template_prefix, email, context):
        try:
            super().send_mail(template_prefix, email, context)
        except Exception:
            logger.warning(
                'No se pudo enviar el email de allauth (%s) a %s',
                template_prefix,
                email,
                exc_info=True,
            )
