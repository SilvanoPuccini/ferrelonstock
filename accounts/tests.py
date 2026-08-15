import re
import uuid

import pytest
from django.test import Client
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test.utils import override_settings
from django.urls import reverse
from allauth.account.models import EmailAddress
from accounts.models import UserProfile


@pytest.mark.django_db
class TestUserProfile:
    def test_profile_created_on_signup(self):
        user = User.objects.create_user('newuser', 'new@test.com', 'pass123')
        assert hasattr(user, 'profile')
        assert isinstance(user.profile, UserProfile)

    def test_profile_initials(self):
        user = User.objects.create_user('initials', 'init@test.com', 'pass123')
        user.first_name = 'Juan'
        user.last_name = 'Pérez'
        user.save()
        assert user.profile.get_initials() == 'JP'

    def test_profile_initials_no_name(self):
        user = User.objects.create_user('noname', 'noname@test.com', 'pass123')
        assert len(user.profile.get_initials()) == 2


@pytest.mark.django_db
class TestProfileViews:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user('profview', 'pv@test.com', 'pass123')

    def test_profile_requires_login(self):
        response = self.client.get('/account/profile/')
        assert response.status_code == 302

    def test_profile_logged_in(self):
        self.client.login(username='profview', password='pass123')
        response = self.client.get('/account/profile/')
        assert response.status_code == 200

    def test_profile_edit(self):
        self.client.login(username='profview', password='pass123')
        response = self.client.post('/account/profile/edit/', {
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'phone': '1122334455',
            'address': 'Av. Corrientes 1234',
            'city': 'CABA',
            'region': 'Buenos Aires',
            'postal_code': 'C1043',
        })
        assert response.status_code == 302
        self.user.refresh_from_db()
        assert self.user.first_name == 'Juan'
        assert self.user.profile.city == 'CABA'


SIGNUP_URL = reverse('account_signup')
LOGIN_URL = reverse('account_login')
SIGNUP_PASSWORD = 'S3gura!Pass123'


def _fresh_email():
    """Email único por test: el cooldown de confirmación (3 min) usa el cache
    compartido y bloquearía los emails si reutilizáramos la misma dirección."""
    return f'user{uuid.uuid4().hex[:10]}@test.com'


def _signup(client, email):
    return client.post(SIGNUP_URL, {
        'email': email,
        'password1': SIGNUP_PASSWORD,
        'password2': SIGNUP_PASSWORD,
    })


def _extract_confirm_url(mail_body):
    match = re.search(r'https?://\S+', mail_body)
    assert match, 'no se encontró URL de confirmación en el email'
    return match.group(0).rstrip('.')


@pytest.mark.django_db
class TestMandatoryEmailVerification:
    def setup_method(self):
        self.client = Client()

    def test_signup_sends_confirmation_email(self, mailoutbox):
        email = _fresh_email()
        response = _signup(self.client, email)
        assert response.status_code == 302
        subjects = [m.subject for m in mailoutbox]
        assert any('Confirmá tu email' in s for s in subjects)

    def test_signup_sends_welcome_email(self, mailoutbox):
        _signup(self.client, _fresh_email())
        subjects = [m.subject for m in mailoutbox]
        assert any('Bienvenido' in s for s in subjects)

    def test_signup_does_not_log_in_until_confirmed(self, mailoutbox):
        email = _fresh_email()
        response = _signup(self.client, email)
        assert response.status_code == 302
        assert response.url == reverse('account_email_verification_sent')
        assert '_auth_user_id' not in self.client.session
        user = User.objects.get(email=email)
        address = EmailAddress.objects.get(user=user, email=email)
        assert not address.verified

    def test_login_blocked_until_confirmed(self, mailoutbox):
        email = _fresh_email()
        _signup(self.client, email)
        self.client.logout()
        response = self.client.post(LOGIN_URL, {
            'login': email,
            'password': SIGNUP_PASSWORD,
        })
        assert response.status_code == 302
        assert response.url == reverse('account_email_verification_sent')
        assert '_auth_user_id' not in self.client.session

    def test_confirmation_flow_logs_in_and_welcomes(self, mailoutbox):
        email = _fresh_email()
        _signup(self.client, email)
        subjects = [m.subject for m in mailoutbox]
        assert any('Bienvenido' in s for s in subjects)
        confirm_mail = next(
            m for m in mailoutbox if 'Confirmá tu email' in m.subject
        )
        confirm_url = _extract_confirm_url(confirm_mail.body)
        response = self.client.post(confirm_url)
        assert response.status_code == 302
        assert '_auth_user_id' in self.client.session
        address = EmailAddress.objects.get(email=email)
        assert address.verified


# Limite bajo para que el test sea rápido y determinista: 2 intentos
# fallidos permitidos por email; el 3er intento (aunque la contraseña sea
# correcta) queda bloqueado.
RATE_LIMIT_OVERRIDE = {
    'login_failed': '10/m/ip,2/300s/key',
}


