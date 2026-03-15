from django.db import models
from django.contrib.auth.models import User
from shop.models import Product


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Usuario'
    )
    first_name = models.CharField('Nombre', max_length=100)
    last_name = models.CharField('Apellido', max_length=100)
    email = models.EmailField('Email')
    phone = models.CharField('Teléfono', max_length=20, blank=True)
    address = models.CharField('Dirección', max_length=250)
    city = models.CharField('Ciudad', max_length=100)
    region = models.CharField('Región', max_length=100, blank=True)
    postal_code = models.CharField('Código postal', max_length=20, blank=True)
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    notes = models.TextField('Notas del cliente', blank=True)
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última actualización', auto_now=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']

    def __str__(self):
        return f'Pedido #{self.pk} - {self.user.email}'

    @property
    def total(self):
        return sum(item.get_total for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def status_color(self):
        colors = {
            'pending': 'yellow',
            'paid': 'blue',
            'shipped': 'purple',
            'delivered': 'green',
            'cancelled': 'red',
        }
        return colors.get(self.status, 'gray')


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Pedido'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='Producto'
    )
    price = models.DecimalField('Precio', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Cantidad', default=1)

    class Meta:
        verbose_name = 'Ítem del pedido'
        verbose_name_plural = 'Ítems del pedido'

    def __str__(self):
        return f'{self.quantity}x {self.product.name}'

    @property
    def get_total(self):
        return self.price * self.quantity
