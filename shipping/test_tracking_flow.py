import json

import pytest
from django.contrib.auth.models import User
from django.test import Client, override_settings

from orders.models import Order
from payments.views import _mark_order_paid
from shipping.models import Carrier, Shipment, ShipmentEvent


@pytest.mark.django_db
class TestLogisticsFlow:
    """Flujo logístico integrado: pago → preparación → envío → seguimiento → entrega.

    Documenta el comportamiento ACTUAL del sistema end-to-end:
    - Pago confirmado → pedido 'preparing' + email de pago.
    - Webhook del carrier → shipment actualizado + ShipmentEvent + order.status sync.
    - Vista de tracking → timeline de eventos visible para el cliente.
    """

    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user('logistic', 'log@test.com', 'pass123')
        self.order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
        )
        self.carrier = Carrier.objects.create(
            name='Andreani', code='andreani',
            tracking_url='https://andreani.com/{tracking_number}',
        )

    def _create_shipment(self, tracking_number='AND-2026-001234'):
        return Shipment.objects.create(
            order=self.order, carrier=self.carrier, tracking_number=tracking_number,
        )

    def _webhook_post(self, tracking_number, status, **extra):
        data = {'tracking_number': tracking_number, 'status': status}
        data.update(extra)
        return self.client.post(
            '/shipping/webhook/update/',
            data=json.dumps(data).encode(),
            content_type='application/json',
            HTTP_X_WEBHOOK_SECRET='secret-valido',
        )

    def test_payment_confirmed_marks_order_preparing_and_emails(self, mailoutbox):
        _mark_order_paid(self.order, 'stripe', 'txn-123')

        self.order.refresh_from_db()
        assert self.order.status == 'preparing'
        assert self.order.payment_status == 'paid'

        to_buyer = [m for m in mailoutbox if 'juan@test.com' in m.to]
        # Un solo email al pagar: la confirmación de pago. El genérico
        # "cambió de estado" se suprime en _mark_order_paid
        # (send_status_email=False) porque send_payment_confirmation ya es el
        # aviso correcto y específico — antes llegaban DOS emails.
        assert len(to_buyer) == 1
        payment_emails = [m for m in to_buyer if '¡Pago recibido!' in m.subject]
        assert len(payment_emails) == 1
        assert f'¡Pago recibido! Pedido #{self.order.pk}' in payment_emails[0].subject

    @override_settings(SHIPPING_WEBHOOK_SECRET='secret-valido')
    def test_webhook_in_transit_syncs_order_and_creates_event(self, mailoutbox):
        _mark_order_paid(self.order, 'stripe', 'txn-123')
        shipment = self._create_shipment()

        response = self._webhook_post(
            'AND-2026-001234', 'in_transit',
            description='Paquete en tránsito hacia destino',
            location='Centro de distribución CABA',
        )
        assert response.status_code == 200

        shipment.refresh_from_db()
        self.order.refresh_from_db()
        assert shipment.status == 'in_transit'
        assert self.order.status == 'shipped'

        event = shipment.events.get()
        assert event.status == 'in_transit'
        assert event.description == 'Paquete en tránsito hacia destino'
        assert event.location == 'Centro de distribución CABA'

        # Respuesta legible para el carrier
        payload = response.json()
        assert payload['ok'] is True
        assert payload['order_status'] == 'Enviado'

    @override_settings(SHIPPING_WEBHOOK_SECRET='secret-valido')
    def test_webhook_delivered_stamps_delivery_and_updates_order(self):
        _mark_order_paid(self.order, 'stripe', 'txn-123')
        shipment = self._create_shipment()
        self._webhook_post('AND-2026-001234', 'in_transit')
        self._webhook_post(
            'AND-2026-001234', 'delivered',
            description='Entregado al destinatario',
            location='Domicilio del cliente',
        )

        shipment.refresh_from_db()
        self.order.refresh_from_db()
        assert shipment.status == 'delivered'
        assert shipment.delivered_at is not None
        assert self.order.status == 'delivered'
        assert shipment.events.count() == 2

    @override_settings(SHIPPING_WEBHOOK_SECRET='secret-valido')
    def test_tracking_view_shows_timeline_after_webhook_updates(self):
        _mark_order_paid(self.order, 'stripe', 'txn-123')
        shipment = self._create_shipment()
        self._webhook_post('AND-2026-001234', 'picked_up', description='Retirado por transportista')
        self._webhook_post('AND-2026-001234', 'in_transit', description='En camino a CABA')

        self.client.login(username='logistic', password='pass123')
        response = self.client.get(f'/shipping/tracking/{self.order.pk}/')
        assert response.status_code == 200

        content = response.content.decode()
        assert 'AND-2026-001234' in content
        assert 'Retirado por transportista' in content
        assert 'En camino a CABA' in content

    @override_settings(SHIPPING_WEBHOOK_SECRET='secret-valido')
    def test_webhook_status_change_sends_email_with_tracking(self, mailoutbox):
        """El webhook avisa al cliente por email con el tracking del envío.

        Order.save() dispara el email de estado; cuando el pedido ya tiene
        shipment, el email incluye el tracking number y un link a
        /shipping/tracking/{pk}/ para que el cliente siga el envío desde ahí.
        """
        _mark_order_paid(self.order, 'stripe', 'txn-123')
        shipment = self._create_shipment()

        mailoutbox.clear()
        self._webhook_post('AND-2026-001234', 'in_transit', description='En camino')

        shipment.refresh_from_db()
        self.order.refresh_from_db()
        assert shipment.events.count() == 1
        assert self.order.status == 'shipped'

        assert len(mailoutbox) == 1
        email = mailoutbox[0]
        assert 'cambió de estado' in email.subject
        assert 'Enviado' in email.body
        # El email de estado incluye el tracking number y el link al seguimiento.
        assert 'AND-2026-001234' in email.body
        assert f'/shipping/tracking/{self.order.pk}/' in email.body