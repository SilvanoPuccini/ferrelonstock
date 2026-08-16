import pytest
from decimal import Decimal
from datetime import timedelta

from django.test import Client
from django.contrib.auth.models import User
from django.utils import timezone
from shop.models import Category, Product
from coupons.models import Coupon
from orders.models import Order


def _make_coupon(**overrides):
    defaults = dict(
        code='VERANO10',
        discount_type='percent',
        discount_value=Decimal('10'),
        minimum_order=Decimal('0'),
        active=True,
    )
    defaults.update(overrides)
    return Coupon.objects.create(**defaults)


@pytest.mark.django_db
class TestCouponCart:
    def setup_method(self):
        self.client = Client()
        self.cat = Category.objects.create(name='Test', slug='test-coupon')
        self.product = Product.objects.create(
            name='Producto', slug='prod-coupon', category=self.cat,
            price=Decimal('10000'), stock=10, available=True,
        )

    def test_apply_valid_coupon_stores_in_session(self):
        _make_coupon()
        self.client.post(f'/cart/add/{self.product.pk}/', {'quantity': 1})
        response = self.client.post('/coupons/apply/', {'code': 'verano10'})
        assert response.status_code == 302
        assert self.client.session['coupon']['code'] == 'VERANO10'

    def test_discount_percent_computed_correctly(self):
        _make_coupon()
        self.client.post(f'/cart/add/{self.product.pk}/', {'quantity': 1})
        self.client.post('/coupons/apply/', {'code': 'VERANO10'})
        # 10% of 10000 = 1000
        assert Decimal(self.client.session['coupon']['discount']) == Decimal('1000')

    def test_fixed_coupon_discount(self):
        _make_coupon(code='FIJO5', discount_type='fixed', discount_value=Decimal('500'))
        self.client.post(f'/cart/add/{self.product.pk}/', {'quantity': 2})
        self.client.post('/coupons/apply/', {'code': 'FIJO5'})
        assert Decimal(self.client.session['coupon']['discount']) == Decimal('500')

    def test_invalid_code_rejected(self):
        response = self.client.post('/coupons/apply/', {'code': 'NOEXISTE'})
        assert response.status_code == 302
        assert 'coupon' not in self.client.session

    def test_min_order_not_met_rejected(self):
        _make_coupon(minimum_order=Decimal('20000'))
        self.client.post(f'/cart/add/{self.product.pk}/', {'quantity': 1})
        response = self.client.post('/coupons/apply/', {'code': 'VERANO10'})
        assert response.status_code == 302
        assert 'coupon' not in self.client.session

    def test_expired_coupon_rejected(self):
        _make_coupon(valid_until=timezone.now() - timedelta(days=1))
        self.client.post(f'/cart/add/{self.product.pk}/', {'quantity': 1})
        response = self.client.post('/coupons/apply/', {'code': 'VERANO10'})
        assert response.status_code == 302
        assert 'coupon' not in self.client.session

    def test_inactive_coupon_rejected(self):
        _make_coupon(active=False)
        self.client.post(f'/cart/add/{self.product.pk}/', {'quantity': 1})
        response = self.client.post('/coupons/apply/', {'code': 'VERANO10'})
        assert 'coupon' not in self.client.session

    def test_remove_coupon(self):
        _make_coupon()
        self.client.post(f'/cart/add/{self.product.pk}/', {'quantity': 1})
        self.client.post('/coupons/apply/', {'code': 'VERANO10'})
        assert 'coupon' in self.client.session
        response = self.client.post('/coupons/remove/')
        assert response.status_code == 302
        assert 'coupon' not in self.client.session


@pytest.mark.django_db
class TestCouponCheckout:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user('couponbuyer', 'cb@test.com', 'pass123')
        self.cat = Category.objects.create(name='Test', slug='test-coupon-checkout')
        self.product = Product.objects.create(
            name='Producto', slug='prod-coupon-checkout', category=self.cat,
            price=Decimal('10000'), stock=10, available=True,
        )
        from shipping.models import ShippingZone, ShippingMethod
        ShippingZone.objects.create(name='CABA', code='caba', base_price=Decimal('2500'))
        ShippingMethod.objects.create(
            name='Envío estándar', code='standard', method_type='standard'
        )

    def _checkout_post(self):
        return self.client.post('/orders/checkout/', {
            'first_name': 'Juan', 'last_name': 'Pérez',
            'email': 'juan@test.com', 'address': 'Calle 123', 'city': 'CABA',
            'shipping_method': 'standard', 'shipping_zone': 'caba',
        })

    def test_order_created_with_coupon_persists_discount_and_increments_used_count(self):
        coupon = _make_coupon()
        self.client.login(username='couponbuyer', password='pass123')
        self.client.post(f'/cart/add/{self.product.pk}/', {'quantity': 2})
        self.client.post('/coupons/apply/', {'code': 'VERANO10'})

        response = self._checkout_post()

        assert response.status_code == 302
        order = Order.objects.get(user=self.user)
        assert order.coupon == coupon
        # 10% of 20000 = 2000
        assert order.discount == Decimal('2000')
        assert order.total == Decimal('20500')  # 20000 + 2500 envío - 2000 descuento
        coupon.refresh_from_db()
        assert coupon.used_count == 1

    def test_checkout_without_coupon_has_zero_discount(self):
        self.client.login(username='couponbuyer', password='pass123')
        self.client.post(f'/cart/add/{self.product.pk}/', {'quantity': 1})

        response = self._checkout_post()

        assert response.status_code == 302
        order = Order.objects.get(user=self.user)
        assert order.coupon is None
        assert order.discount == Decimal('0')

    def test_coupon_used_once_per_user_dropped_on_second_checkout(self):
        """El mismo cupón no se puede reusar: el segundo checkout lo descarta
        en silencio (descuento 0, sin adjuntar) a pesar de aplicarlo en el carrito."""
        coupon = _make_coupon()
        self.client.login(username='couponbuyer', password='pass123')

        # Primer pedido: el cupón se adjunta y descuenta.
        self.client.post(f'/cart/add/{self.product.pk}/', {'quantity': 1})
        self.client.post('/coupons/apply/', {'code': 'VERANO10'})
        response = self._checkout_post()
        assert response.status_code == 302
        first = Order.objects.filter(user=self.user).order_by('pk').first()
        assert first.coupon == coupon
        assert first.discount == Decimal('1000')

        # Segundo pedido con el mismo cupón: se descarta en el checkout.
        self.client.post(f'/cart/add/{self.product.pk}/', {'quantity': 1})
        self.client.post('/coupons/apply/', {'code': 'VERANO10'})
        response = self._checkout_post()
        assert response.status_code == 302

        orders = Order.objects.filter(user=self.user).order_by('pk')
        assert orders.count() == 2
        second = orders[1]
        assert second.coupon is None
        assert second.discount == Decimal('0')
        coupon.refresh_from_db()
        assert coupon.used_count == 1  # el uso se contó una sola vez