@pytest.mark.django_db
class TestLoginRateLimit:
    def setup_method(self):
        cache.clear()
        self.client = Client()
        self.email = _fresh_email()
        user = User.objects.create_user('ratelimit', self.email, SIGNUP_PASSWORD)
        EmailAddress.objects.create(
            user=user, email=self.email, verified=True, primary=True,
        )

    def _login(self, password=SIGNUP_PASSWORD):
        return self.client.post(LOGIN_URL, {
            'login': self.email,
            'password': password,
        })

    def _non_field_messages(self, response):
        return [str(e) for e in response.context['form'].non_field_errors()]

    def _is_throttled(self, response):
        return any(
            'intentos' in m.lower() or 'attempts' in m.lower()
            for m in self._non_field_messages(response)
        )

    @override_settings(ACCOUNT_RATE_LIMITS=RATE_LIMIT_OVERRIDE)
    def test_third_login_attempt_is_throttled(self):
        # Intentos 1 y 2: contraseña incorrecta -> error normal, sin bloqueo.
        for i in (1, 2):
            response = self._login(password=f'wrong-pass-{i}')
            assert response.status_code == 200
            assert not self._is_throttled(response)
        # Intento 3: bloqueado por rate limit, AUN con la contraseña correcta.
        response = self._login()
        assert response.status_code == 200
        assert self._is_throttled(response)
        assert '_auth_user_id' not in self.client.session

    @override_settings(ACCOUNT_RATE_LIMITS=RATE_LIMIT_OVERRIDE)
    def test_throttle_persists_until_timeout(self):
        for i in (1, 2):
            self._login(password=f'wrong-pass-{i}')
        # Sigue bloqueado en el 4to intento (dentro de la ventana de 300s).
        self._login()
        response = self._login()
        assert self._is_throttled(response)
        assert '_auth_user_id' not in self.client.session

    def test_db_cache_backend_works(self):
        # La tabla de cache compartida existe y set/get funcionan.
        cache.set('probe-key', 'probe-value', 60)
        assert cache.get('probe-key') == 'probe-value'
        cache.delete('probe-key')
        assert cache.get('probe-key') is None


# Un fallo de SMTP durante el signup (email de confirmación) NO debe romper
# el registro con 500: el adapter custom captura el error y el flujo sigue.
SMTP_DEAD_BACKEND = 'accounts.tests.SMTPDeadEmailBackend'


class SMTPDeadEmailBackend:
    """Backend de email que siempre falla al enviar (simula Brevo caído)."""

    def __init__(self, fail_silently=False, **kwargs):
        self.fail_silently = fail_silently

    def send_messages(self, email_messages):
        raise ConnectionError('SMTP caído (simulación de fallo en producción)')

    def close(self):
        pass


@pytest.mark.django_db
class TestSignupSurvivesSMTPFailure:
    def setup_method(self):
        self.client = Client()

    @override_settings(EMAIL_BACKEND=SMTP_DEAD_BACKEND)
    def test_signup_does_not_500_when_smtp_fails(self):
        response = self.client.post(SIGNUP_URL, {
            'email': _fresh_email(),
            'password1': SIGNUP_PASSWORD,
            'password2': SIGNUP_PASSWORD,
        })
        # Con verificación mandatory el signup termina redirigiendo a
        # 'account_email_verification_sent' aunque el envío haya fallado.
        assert response.status_code == 302
        assert response.url == reverse('account_email_verification_sent')

    @override_settings(EMAIL_BACKEND=SMTP_DEAD_BACKEND)
    def test_signup_creates_user_even_if_smtp_fails(self):
        email = _fresh_email()
        self.client.post(SIGNUP_URL, {
            'email': email,
            'password1': SIGNUP_PASSWORD,
            'password2': SIGNUP_PASSWORD,
        })
        assert User.objects.filter(email=email).exists()
        address = EmailAddress.objects.filter(email=email).first()
        assert address is not None
        assert not address.verified  # pendiente de confirmación

    @override_settings(EMAIL_BACKEND=SMTP_DEAD_BACKEND)
    def test_signup_with_existing_email_does_not_500(self):
        # Email ya registrado: allauth envía el mail "account_already_exists"
        # (anti-enumeración). Si el SMTP falla, NO debe romper con 500.
        existing = User.objects.create_user('dup', 'dup@test.com', SIGNUP_PASSWORD)
        EmailAddress.objects.create(
            user=existing, email='dup@test.com', verified=True, primary=True,
        )
        response = self.client.post(SIGNUP_URL, {
            'email': 'dup@test.com',
            'password1': SIGNUP_PASSWORD,
            'password2': SIGNUP_PASSWORD,
        })
        assert response.status_code == 302
        # No se crea una segunda cuenta.
        assert User.objects.filter(email='dup@test.com').count() == 1

