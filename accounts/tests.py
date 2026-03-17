import pytest
from django.test import Client
from django.contrib.auth.models import User
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
