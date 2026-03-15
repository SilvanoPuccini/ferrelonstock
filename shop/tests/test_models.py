import pytest
from decimal import Decimal
from shop.tests.factories import CategoryFactory, ProductFactory


@pytest.mark.django_db
class TestCategory:

    def test_create_category(self):
        category = CategoryFactory(name='Herramientas', slug='herramientas')
        assert category.name == 'Herramientas'
        assert category.slug == 'herramientas'

    def test_str_representation(self):
        category = CategoryFactory(name='Pinturas')
        assert str(category) == 'Pinturas'

    def test_get_absolute_url(self):
        category = CategoryFactory(slug='electricidad')
        assert category.get_absolute_url() == '/shop/category/electricidad/'


@pytest.mark.django_db
class TestProduct:

    def test_create_product(self):
        product = ProductFactory(name='Martillo', price=Decimal('5990.00'))
        assert product.name == 'Martillo'
        assert product.price == Decimal('5990.00')

    def test_str_representation(self):
        product = ProductFactory(name='Taladro Bosch')
        assert str(product) == 'Taladro Bosch'

    def test_in_stock_true(self):
        product = ProductFactory(stock=5, available=True)
        assert product.in_stock is True

    def test_in_stock_false_no_stock(self):
        product = ProductFactory(stock=0, available=True)
        assert product.in_stock is False

    def test_in_stock_false_not_available(self):
        product = ProductFactory(stock=10, available=False)
        assert product.in_stock is False

    def test_product_belongs_to_category(self):
        category = CategoryFactory(name='Corralón')
        product = ProductFactory(category=category)
        assert product.category.name == 'Corralón'

    def test_get_absolute_url(self):
        product = ProductFactory(slug='cemento-50kg')
        assert product.get_absolute_url() == '/shop/product/cemento-50kg/'

    def test_default_ordering(self):
        p1 = ProductFactory(name='Primero')
        p2 = ProductFactory(name='Segundo')
        from shop.models import Product
        products = list(Product.objects.all())
        assert products[0] == p2  # más reciente primero
