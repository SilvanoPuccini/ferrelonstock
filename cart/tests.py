import pytest
from decimal import Decimal
from django.test import Client, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import User
from shop.models import Category, Product
from cart.cart import Cart


def get_request_with_session():
    factory = RequestFactory()
    request = factory.get('/')
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.mark.django_db
class TestCart:
    def setup_method(self):
        self.cat = Category.objects.create(name='Test', slug='test-cart')
        self.product = Product.objects.create(
            name='Producto', slug='prod-cart', category=self.cat,
            price=Decimal('10000'), stock=5, available=True
        )
        self.product_offer = Product.objects.create(
            name='Oferta', slug='prod-offer', category=self.cat,
            price=Decimal('20000'), discount_price=Decimal('15000'),
            stock=3, available=True
        )

    def test_add_to_cart(self):
        request = get_request_with_session()
        cart = Cart(request)
        cart.add(self.product, quantity=2)
        assert cart.get_total_items() == 2

    def test_cart_total_price(self):
        request = get_request_with_session()
        cart = Cart(request)
        cart.add(self.product, quantity=2)
        assert cart.get_total_price() == Decimal('20000')

    def test_cart_uses_discount_price(self):
        request = get_request_with_session()
        cart = Cart(request)
        cart.add(self.product_offer, quantity=1)
        assert cart.get_total_price() == Decimal('15000')

    def test_remove_from_cart(self):
        request = get_request_with_session()
        cart = Cart(request)
        cart.add(self.product, quantity=1)
        cart.remove(self.product)
        assert cart.get_total_items() == 0

    def test_cart_respects_stock(self):
        request = get_request_with_session()
        cart = Cart(request)
        cart.add(self.product, quantity=99)
        assert cart.get_total_items() == 5  # Stock máximo

    def test_clear_cart(self):
        request = get_request_with_session()
        cart = Cart(request)
        cart.add(self.product, quantity=3)
        cart.clear()
        new_cart = Cart(request)
        assert new_cart.get_total_items() == 0


@pytest.mark.django_db
class TestCartViews:
    def setup_method(self):
        self.client = Client()
        self.cat = Category.objects.create(name='Test', slug='test-cartv')
        self.product = Product.objects.create(
            name='Producto', slug='prod-cartv', category=self.cat,
            price=Decimal('5000'), stock=10, available=True
        )

    def test_add_to_cart_view(self):
        response = self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 1})
        assert response.status_code in [200, 204, 302]

    def test_cart_detail_view(self):
        response = self.client.get('/cart/')
        assert response.status_code == 200
