import pytest
from decimal import Decimal
from django.test import Client
from django.contrib.auth.models import User
from core.models import Contact, TeamMember
from shop.models import Category, Product
from orders.models import Order, OrderItem


@pytest.mark.django_db
class TestPages:
    def setup_method(self):
        self.client = Client()

    def test_home(self):
        response = self.client.get('/')
        assert response.status_code == 200

    def test_about(self):
        response = self.client.get('/about/')
        assert response.status_code == 200

    def test_contact(self):
        response = self.client.get('/contact/')
        assert response.status_code == 200

    def test_terms(self):
        response = self.client.get('/terms/')
        assert response.status_code == 200

    def test_privacy(self):
        response = self.client.get('/privacy/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestContactForm:
    def test_submit_contact(self):
        client = Client()
        response = client.post('/contact/', {
            'name': 'Juan',
            'email': 'juan@test.com',
            'subject': 'Consulta',
            'message': 'Hola, quiero saber más.'
        })
        assert response.status_code == 302
        assert Contact.objects.count() == 1

    def test_contact_invalid(self):
        client = Client()
        response = client.post('/contact/', {
            'name': '',
            'email': 'invalido',
            'subject': '',
            'message': ''
        })
        assert response.status_code == 200  # Vuelve al form con errores
        assert Contact.objects.count() == 0


@pytest.mark.django_db
class TestTeamMember:
    def test_create_member(self):
        member = TeamMember.objects.create(name='Carlos', role='Director', order=1)
        assert str(member) == 'Carlos'
        assert member.is_active is True


@pytest.mark.django_db
class TestSalesReport:
    def setup_method(self):
        self.client = Client()
        self.staff = User.objects.create_superuser('admin', 'admin@test.com', 'pass123')
        self.user = User.objects.create_user('regular', 'reg@test.com', 'pass123')
        self.cat = Category.objects.create(name='Test', slug='test-report')
        self.product_a = Product.objects.create(
            name='Taladro', slug='taladro-rep', category=self.cat,
            price=Decimal('10000'), stock=10, available=True,
        )
        self.product_b = Product.objects.create(
            name='Martillo', slug='martillo-rep', category=self.cat,
            price=Decimal('5000'), stock=10, available=True,
        )

    def _make_order(self, user, payment_status='paid', shipping_price=0, discount=0):
        order = Order.objects.create(
            user=user, first_name='Juan', last_name='Pérez',
            email='juan@test.com', address='Calle 123', city='CABA',
            payment_status=payment_status, shipping_price=Decimal(str(shipping_price)),
            discount=Decimal(str(discount)),
        )
        OrderItem.objects.create(order=order, product=self.product_a, price=self.product_a.price, quantity=2)
        OrderItem.objects.create(order=order, product=self.product_b, price=self.product_b.price, quantity=1)
        return order

    def test_anonymous_redirected(self):
        response = self.client.get('/reports/sales/')
        assert response.status_code == 302

    def test_non_staff_redirected(self):
        self.client.login(username='regular', password='pass123')
        response = self.client.get('/reports/sales/')
        assert response.status_code == 302

    def test_sales_report_shows_revenue_and_orders(self):
        self._make_order(self.user)
        self.client.login(username='admin', password='pass123')
        response = self.client.get('/reports/sales/')
        content = response.content.decode()
        assert response.status_code == 200
        assert '25.000' in content  # 10000*2 + 5000*1
        assert 'Taladro' in content
        assert 'Martillo' in content
        assert 'Pedidos pagados' in content

    def test_sales_report_ignores_unpaid_orders(self):
        self._make_order(self.user, payment_status='unpaid')
        self.client.login(username='admin', password='pass123')
        response = self.client.get('/reports/sales/')
        content = response.content.decode()
        assert '25.000' not in content

    def test_sales_report_includes_shipping_in_revenue(self):
        self._make_order(self.user, shipping_price=2500)
        self.client.login(username='admin', password='pass123')
        response = self.client.get('/reports/sales/')
        content = response.content.decode()
        assert '27.500' in content  # 25000 + 2500 envío

    def test_sales_report_subtracts_coupon_discount(self):
        self._make_order(self.user, shipping_price=2500, discount=5000)
        self.client.login(username='admin', password='pass123')
        response = self.client.get('/reports/sales/')
        content = response.content.decode()
        assert response.status_code == 200
        assert '22.500' in content  # 25000 + 2500 - 5000 descuento
        assert '27.500' not in content
        assert '25.000' not in content

    def test_sales_report_discount_never_makes_revenue_negative(self):
        self._make_order(self.user, discount=40000)
        self.client.login(username='admin', password='pass123')
        response = self.client.get('/reports/sales/')
        content = response.content.decode()
        assert response.status_code == 200
        assert '$0' in content  # 25000 - 40000 clamped a 0


@pytest.mark.django_db
class TestStockReport:
    def setup_method(self):
        self.client = Client()
        self.staff = User.objects.create_superuser('admin', 'admin@test.com', 'pass123')
        self.cat = Category.objects.create(name='Test', slug='test-stock-rep')
        self.low = Product.objects.create(
            name='Bajo', slug='bajo-rep', category=self.cat,
            price=Decimal('1000'), stock=2, available=True,
        )
        self.border = Product.objects.create(
            name='Limite', slug='limite-rep', category=self.cat,
            price=Decimal('2000'), stock=5, available=True,
        )
        self.ok = Product.objects.create(
            name='Sano', slug='sano-rep', category=self.cat,
            price=Decimal('3000'), stock=50, available=True,
        )

    def test_anonymous_redirected(self):
        response = self.client.get('/reports/stock/')
        assert response.status_code == 302

    def test_stock_report_default_threshold(self):
        self.client.login(username='admin', password='pass123')
        response = self.client.get('/reports/stock/')
        content = response.content.decode()
        assert response.status_code == 200
        assert 'Bajo' in content
        assert 'Limite' in content
        assert 'Sano' not in content

    def test_stock_report_custom_threshold(self):
        self.client.login(username='admin', password='pass123')
        response = self.client.get('/reports/stock/', {'threshold': '2'})
        content = response.content.decode()
        assert 'Bajo' in content
        assert 'Limite' not in content

    def test_stock_report_invalid_threshold_falls_back(self):
        self.client.login(username='admin', password='pass123')
        response = self.client.get('/reports/stock/', {'threshold': 'abc'})
        assert response.status_code == 200
        assert 'Bajo' in response.content.decode()
