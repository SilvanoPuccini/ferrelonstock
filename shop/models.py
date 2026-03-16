from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField('Nombre', max_length=200)
    slug = models.SlugField('Slug', max_length=200, unique=True)
    image = models.ImageField('Imagen', upload_to='categories/', blank=True, null=True)
    description = models.TextField('Descripción', blank=True)
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
    discount_price = models.DecimalField('Precio de oferta', max_digits=10, decimal_places=2, null=True, blank=True, help_text='Dejá vacío si no tiene descuento')
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

    @property
    def has_discount(self):
        return self.discount_price is not None and self.discount_price < self.price

    @property
    def discount_percent(self):
        if self.has_discount:
            return int(100 - (self.discount_price * 100 / self.price))
        return 0

    @property
    def final_price(self):
        if self.has_discount:
            return self.discount_price
        return self.price


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='Producto')
    image = models.ImageField('Imagen', upload_to='products/gallery/')
    order = models.PositiveIntegerField('Orden', default=0)

    class Meta:
        verbose_name = 'Imagen del producto'
        verbose_name_plural = 'Imágenes del producto'
        ordering = ['order']

    def __str__(self):
        return f'Imagen {self.order} de {self.product.name}'
