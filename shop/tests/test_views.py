import pytest
from decimal import Decimal
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from shop.models import Category, Brand, Product


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

    def test_review_requires_login(self):
        response = self.client.post(f'/shop/product/producto-rev/review/', {'rating': 5, 'comment': 'Genial'})
        assert response.status_code == 302  # Redirect to login

    def test_review_submit(self):
        self.client.login(username='tester', password='pass123')
        response = self.client.post(f'/shop/product/producto-rev/review/', {'rating': 5, 'comment': 'Excelente'})
        assert response.status_code == 302
        assert self.product.reviews.count() == 1

    def test_review_duplicate_blocked(self):
        self.client.login(username='tester', password='pass123')
        self.client.post(f'/shop/product/producto-rev/review/', {'rating': 5, 'comment': 'Primera'})
        self.client.post(f'/shop/product/producto-rev/review/', {'rating': 3, 'comment': 'Segunda'})
        assert self.product.reviews.count() == 1  # Solo la primera
