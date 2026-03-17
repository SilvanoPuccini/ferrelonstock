import pytest
from django.test import Client
from core.models import Contact, TeamMember


@pytest.mark.django_db
class TestPages:
    def setup_method(self):
        self.client = Client()

    def test_home(self):
        response = self.client.get('/')
        assert response.status_code == 200

    def test_about(self):
        response = self.client.get('/about/')
        assert response.status_code == 200

    def test_contact(self):
        response = self.client.get('/contact/')
        assert response.status_code == 200

    def test_terms(self):
        response = self.client.get('/terms/')
        assert response.status_code == 200

    def test_privacy(self):
        response = self.client.get('/privacy/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestContactForm:
    def test_submit_contact(self):
        client = Client()
        response = client.post('/contact/', {
            'name': 'Juan',
            'email': 'juan@test.com',
            'subject': 'Consulta',
            'message': 'Hola, quiero saber más.'
        })
        assert response.status_code == 302
        assert Contact.objects.count() == 1

    def test_contact_invalid(self):
        client = Client()
        response = client.post('/contact/', {
            'name': '',
            'email': 'invalido',
            'subject': '',
            'message': ''
        })
        assert response.status_code == 200  # Vuelve al form con errores
        assert Contact.objects.count() == 0


@pytest.mark.django_db
class TestTeamMember:
    def test_create_member(self):
        member = TeamMember.objects.create(name='Carlos', role='Director', order=1)
        assert str(member) == 'Carlos'
        assert member.is_active is True
