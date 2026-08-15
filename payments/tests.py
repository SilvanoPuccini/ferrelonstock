import hashlib
import hmac
import json
import time
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
from django.test import Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse

from shop.models import Category, Product
from orders.models import Order, OrderItem
from payments.models import Payment


@pytest.mark.django_db
class TestPaymentModel:
    def setup_method(self):
        self.user = User.objects.create_user('payer', 'payer@test.com', 'pass123')

    def test_create_payment(self):
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            payment_status='unpaid',
        )
        payment = Payment.objects.create(
            order=order, provider='stripe', transaction_id='pi_test123',
            status='completed', amount=Decimal('10000'),
        )
        assert payment.provider == 'stripe'
        assert payment.status == 'completed'
        assert payment.amount == Decimal('10000')
        assert payment.transaction_id == 'pi_test123'

    def test_payment_str(self):
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
        )
        payment = Payment.objects.create(
            order=order, provider='mercadopago', status='pending',
            amount=Decimal('5000'),
        )
        assert 'mercadopago' in str(payment)
        assert 'Pendiente' in str(payment)

    def test_payment_one_to_one(self):
        """Each order can only have one payment record."""
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
        )
        Payment.objects.create(
            order=order, provider='stripe', status='completed',
            amount=Decimal('10000'),
        )
        # Second payment for same order should violate OneToOne
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Payment.objects.create(
                order=order, provider='mercadopago', status='completed',
                amount=Decimal('10000'),
            )


