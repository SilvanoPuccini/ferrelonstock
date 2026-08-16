import pytest
from decimal import Decimal
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from shop.models import Category, Brand, Product, Review
from orders.models import Order, OrderItem


@pytest.mark.django_db
class TestProductListView:
    def setup_method(self):
        self.client = Client()
        self.cat = Category.objects.create(name='Herramientas', slug='herramientas')
        self.brand = Brand.objects.create(name='Bosch', slug='bosch')
        self.product = Product.objects.create(
            name='Taladro Bosch', slug='taladro-bosch', category=self.cat,
            brand=self.brand, price=Decimal('25000'), stock=10, available=True
        )

    def test_product_list_status(self):
        response = self.client.get('/shop/')
        assert response.status_code == 200

    def test_product_list_contains_product(self):
        response = self.client.get('/shop/')
        assert 'Taladro Bosch' in response.content.decode()

    def test_product_list_by_category(self):
        response = self.client.get('/shop/category/herramientas/')
        assert response.status_code == 200
        assert 'Taladro Bosch' in response.content.decode()

    def test_product_list_by_brand(self):
        response = self.client.get('/shop/brand/bosch/')
        assert response.status_code == 200
        assert 'Taladro Bosch' in response.content.decode()

    def test_search(self):
        response = self.client.get('/shop/?q=taladro')
        assert response.status_code == 200

    def test_unavailable_product_hidden(self):
        Product.objects.create(
            name='Oculto', slug='oculto', category=self.cat,
            price=Decimal('100'), stock=5, available=False
        )
        response = self.client.get('/shop/')
        assert 'Oculto' not in response.content.decode()

    def test_filter_by_min_price(self):
        Product.objects.create(
            name='Barato', slug='barato', category=self.cat,
            price=Decimal('10000'), stock=5, available=True
        )
        response = self.client.get(reverse('shop:product_list'), {'min_price': '20000'})
        content = response.content.decode()
        assert 'Taladro Bosch' in content
        assert 'Barato' not in content

    def test_filter_by_max_price(self):
        Product.objects.create(
            name='Caro', slug='caro', category=self.cat,
            price=Decimal('100000'), stock=5, available=True
        )
        response = self.client.get(reverse('shop:product_list'), {'max_price': '30000'})
        content = response.content.decode()
        assert 'Taladro Bosch' in content
        assert 'Caro' not in content

    def test_filter_by_price_bounds(self):
        Product.objects.create(
            name='Medio', slug='medio', category=self.cat,
            price=Decimal('20000'), stock=5, available=True
        )
        Product.objects.create(
            name='Caro', slug='caro', category=self.cat,
            price=Decimal('100000'), stock=5, available=True
        )
        response = self.client.get(
            reverse('shop:product_list'), {'min_price': '15000', 'max_price': '30000'}
        )
        content = response.content.decode()
        assert 'Taladro Bosch' in content
        assert 'Medio' in content
        assert 'Caro' not in content

    def test_filter_uses_effective_price(self):
        Product.objects.create(
            name='Oferta cara', slug='oferta-cara', category=self.cat,
            price=Decimal('100000'), discount_price=Decimal('20000'), stock=5, available=True
        )
        response = self.client.get(reverse('shop:product_list'), {'max_price': '22000'})
        content = response.content.decode()
        assert 'Oferta cara' in content
        assert 'Taladro Bosch' not in content

    def test_invalid_price_param_ignored(self):
        response = self.client.get(
            reverse('shop:product_list'), {'min_price': 'abc', 'max_price': ''}
        )
        content = response.content.decode()
        assert response.status_code == 200
        assert 'Taladro Bosch' in content

    def test_sort_by_price_asc(self):
        Product.objects.create(
            name='Barato', slug='barato', category=self.cat,
            price=Decimal('10000'), stock=5, available=True
        )
        response = self.client.get(reverse('shop:product_list'), {'sort': 'price_asc'})
        content = response.content.decode()
        assert content.index('Barato') < content.index('Taladro Bosch')

    def test_sort_by_price_desc(self):
        Product.objects.create(
            name='Barato', slug='barato', category=self.cat,
            price=Decimal('10000'), stock=5, available=True
        )
        response = self.client.get(reverse('shop:product_list'), {'sort': 'price_desc'})
        content = response.content.decode()
        assert content.index('Taladro Bosch') < content.index('Barato')

    def test_sort_by_name(self):
        Product.objects.create(
            name='Amoladora', slug='amoladora', category=self.cat,
            price=Decimal('10000'), stock=5, available=True
        )
        response = self.client.get(reverse('shop:product_list'), {'sort': 'name'})
        content = response.content.decode()
        assert content.index('Amoladora') < content.index('Taladro Bosch')

    def test_invalid_sort_ignored(self):
        response = self.client.get(reverse('shop:product_list'), {'sort': 'bogus'})
        content = response.content.decode()
        assert response.status_code == 200
        assert 'Taladro Bosch' in content

    def test_combined_category_and_price_filter(self):
        other = Category.objects.create(name='Electricidad', slug='electricidad')
        Product.objects.create(
            name='Cable', slug='cable', category=other,
            price=Decimal('10000'), stock=5, available=True
        )
        response = self.client.get(
            reverse('shop:product_list_by_category', args=[self.cat.slug]), {'min_price': '20000'}
        )
        content = response.content.decode()
        assert 'Taladro Bosch' in content
        assert 'Cable' not in content


