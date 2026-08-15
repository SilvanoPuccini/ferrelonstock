from django.dispatch import receiver
from allauth.account.signals import user_signed_up


@receiver(user_signed_up)
def handle_user_signed_up(request, user, **kwargs):
    from .emails import send_welcome_email

    send_welcome_email(user)
