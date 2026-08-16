import pytest
from decimal import Decimal

from django.test import Client
from django.contrib.auth.models import User
from shop.models import Category, Product
from wishlist.models import WishlistItem


@pytest.mark.django_db
class TestWishlistViews:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user('wishlistuser', 'wl@test.com', 'pass123')
        self.cat = Category.objects.create(name='Test', slug='test-wishlist')
        self.product = Product.objects.create(
            name='Producto', slug='prod-wishlist', category=self.cat,
            price=Decimal('10000'), stock=10, available=True,
        )
        self.product2 = Product.objects.create(
            name='Otro', slug='prod-wishlist2', category=self.cat,
            price=Decimal('5000'), stock=10, available=True,
        )

    def test_add_requires_login(self):
        response = self.client.post(f'/wishlist/add/{self.product.pk}/')
        assert response.status_code == 302

    def test_add_works_and_is_idempotent(self):
        self.client.login(username='wishlistuser', password='pass123')
        response = self.client.post(f'/wishlist/add/{self.product.pk}/')
        assert response.status_code == 204
        response = self.client.post(f'/wishlist/add/{self.product.pk}/')
        assert response.status_code == 204
        assert WishlistItem.objects.filter(user=self.user, product=self.product).count() == 1

    def test_remove_works(self):
        self.client.login(username='wishlistuser', password='pass123')
        WishlistItem.objects.create(user=self.user, product=self.product)
        response = self.client.post(f'/wishlist/remove/{self.product.pk}/')
        assert response.status_code == 204
        assert not WishlistItem.objects.filter(user=self.user).exists()

    def test_remove_requires_login(self):
        response = self.client.post(f'/wishlist/remove/{self.product.pk}/')
        assert response.status_code == 302

    def test_detail_requires_login(self):
        response = self.client.get('/wishlist/')
        assert response.status_code == 302

    def test_detail_lists_only_own_items(self):
        self.client.login(username='wishlistuser', password='pass123')
        other = User.objects.create_user('other', 'other@test.com', 'pass123')
        WishlistItem.objects.create(user=self.user, product=self.product)
        WishlistItem.objects.create(user=other, product=self.product2)
        response = self.client.get('/wishlist/')
        assert response.status_code == 200
        assert response.context['items'].count() == 1
        assert response.context['items'][0].product == self.product

    def test_unauthenticated_htmx_add_returns_login_prompt(self):
        response = self.client.post(
            f'/wishlist/add/{self.product.pk}/',
            HTTP_HX_REQUEST='true',
        )
        assert response.status_code == 200
        assert 'Iniciá sesión' in response.content.decode()