@pytest.mark.django_db
class TestProductDetailView:
    def setup_method(self):
        self.client = Client()
        self.cat = Category.objects.create(name='Test', slug='test-detail')
        self.product = Product.objects.create(
            name='Martillo', slug='martillo-detail', category=self.cat,
            price=Decimal('8000'), stock=5, available=True, description='Un buen martillo'
        )

    def test_detail_status(self):
        response = self.client.get('/shop/product/martillo-detail/')
        assert response.status_code == 200

    def test_detail_contains_info(self):
        response = self.client.get('/shop/product/martillo-detail/')
        content = response.content.decode()
        assert 'Martillo' in content
        assert '8000' in content

    def test_detail_unavailable_404(self):
        Product.objects.create(
            name='No disp', slug='no-disp', category=self.cat,
            price=Decimal('100'), stock=0, available=False
        )
        response = self.client.get('/shop/product/no-disp/')
        assert response.status_code == 404

    def test_detail_unavailable_404_for_logged_in_non_buyer(self):
        non_buyer = User.objects.create_user('nobuy', 'nb@test.com', 'pass123')
        Product.objects.create(
            name='No comprado', slug='no-comprado-detail', category=self.cat,
            price=Decimal('100'), stock=0, available=False
        )
        self.client.login(username='nobuy', password='pass123')
        response = self.client.get('/shop/product/no-comprado-detail/')
        assert response.status_code == 404

    def test_detail_unavailable_visible_to_buyer(self):
        buyer = User.objects.create_user('buyer', 'buyer@test.com', 'pass123')
        sold_out = Product.objects.create(
            name='Agotado', slug='agotado-detail', category=self.cat,
            price=Decimal('100'), stock=0, available=False
        )
        order = Order.objects.create(
            user=buyer, first_name='Juan', last_name='Pérez',
            email='buyer@test.com', address='Calle 123', city='CABA',
            payment_status='paid',
        )
        OrderItem.objects.create(order=order, product=sold_out, price=sold_out.price, quantity=1)
        self.client.login(username='buyer', password='pass123')
        response = self.client.get('/shop/product/agotado-detail/')
        assert response.status_code == 200
        assert 'Agotado' in response.content.decode()


@pytest.mark.django_db
class TestOffersView:
    def setup_method(self):
        self.client = Client()
        self.cat = Category.objects.create(name='Test', slug='test-offers')

    def test_offers_empty(self):
        response = self.client.get('/shop/offers/')
        assert response.status_code == 200

    def test_offers_shows_discounted(self):
        Product.objects.create(
            name='En oferta', slug='en-oferta', category=self.cat,
            price=Decimal('10000'), discount_price=Decimal('8000'),
            stock=5, available=True
        )
        response = self.client.get('/shop/offers/')
        assert 'En oferta' in response.content.decode()


