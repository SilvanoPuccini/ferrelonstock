import factory
from shop.models import Category, Product


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f'Categoría {n}')
    slug = factory.Sequence(lambda n: f'categoria-{n}')
    description = 'Descripción de prueba'


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    category = factory.SubFactory(CategoryFactory)
    name = factory.Sequence(lambda n: f'Producto {n}')
    slug = factory.Sequence(lambda n: f'producto-{n}')
    description = 'Descripción del producto de prueba'
    price = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    stock = 10
    available = True
