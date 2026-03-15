from django.db import models
from django.contrib.auth.models import User
from shop.models import Product


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente de pago'),
        ('paid', 'Pagado'),
        ('preparing', 'En preparación'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'No pagado'),
        ('paid', 'Pagado'),
        ('refunded', 'Reembolsado'),
        ('failed', 'Fallido'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='Usuario')
    first_name = models.CharField('Nombre', max_length=100)
    last_name = models.CharField('Apellido', max_length=100)
    email = models.EmailField('Email')
    phone = models.CharField('Teléfono', max_length=20, blank=True)
    address = models.CharField('Dirección', max_length=250)
    city = models.CharField('Ciudad', max_length=100)
    region = models.CharField('Región', max_length=100, blank=True)
    postal_code = models.CharField('Código postal', max_length=20, blank=True)
    status = models.CharField('Estado del pedido', max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField('Estado de pago', max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    notes = models.TextField('Notas del cliente', blank=True)
    shipping_method = models.ForeignKey(
        'shipping.ShippingMethod', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Método de envío'
    )
    shipping_zone = models.ForeignKey(
        'shipping.ShippingZone', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Zona de envío'
    )
    shipping_price = models.DecimalField('Costo de envío', max_digits=10, decimal_places=2, default=0)
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
        items_total = sum(item.get_total for item in self.items.all())
        return items_total + self.shipping_price

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Pedido')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items', verbose_name='Producto')
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


class OrderMessage(models.Model):
    TYPE_CHOICES = [
        ('question', 'Consulta'),
        ('complaint', 'Reclamo'),
        ('suggestion', 'Sugerencia'),
        ('other', 'Otro'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='messages', verbose_name='Pedido')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Remitente')
    message_type = models.CharField('Tipo', max_length=20, choices=TYPE_CHOICES, default='question')
    subject = models.CharField('Asunto', max_length=200)
    body = models.TextField('Mensaje')
    is_from_staff = models.BooleanField('Respuesta del vendedor', default=False)
    is_read = models.BooleanField('Leído', default=False)
    created_at = models.DateTimeField('Fecha', auto_now_add=True)

    class Meta:
        verbose_name = 'Mensaje del pedido'
        verbose_name_plural = 'Mensajes del pedido'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.get_message_type_display()} - Pedido #{self.order.pk}'