@pytest.mark.django_db
class TestReviewSubmit:
    def setup_method(self):
        self.client = Client()
        self.cat = Category.objects.create(name='Test', slug='test-rev-view')
        self.product = Product.objects.create(
            name='Producto', slug='producto-rev', category=self.cat,
            price=Decimal('5000'), stock=5, available=True
        )
        self.user = User.objects.create_user('tester', 'test@test.com', 'pass123')

    def _make_buyer(self, payment_status='paid'):
        order = Order.objects.create(
            user=self.user, first_name='Juan', last_name='Pérez',
            email='test@test.com', address='Calle 123', city='CABA',
            payment_status=payment_status,
        )
        OrderItem.objects.create(
            order=order, product=self.product,
            price=self.product.price, quantity=1,
        )
        return order

    def test_review_requires_login(self):
        response = self.client.post(f'/shop/product/producto-rev/review/', {'rating': 5, 'comment': 'Genial'})
        assert response.status_code == 302  # Redirect to login

    def test_review_submit(self):
        self._make_buyer()
        self.client.login(username='tester', password='pass123')
        response = self.client.post(f'/shop/product/producto-rev/review/', {'rating': 5, 'comment': 'Excelente'})
        assert response.status_code == 302
        assert self.product.reviews.count() == 1

    def test_review_duplicate_blocked(self):
        self._make_buyer()
        self.client.login(username='tester', password='pass123')
        self.client.post(f'/shop/product/producto-rev/review/', {'rating': 5, 'comment': 'Primera'})
        self.client.post(f'/shop/product/producto-rev/review/', {'rating': 3, 'comment': 'Segunda'})
        assert self.product.reviews.count() == 1  # Solo la primera

    def test_review_buyer_verified_purchase(self):
        self._make_buyer()
        self.client.login(username='tester', password='pass123')
        self.client.post(f'/shop/product/producto-rev/review/', {'rating': 4, 'comment': 'Bueno'})
        review = Review.objects.get(user=self.user, product=self.product)
        assert review.verified_purchase is True

    def test_review_submit_after_sold_out(self):
        self._make_buyer()
        self.product.available = False
        self.product.stock = 0
        self.product.save()
        self.client.login(username='tester', password='pass123')
        response = self.client.post(f'/shop/product/producto-rev/review/', {'rating': 5, 'comment': 'Llegó tarde pero bien'})
        assert response.status_code == 302
        review = Review.objects.get(user=self.user, product=self.product)
        assert review.verified_purchase is True

    def test_review_non_buyer_blocked(self):
        self.client.login(username='tester', password='pass123')
        response = self.client.post(
            f'/shop/product/producto-rev/review/', {'rating': 5, 'comment': 'Sin compra'}, follow=True
        )
        assert self.product.reviews.count() == 0
        assert any(
            'Solo los clientes que compraron este producto' in m.message
            for m in response.context['messages']
        )

    def test_review_unpaid_order_blocked(self):
        self._make_buyer(payment_status='unpaid')
        self.client.login(username='tester', password='pass123')
        self.client.post(f'/shop/product/producto-rev/review/', {'rating': 5, 'comment': 'No pagó'})
        assert self.product.reviews.count() == 0

    def test_review_detail_shows_purchase_gate(self):
        self.client.login(username='tester', password='pass123')
        response = self.client.get('/shop/product/producto-rev/')
        content = response.content.decode()
        assert 'Solo los clientes que compraron este producto' in content

    def test_review_detail_shows_form_for_buyer(self):
        self._make_buyer()
        self.client.login(username='tester', password='pass123')
        response = self.client.get('/shop/product/producto-rev/')
        content = response.content.decode()
        assert 'Dejá tu valoración' in content
