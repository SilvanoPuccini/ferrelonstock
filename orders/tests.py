import pytest
from decimal import Decimal
from django.test import Client
from django.contrib.auth.models import User
from shop.models import Category, Product
from orders.models import Order, OrderItem, OrderMessage


@pytest.mark.django_db
class TestOrderModel:
    def setup_method(self):
        self.user = User.objects.create_user('buyer', 'buyer@test.com', 'pass123')
        self.cat = Category.objects.create(name='Test', slug='test-order')
        self.product = Product.objects.create(
            name='Producto', slug='prod-order', category=self.cat,
            price=Decimal('10000'), stock=10, available=True
        )

    def test_create_order(self):
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA'
        )
        assert order.status == 'pending'
        assert order.payment_status == 'unpaid'

    def test_order_total(self):
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            shipping_price=Decimal('2500')
        )
        OrderItem.objects.create(order=order, product=self.product, price=Decimal('10000'), quantity=2)
        assert order.total == Decimal('22500')  # 20000 + 2500 envío
        assert order.total_items == 2

    def test_order_str(self):
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA'
        )
        assert f'#{order.pk}' in str(order)


@pytest.mark.django_db
class TestOrderMessage:
    def test_create_message(self):
        user = User.objects.create_user('msg', 'msg@test.com', 'pass123')
        order = Order.objects.create(
            user=user, first_name='Test', last_name='User',
            email='msg@test.com', address='Calle', city='CABA'
        )
        msg = OrderMessage.objects.create(
            order=order, sender=user, message_type='question',
            subject='Consulta', body='Hola, cuándo llega?'
        )
        assert msg.is_from_staff is False
        assert order.messages.count() == 1


@pytest.mark.django_db
class TestOrderViews:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user('orderview', 'ov@test.com', 'pass123')

    def test_checkout_requires_login(self):
        response = self.client.get('/orders/checkout/')
        assert response.status_code == 302

    def test_order_history_requires_login(self):
        response = self.client.get('/orders/history/')
        assert response.status_code == 302

    def test_order_history_logged_in(self):
        self.client.login(username='orderview', password='pass123')
        response = self.client.get('/orders/history/')
        assert response.status_code == 200

    def test_order_detail_requires_login(self):
        response = self.client.get('/orders/1/')
        assert response.status_code == 302

    def test_cannot_see_others_orders(self):
        other_user = User.objects.create_user('other', 'other@test.com', 'pass123')
        order = Order.objects.create(
            user=other_user, first_name='Other', last_name='User',
            email='other@test.com', address='Calle', city='CABA'
        )
        self.client.login(username='orderview', password='pass123')
        response = self.client.get(f'/orders/{order.pk}/')
        assert response.status_code == 404
