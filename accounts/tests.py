import re
import uuid

import pytest
from django.test import Client
from django.contrib.auth.models import User
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