@pytest.mark.django_db
class TestPaymentSelectView:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user('payerview', 'pv@test.com', 'pass123')

    def test_requires_login(self):
        response = self.client.get('/payments/select/1/')
        assert response.status_code == 302

    def test_redirects_if_already_paid(self):
        self.client.login(username='payerview', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            payment_status='paid',
        )
        response = self.client.get(f'/payments/select/{order.pk}/')
        assert response.status_code == 302
        assert response.url == reverse('orders:order_detail', args=[order.pk])

    def test_shows_payment_page(self):
        self.client.login(username='payerview', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            payment_status='unpaid',
        )
        response = self.client.get(f'/payments/select/{order.pk}/')
        assert response.status_code == 200
        assert 'order' in response.context

    def test_payment_select_shows_only_stripe(self):
        """Mercado Pago ya no se ofrece como opción: la UI solo muestra Stripe."""
        self.client.login(username='payerview', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            payment_status='unpaid',
        )
        response = self.client.get(f'/payments/select/{order.pk}/')
        content = response.content.decode()
        assert 'Pagar con Stripe' in content
        # El link al checkout de Mercado Pago ya no existe; solo el de Stripe.
        assert '/payments/mp/' not in content
        assert '/payments/stripe/' in content

    def test_cannot_access_others_order(self):
        other = User.objects.create_user('other', 'other@test.com', 'pass123')
        order = Order.objects.create(
            user=other, first_name='Other', last_name='User',
            email='other@test.com', address='Calle', city='CABA',
        )
        self.client.login(username='payerview', password='pass123')
        response = self.client.get(f'/payments/select/{order.pk}/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestStripeCheckoutView:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user('stripeuser', 'su@test.com', 'pass123')

    def test_requires_login(self):
        response = self.client.get('/payments/stripe/1/')
        assert response.status_code == 302

    @patch('payments.views.stripe.checkout.Session')
    def test_creates_stripe_session(self, mock_session_class):
        mock_session = MagicMock()
        mock_session.url = 'https://checkout.stripe.com/test'
        mock_session_class.create.return_value = mock_session

        self.client.login(username='stripeuser', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            shipping_price=Decimal('0'),
        )
        cat = Category.objects.create(name='Test', slug='test-stripe')
        product = Product.objects.create(
            name='Producto', slug='prod-stripe', category=cat,
            price=Decimal('10000'), stock=10, available=True,
        )
        OrderItem.objects.create(order=order, product=product, price=Decimal('10000'), quantity=1)

        response = self.client.get(f'/payments/stripe/{order.pk}/')

        assert response.status_code == 302
        assert mock_session_class.create.called

    def test_cannot_access_others_order(self):
        other = User.objects.create_user('other', 'other@test.com', 'pass123')
        order = Order.objects.create(
            user=other, first_name='Other', last_name='User',
            email='other@test.com', address='Calle', city='CABA',
        )
        self.client.login(username='stripeuser', password='pass123')
        response = self.client.get(f'/payments/stripe/{order.pk}/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestStripeSuccessView:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user('stripesuccess', 'ss@test.com', 'pass123')

    def test_requires_login(self):
        response = self.client.get('/payments/stripe/success/1/')
        assert response.status_code == 302

    @patch('payments.views.stripe.checkout.Session.retrieve')
    def test_marks_order_as_paid(self, mock_retrieve):
        self.client.login(username='stripesuccess', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            shipping_price=Decimal('0'),
        )
        cat = Category.objects.create(name='Test', slug='test-ss')
        product = Product.objects.create(
            name='Producto', slug='prod-ss', category=cat,
            price=Decimal('10000'), stock=10, available=True,
        )
        OrderItem.objects.create(order=order, product=product, price=Decimal('10000'), quantity=1)

        mock_session = MagicMock()
        mock_session.payment_status = 'paid'
        mock_session.payment_intent = 'pi_test123'
        mock_session.metadata = {'order_id': str(order.pk)}
        mock_session.amount_total = int(order.total)
        mock_retrieve.return_value = mock_session

        response = self.client.get(
            f'/payments/stripe/success/{order.pk}/',
            {'session_id': 'cs_test_123'},
        )

        assert response.status_code == 302
        order.refresh_from_db()
        assert order.payment_status == 'paid'
        assert order.status == 'preparing'
        assert Payment.objects.filter(order=order, provider='stripe').exists()

    @patch('payments.views.stripe.checkout.Session.retrieve')
    def test_does_not_mark_paid_if_session_order_mismatch(self, mock_retrieve):
        """Una sesión de Stripe de OTRO pedido no debe marcar este como pagado."""
        self.client.login(username='stripesuccess', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            payment_status='unpaid',
        )
        cat = Category.objects.create(name='Test', slug='test-ss-mismatch')
        product = Product.objects.create(
            name='Producto', slug='prod-ss-mismatch', category=cat,
            price=Decimal('10000'), stock=10, available=True,
        )
        OrderItem.objects.create(order=order, product=product, price=Decimal('10000'), quantity=1)

        mock_session = MagicMock()
        mock_session.payment_status = 'paid'
        mock_session.metadata = {'order_id': '99999'}  # otro pedido
        mock_session.amount_total = int(order.total)
        mock_retrieve.return_value = mock_session

        response = self.client.get(
            f'/payments/stripe/success/{order.pk}/',
            {'session_id': 'cs_test_other'},
        )

        assert response.status_code == 302
        order.refresh_from_db()
        assert order.payment_status == 'unpaid'
        assert not Payment.objects.filter(order=order).exists()

    @patch('payments.views.stripe.checkout.Session.retrieve')
    def test_does_not_mark_paid_if_amount_mismatch(self, mock_retrieve):
        """Una sesión cuyo amount_total no coincide con el total del pedido no lo marca pagado."""
        self.client.login(username='stripesuccess', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            payment_status='unpaid',
        )
        cat = Category.objects.create(name='Test', slug='test-ss-amount')
        product = Product.objects.create(
            name='Producto', slug='prod-ss-amount', category=cat,
            price=Decimal('10000'), stock=10, available=True,
        )
        OrderItem.objects.create(order=order, product=product, price=Decimal('10000'), quantity=1)

        mock_session = MagicMock()
        mock_session.payment_status = 'paid'
        mock_session.metadata = {'order_id': str(order.pk)}
        mock_session.amount_total = int(order.total) + 500  # monto manipulado
        mock_retrieve.return_value = mock_session

        response = self.client.get(
            f'/payments/stripe/success/{order.pk}/',
            {'session_id': 'cs_test_123'},
        )

        assert response.status_code == 302
        order.refresh_from_db()
        assert order.payment_status == 'unpaid'
        assert not Payment.objects.filter(order=order).exists()

    @patch('payments.views.stripe.checkout.Session.retrieve')
    def test_does_not_mark_paid_if_not_paid(self, mock_retrieve):
        mock_session = MagicMock()
        mock_session.payment_status = 'unpaid'
        mock_retrieve.return_value = mock_session

        self.client.login(username='stripesuccess', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            payment_status='unpaid',
        )
        response = self.client.get(
            f'/payments/stripe/success/{order.pk}/',
            {'session_id': 'cs_test_123'},
        )

        order.refresh_from_db()
        assert order.payment_status == 'unpaid'
        assert not Payment.objects.filter(order=order).exists()

    def test_handles_missing_session_id(self):
        self.client.login(username='stripesuccess', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            payment_status='unpaid',
        )
        response = self.client.get(f'/payments/stripe/success/{order.pk}/')
        # Should redirect without error even without session_id
        assert response.status_code == 302

    def test_cannot_access_others_order(self):
        other = User.objects.create_user('other', 'other@test.com', 'pass123')
        order = Order.objects.create(
            user=other, first_name='Other', last_name='User',
            email='other@test.com', address='Calle', city='CABA',
        )
        self.client.login(username='stripesuccess', password='pass123')
        response = self.client.get(f'/payments/stripe/success/{order.pk}/?session_id=cs_test')
        assert response.status_code == 404


@pytest.mark.django_db
class TestMercadoPagoCheckoutView:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user('mpuser', 'mp@test.com', 'pass123')

    def test_requires_login(self):
        response = self.client.get('/payments/mp/1/')
        assert response.status_code == 302

    @patch('payments.views.mercadopago.SDK')
    def test_creates_mp_preference(self, mock_sdk):
        mock_sdk_instance = MagicMock()
        mock_sdk.return_value = mock_sdk_instance
        mock_sdk_instance.preference.return_value.create.return_value = {
            'response': {'sandbox_init_point': 'https://mp.com/checkout/123'}
        }

        self.client.login(username='mpuser', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            shipping_price=Decimal('0'),
        )

        response = self.client.get(f'/payments/mp/{order.pk}/')

        assert response.status_code == 302
        mock_sdk_instance.preference.return_value.create.assert_called_once()
        pref_data = mock_sdk_instance.preference.return_value.create.call_args[0][0]
        assert pref_data['external_reference'] == str(order.pk)
        assert pref_data['items'][0]['currency_id'] == 'ARS'

    def test_cannot_access_others_order(self):
        other = User.objects.create_user('other', 'other@test.com', 'pass123')
        order = Order.objects.create(
            user=other, first_name='Other', last_name='User',
            email='other@test.com', address='Calle', city='CABA',
        )
        self.client.login(username='mpuser', password='pass123')
        response = self.client.get(f'/payments/mp/{order.pk}/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestMercadoPagoSuccessView:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user('mpsuccess', 'mps@test.com', 'pass123')

    def test_requires_login(self):
        response = self.client.get('/payments/mp/success/1/')
        assert response.status_code == 302

    def test_forged_approved_does_not_mark_paid(self):
        """Un GET ?status=approved forjado NO marca pagado ni crea un Payment."""
        self.client.login(username='mpsuccess', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            payment_status='unpaid',
        )
        response = self.client.get(
            f'/payments/mp/success/{order.pk}/',
            {'status': 'approved', 'payment_id': 'mp_123'},
        )

        order.refresh_from_db()
        assert response.status_code == 302
        assert order.payment_status == 'unpaid'
        assert order.status == 'pending'
        assert not Payment.objects.filter(order=order).exists()

    def test_already_paid_stays_paid(self):
        """Si el webhook ya marcó el pedido como pagado, mp_success no lo rompe."""
        self.client.login(username='mpsuccess', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            payment_status='paid', status='preparing',
        )
        Payment.objects.create(
            order=order, provider='mercadopago', transaction_id='mp_real_1',
            status='completed', amount=Decimal('10000'),
        )
        response = self.client.get(
            f'/payments/mp/success/{order.pk}/',
            {'status': 'approved', 'payment_id': 'mp_123'},
        )

        order.refresh_from_db()
        assert response.status_code == 302
        assert order.payment_status == 'paid'
        assert order.status == 'preparing'
        payment = Payment.objects.get(order=order)
        assert payment.status == 'completed'
        assert payment.transaction_id == 'mp_real_1'

    def test_pending_get_does_not_create_payment(self):
        """Un GET ?status=pending forjado NO crea un Payment pending."""
        self.client.login(username='mpsuccess', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            payment_status='unpaid',
        )
        response = self.client.get(
            f'/payments/mp/success/{order.pk}/',
            {'status': 'pending', 'payment_id': 'mp_456'},
        )

        order.refresh_from_db()
        assert response.status_code == 302
        assert order.payment_status == 'unpaid'
        assert not Payment.objects.filter(order=order).exists()

    def test_other_status_does_not_mark_failed(self):
        """Un GET con status rechazado forjado NO marca el pedido como failed."""
        self.client.login(username='mpsuccess', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            payment_status='unpaid',
        )
        response = self.client.get(
            f'/payments/mp/success/{order.pk}/',
            {'status': 'rejected', 'payment_id': 'mp_789'},
        )

        order.refresh_from_db()
        assert response.status_code == 302
        assert order.payment_status == 'unpaid'
        assert not Payment.objects.filter(order=order).exists()

    def test_cannot_access_others_order(self):
        other = User.objects.create_user('other', 'other@test.com', 'pass123')
        order = Order.objects.create(
            user=other, first_name='Other', last_name='User',
            email='other@test.com', address='Calle', city='CABA',
        )
        self.client.login(username='mpsuccess', password='pass123')
        response = self.client.get(f'/payments/mp/success/{order.pk}/?status=approved')
        assert response.status_code == 404


@pytest.mark.django_db
class TestPaymentCancelView:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user('canceluser', 'cu@test.com', 'pass123')

    def test_requires_login(self):
        response = self.client.get('/payments/cancel/1/')
        assert response.status_code == 302

    def test_redirects_to_payment_select(self):
        self.client.login(username='canceluser', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
        )
        response = self.client.get(f'/payments/cancel/{order.pk}/')
        assert response.status_code == 302
        assert 'select' in response.url

    def test_does_not_change_order_status(self):
        self.client.login(username='canceluser', password='pass123')
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            payment_status='unpaid',
        )
        self.client.get(f'/payments/cancel/{order.pk}/')
        order.refresh_from_db()
        # Cancel view doesn't change payment_status, just shows message
        assert order.payment_status == 'unpaid'

    def test_cannot_access_others_order(self):
        other = User.objects.create_user('other', 'other@test.com', 'pass123')
        order = Order.objects.create(
            user=other, first_name='Other', last_name='User',
            email='other@test.com', address='Calle', city='CABA',
        )
        self.client.login(username='canceluser', password='pass123')
        response = self.client.get(f'/payments/cancel/{order.pk}/')
        assert response.status_code == 404


def _stripe_signature(payload, secret):
    """Genera el header Stripe-Signature para un payload dado (solo tests)."""
    ts = int(time.time())
    if isinstance(payload, bytes):
        payload = payload.decode('utf-8')
    signed_payload = f'{ts}.{payload}'.encode()
    signature = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f't={ts},v1={signature}'


@pytest.mark.django_db
class TestStripeWebhook:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user('webstripe', 'ws@test.com', 'pass123')

    @override_settings(STRIPE_WEBHOOK_SECRET='whsec_test')
    def test_invalid_signature_returns_400(self):
        payload = json.dumps({'type': 'checkout.session.completed'}).encode()
        response = self.client.post(
            '/payments/webhook/stripe/',
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=forged',
        )
        assert response.status_code == 400

    @override_settings(STRIPE_WEBHOOK_SECRET='whsec_test')
    def test_missing_secret_returns_400(self):
        response = self.client.post(
            '/payments/webhook/stripe/',
            data=json.dumps({'type': 'checkout.session.completed'}).encode(),
            content_type='application/json',
        )
        assert response.status_code == 400

    @override_settings(STRIPE_WEBHOOK_SECRET='whsec_test')
    def test_checkout_session_completed_marks_paid(self):
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            shipping_price=Decimal('0'),
        )
        cat = Category.objects.create(name='Test', slug='test-ws')
        product = Product.objects.create(
            name='Producto', slug='prod-ws', category=cat,
            price=Decimal('10000'), stock=10, available=True,
        )
        OrderItem.objects.create(order=order, product=product, price=Decimal('10000'), quantity=1)

        payload = json.dumps({
            'id': 'evt_completed',
            'object': 'event',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'object': 'checkout.session',
                    'payment_status': 'paid',
                    'payment_intent': 'pi_webhook_1',
                    'amount_total': int(order.total),
                    'metadata': {'order_id': str(order.pk)},
                }
            },
        }).encode()
        signature = _stripe_signature(payload, 'whsec_test')

        response = self.client.post(
            '/payments/webhook/stripe/',
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE=signature,
        )

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.payment_status == 'paid'
        assert order.status == 'preparing'
        payment = Payment.objects.get(order=order)
        assert payment.provider == 'stripe'
        assert payment.status == 'completed'
        assert payment.transaction_id == 'pi_webhook_1'

    @override_settings(STRIPE_WEBHOOK_SECRET='whsec_test')
    def test_checkout_completed_with_amount_mismatch_does_not_mark(self):
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
        )
        payload = json.dumps({
            'id': 'evt_completed_bad',
            'object': 'event',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_bad',
                    'object': 'checkout.session',
                    'payment_intent': 'pi_bad',
                    'amount_total': 1,  # monto forjado
                    'metadata': {'order_id': str(order.pk)},
                }
            },
        }).encode()
        signature = _stripe_signature(payload, 'whsec_test')

        response = self.client.post(
            '/payments/webhook/stripe/',
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE=signature,
        )

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.payment_status == 'unpaid'
        assert not Payment.objects.filter(order=order).exists()

    @override_settings(STRIPE_WEBHOOK_SECRET='whsec_test')
    def test_charge_refunded_marks_refunded(self):
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            payment_status='paid', status='preparing',
        )
        Payment.objects.create(
            order=order, provider='stripe', transaction_id='pi_refund',
            status='completed', amount=Decimal('10000'),
        )
        payload = json.dumps({
            'id': 'evt_refunded',
            'object': 'event',
            'type': 'charge.refunded',
            'data': {
                'object': {
                    'id': 'ch_refund',
                    'object': 'charge',
                    'payment_intent': 'pi_refund',
                    'metadata': {},
                }
            },
        }).encode()
        signature = _stripe_signature(payload, 'whsec_test')

        response = self.client.post(
            '/payments/webhook/stripe/',
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE=signature,
        )

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.payment_status == 'refunded'
        assert Payment.objects.get(order=order).status == 'refunded'


