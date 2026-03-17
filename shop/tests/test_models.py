import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from shop.models import Category, Brand, Product, Review


@pytest.mark.django_db
class TestCategory:
    def test_create_category(self):
        cat = Category.objects.create(name='Herramientas', slug='herramientas')
        assert cat.name == 'Herramientas'

    def test_str_representation(self):
        cat = Category.objects.create(name='Pinturas', slug='pinturas')
        assert str(cat) == 'Pinturas'

    def test_get_absolute_url(self):
        cat = Category.objects.create(name='Plomería', slug='plomeria')
        assert cat.get_absolute_url() == '/shop/category/plomeria/'


@pytest.mark.django_db
class TestProduct:
    def setup_method(self):
        self.category = Category.objects.create(name='Test', slug='test')
        self.brand = Brand.objects.create(name='Bosch', slug='bosch')

    def test_create_product(self):
        p = Product.objects.create(
            name='Taladro', slug='taladro', category=self.category,
            brand=self.brand, price=Decimal('15000'), stock=10
        )
        assert p.name == 'Taladro'
        assert p.price == Decimal('15000')

    def test_str_representation(self):
        p = Product.objects.create(
            name='Martillo', slug='martillo', category=self.category, price=Decimal('5000'), stock=5
        )
        assert str(p) == 'Martillo'

    def test_in_stock_true(self):
        p = Product.objects.create(
            name='Test', slug='test-stock', category=self.category,
            price=Decimal('100'), stock=5, available=True
        )
        assert p.in_stock is True

    def test_in_stock_false_no_stock(self):
        p = Product.objects.create(
            name='Test', slug='test-no-stock', category=self.category,
            price=Decimal('100'), stock=0, available=True
        )
        assert p.in_stock is False

    def test_in_stock_false_not_available(self):
        p = Product.objects.create(
            name='Test', slug='test-unavail', category=self.category,
            price=Decimal('100'), stock=10, available=False
        )
        assert p.in_stock is False

    def test_get_absolute_url(self):
        p = Product.objects.create(
            name='Test', slug='test-url', category=self.category, price=Decimal('100'), stock=1
        )
        assert p.get_absolute_url() == '/shop/product/test-url/'

    def test_has_discount(self):
        p = Product.objects.create(
            name='Test', slug='test-disc', category=self.category,
            price=Decimal('10000'), discount_price=Decimal('8000'), stock=1
        )
        assert p.has_discount is True
        assert p.discount_percent == 20
        assert p.final_price == Decimal('8000')

    def test_no_discount(self):
        p = Product.objects.create(
            name='Test', slug='test-nodisc', category=self.category,
            price=Decimal('10000'), stock=1
        )
        assert p.has_discount is False
        assert p.final_price == Decimal('10000')

    def test_avg_rating(self):
        p = Product.objects.create(
            name='Test', slug='test-rating', category=self.category, price=Decimal('100'), stock=1
        )
        user1 = User.objects.create_user('user1', 'u1@test.com', 'pass123')
        user2 = User.objects.create_user('user2', 'u2@test.com', 'pass123')
        Review.objects.create(product=p, user=user1, rating=5)
        Review.objects.create(product=p, user=user2, rating=3)
        assert p.avg_rating == 4.0
        assert p.review_count == 2


@pytest.mark.django_db
class TestBrand:
    def test_create_brand(self):
        b = Brand.objects.create(name='Stanley', slug='stanley')
        assert str(b) == 'Stanley'
        assert b.get_absolute_url() == '/shop/brand/stanley/'


@pytest.mark.django_db
class TestReview:
    def test_create_review(self):
        cat = Category.objects.create(name='Test', slug='test-rev')
        product = Product.objects.create(name='Test', slug='test-rev-p', category=cat, price=Decimal('100'), stock=1)
        user = User.objects.create_user('reviewer', 'r@test.com', 'pass123')
        review = Review.objects.create(product=product, user=user, rating=4, comment='Muy bueno')
        assert review.rating == 4
        assert 'Test (4/5)' in str(review)

    def test_unique_review_per_user(self):
        cat = Category.objects.create(name='Test', slug='test-uniq')
        product = Product.objects.create(name='Test', slug='test-uniq-p', category=cat, price=Decimal('100'), stock=1)
        user = User.objects.create_user('unique', 'uniq@test.com', 'pass123')
        Review.objects.create(product=product, user=user, rating=5)
        with pytest.raises(Exception):
            Review.objects.create(product=product, user=user, rating=3)
