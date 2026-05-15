from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
from django.test import Client
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
        mock_session = MagicMock()
        mock_session.payment_status = 'paid'
        mock_session.payment_intent = 'pi_test123'
        mock_retrieve.return_value = mock_session

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

    def test_marks_paid_on_approved(self):
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
        assert order.payment_status == 'paid'
        assert order.status == 'preparing'
        payment = Payment.objects.get(order=order)
        assert payment.provider == 'mercadopago'
        assert payment.status == 'completed'
        assert payment.transaction_id == 'mp_123'

    def test_marks_pending_on_pending(self):
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
        assert order.payment_status == 'unpaid'  # stays unpaid, not failed
        payment = Payment.objects.get(order=order)
        assert payment.status == 'pending'

    def test_marks_failed_on_other_status(self):
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
        assert order.payment_status == 'failed'

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