def _mp_signature(secret, data_id, request_id, ts=None):
    """Genera el header x-signature de MercadoPago v2 (solo tests)."""
    ts = ts or int(time.time())
    manifest = f'id:{data_id};request-id:{request_id};ts:{ts};'
    v1 = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return f'ts={ts},v1={v1}'


@pytest.mark.django_db
class TestMercadoPagoWebhook:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user('webmp', 'wm@test.com', 'pass123')

    @override_settings(MP_WEBHOOK_SECRET='mpsecret_test')
    def test_invalid_signature_returns_400(self):
        response = self.client.post(
            '/payments/webhook/mp/?type=payment&data.id=999',
            data={},
            HTTP_X_SIGNATURE='ts=123,v1=forged',
            HTTP_X_REQUEST_ID='req-forged',
        )
        assert response.status_code == 400

    @override_settings(MP_WEBHOOK_SECRET='mpsecret_test')
    def test_missing_signature_returns_400(self):
        response = self.client.post('/payments/webhook/mp/', data={})
        assert response.status_code == 400

    @override_settings(MP_WEBHOOK_SECRET='mpsecret_test')
    def test_missing_data_id_returns_400(self):
        signature = _mp_signature('mpsecret_test', '', 'req1')
        response = self.client.post(
            '/payments/webhook/mp/',
            data={},
            HTTP_X_SIGNATURE=signature,
            HTTP_X_REQUEST_ID='req1',
        )
        assert response.status_code == 400

    @patch('payments.views.mercadopago.SDK')
    @override_settings(MP_WEBHOOK_SECRET='mpsecret_test')
    def test_approved_marks_paid(self, mock_sdk):
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
        )
        mock_sdk_instance = MagicMock()
        mock_sdk.return_value = mock_sdk_instance
        mock_sdk_instance.payment.return_value.get.return_value = {
            'response': {
                'id': 12345,
                'status': 'approved',
                'external_reference': str(order.pk),
            }
        }

        data_id = '12345'
        signature = _mp_signature('mpsecret_test', data_id, 'req-approved')
        response = self.client.post(
            f'/payments/webhook/mp/?type=payment&data.id={data_id}',
            data={},
            HTTP_X_SIGNATURE=signature,
            HTTP_X_REQUEST_ID='req-approved',
        )

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.payment_status == 'paid'
        assert order.status == 'preparing'
        payment = Payment.objects.get(order=order)
        assert payment.provider == 'mercadopago'
        assert payment.status == 'completed'
        assert payment.transaction_id == data_id

    @patch('payments.views.mercadopago.SDK')
    @override_settings(MP_WEBHOOK_SECRET='mpsecret_test')
    def test_rejected_marks_failed(self, mock_sdk):
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
        )
        mock_sdk_instance = MagicMock()
        mock_sdk.return_value = mock_sdk_instance
        mock_sdk_instance.payment.return_value.get.return_value = {
            'response': {
                'id': 67890,
                'status': 'rejected',
                'external_reference': str(order.pk),
            }
        }

        data_id = '67890'
        signature = _mp_signature('mpsecret_test', data_id, 'req-rejected')
        response = self.client.post(
            f'/payments/webhook/mp/?type=payment&data.id={data_id}',
            data={},
            HTTP_X_SIGNATURE=signature,
            HTTP_X_REQUEST_ID='req-rejected',
        )

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.payment_status == 'failed'
        payment = Payment.objects.get(order=order)
        assert payment.status == 'failed'

    @patch('payments.views.mercadopago.SDK')
    @override_settings(MP_WEBHOOK_SECRET='mpsecret_test')
    def test_pending_marks_pending(self, mock_sdk):
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
        )
        mock_sdk_instance = MagicMock()
        mock_sdk.return_value = mock_sdk_instance
        mock_sdk_instance.payment.return_value.get.return_value = {
            'response': {
                'id': 11111,
                'status': 'pending',
                'external_reference': str(order.pk),
            }
        }

        data_id = '11111'
        signature = _mp_signature('mpsecret_test', data_id, 'req-pending')
        response = self.client.post(
            f'/payments/webhook/mp/?type=payment&data.id={data_id}',
            data={},
            HTTP_X_SIGNATURE=signature,
            HTTP_X_REQUEST_ID='req-pending',
        )

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.payment_status == 'unpaid'
        payment = Payment.objects.get(order=order)
        assert payment.status == 'pending'
