from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField('Nombre', max_length=200)
    slug = models.SlugField('Slug', max_length=200, unique=True)
    description = models.TextField('Descripción', blank=True)
    image = models.ImageField('Imagen', upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_list_by_category', args=[self.slug])


class Brand(models.Model):
    name = models.CharField('Nombre', max_length=200)
    slug = models.SlugField('Slug', max_length=200, unique=True)
    logo = models.ImageField('Logo', upload_to='brands/', blank=True, null=True)

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_list_by_brand', args=[self.slug])


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE,
        related_name='products', verbose_name='Categoría'
    )
    brand = models.ForeignKey(
        Brand, on_delete=models.SET_NULL,
        related_name='products', verbose_name='Marca',
        null=True, blank=True
    )
    name = models.CharField('Nombre', max_length=200)
    slug = models.SlugField('Slug', max_length=200, unique=True)
    description = models.TextField('Descripción', blank=True)
    price = models.DecimalField('Precio', max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField('Stock', default=0)
    image = models.ImageField('Imagen', upload_to='products/', blank=True, null=True)
    available = models.BooleanField('Disponible', default=True)
    featured = models.BooleanField('Destacado', default=False)
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última actualización', auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.slug])

    @property
    def in_stock(self):
        return self.stock > 0 and self.available
