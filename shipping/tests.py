import pytest
import json
from django.test import Client, override_settings
from django.contrib.auth.models import User
from orders.models import Order
from shipping.models import ShippingZone, ShippingMethod, ShippingConfig, Carrier, Shipment


@pytest.mark.django_db
class TestShippingModels:
    def test_create_zone(self):
        zone = ShippingZone.objects.create(name='CABA', code='caba', base_price=2500)
        assert str(zone) == 'CABA ($2,500)'

    def test_shipping_config_singleton(self):
        config1 = ShippingConfig.get_config()
        config2 = ShippingConfig.get_config()
        assert config1.pk == config2.pk

    def test_carrier_tracking_url(self):
        carrier = Carrier.objects.create(
            name='Andreani', code='andreani',
            tracking_url='https://andreani.com/{tracking_number}'
        )
        url = carrier.get_tracking_url('ABC123')
        assert 'ABC123' in url


@pytest.mark.django_db
class TestTrackingView:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user('tracker', 'track@test.com', 'pass123')
        self.order = Order.objects.create(
            user=self.user, first_name='Test', last_name='User',
            email='track@test.com', address='Calle', city='CABA'
        )

    def test_tracking_requires_login(self):
        response = self.client.get(f'/shipping/tracking/{self.order.pk}/')
        assert response.status_code == 302

    def test_tracking_no_shipment(self):
        self.client.login(username='tracker', password='pass123')
        response = self.client.get(f'/shipping/tracking/{self.order.pk}/')
        assert response.status_code == 200
        assert response.status_code == 200  # Página de tracking carga OK


@pytest.mark.django_db
class TestShippingWebhookFailSafe:
    """El webhook NUNCA autoriza si SHIPPING_WEBHOOK_SECRET está vacío."""

    def _post(self, client, secret_header):
        return client.post(
            '/shipping/webhook/update/',
            data=json.dumps({'tracking_number': 'X-1', 'status': 'in_transit'}).encode(),
            content_type='application/json',
            HTTP_X_WEBHOOK_SECRET=secret_header,
        )

    @override_settings(SHIPPING_WEBHOOK_SECRET='')
    def test_empty_secret_rejects_even_with_token(self):
        response = self._post(Client(), 'cualquier-token')
        assert response.status_code == 401

    @override_settings(SHIPPING_WEBHOOK_SECRET='')
    def test_empty_secret_rejects_without_token(self):
        response = self._post(Client(), '')
        assert response.status_code == 401

    def test_valid_secret_authorizes(self):
        user = User.objects.create_user('shipper', 'shipper@test.com', 'pass123')
        order = Order.objects.create(
            user=user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
        )
        carrier = Carrier.objects.create(name='Test Carrier', code='test-carrier')
        Shipment.objects.create(order=order, carrier=carrier, tracking_number='X-1')
        with override_settings(SHIPPING_WEBHOOK_SECRET='secret-valido'):
            response = self._post(Client(), 'secret-valido')
        assert response.status_code == 200
