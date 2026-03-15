from django.db import models
from decimal import Decimal


class ShippingZone(models.Model):
    name = models.CharField('Nombre', max_length=100)
    code = models.CharField('Código', max_length=20, unique=True)
    base_price = models.DecimalField('Precio base', max_digits=10, decimal_places=2)
    price_per_kg = models.DecimalField('Precio por kg', max_digits=10, decimal_places=2, default=0)
    estimated_days_min = models.PositiveIntegerField('Días mín.', default=1)
    estimated_days_max = models.PositiveIntegerField('Días máx.', default=3)
    is_active = models.BooleanField('Activa', default=True)

    class Meta:
        verbose_name = 'Zona de envío'
        verbose_name_plural = 'Zonas de envío'
        ordering = ['base_price']

    def __str__(self):
        return f'{self.name} (${self.base_price:,.0f})'


class ShippingMethod(models.Model):
    METHOD_CHOICES = [
        ('pickup', 'Retiro en local'),
        ('standard', 'Envío estándar'),
        ('express', 'Envío express'),
        ('andreani', 'Andreani'),
        ('oca', 'OCA'),
    ]

    name = models.CharField('Nombre', max_length=100)
    code = models.CharField('Código', max_length=20, unique=True)
    method_type = models.CharField('Tipo', max_length=20, choices=METHOD_CHOICES)
    description = models.CharField('Descripción', max_length=250, blank=True)
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Método de envío'
        verbose_name_plural = 'Métodos de envío'

    def __str__(self):
        return self.name


class ShippingConfig(models.Model):
    free_shipping_threshold = models.DecimalField(
        'Envío gratis desde ($)', max_digits=10, decimal_places=2, default=50000
    )
    pickup_address = models.CharField(
        'Dirección de retiro', max_length=250, default='Av. Corrientes 1234, CABA, Buenos Aires'
    )
    pickup_hours = models.CharField(
        'Horarios de retiro', max_length=250, default='Lunes a Viernes 8:00 - 18:00, Sábados 9:00 - 14:00'
    )

    class Meta:
        verbose_name = 'Configuración de envío'
        verbose_name_plural = 'Configuración de envío'

    def __str__(self):
        return f'Envío gratis desde ${self.free_shipping_threshold:,.0f}'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config


class Carrier(models.Model):
    name = models.CharField('Nombre', max_length=100)
    code = models.CharField('Código', max_length=20, unique=True)
    tracking_url = models.CharField(
        'URL de seguimiento',
        max_length=500,
        blank=True,
        help_text='Usá {tracking_number} como placeholder. Ej: https://www.andreani.com/#!/informacionEnvio/{tracking_number}'
    )
    phone = models.CharField('Teléfono', max_length=50, blank=True)
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Transportista'
        verbose_name_plural = 'Transportistas'

    def __str__(self):
        return self.name

    def get_tracking_url(self, tracking_number):
        if self.tracking_url and tracking_number:
            return self.tracking_url.replace('{tracking_number}', tracking_number)
        return ''


class Shipment(models.Model):
    STATUS_CHOICES = [
        ('preparing', 'Preparando envío'),
        ('picked_up', 'Retirado por transportista'),
        ('in_transit', 'En camino'),
        ('out_for_delivery', 'En reparto'),
        ('delivered', 'Entregado'),
        ('failed', 'Entrega fallida'),
        ('returned', 'Devuelto'),
    ]

    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='shipment',
        verbose_name='Pedido'
    )
    carrier = models.ForeignKey(
        Carrier,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Transportista'
    )
    tracking_number = models.CharField('Número de seguimiento', max_length=100, blank=True)
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='preparing')
    estimated_delivery = models.DateField('Entrega estimada', null=True, blank=True)
    delivered_at = models.DateTimeField('Fecha de entrega', null=True, blank=True)
    notes = models.TextField('Notas internas', blank=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Envío'
        verbose_name_plural = 'Envíos'

    def __str__(self):
        return f'Envío #{self.pk} - Pedido #{self.order.pk}'

    @property
    def tracking_url(self):
        if self.carrier and self.tracking_number:
            return self.carrier.get_tracking_url(self.tracking_number)
        return ''

    @property
    def status_icon(self):
        icons = {
            'preparing': '📦',
            'picked_up': '🚛',
            'in_transit': '🚚',
            'out_for_delivery': '🏍️',
            'delivered': '✅',
            'failed': '❌',
            'returned': '↩️',
        }
        return icons.get(self.status, '📦')

    @property
    def progress_percent(self):
        steps = {
            'preparing': 20,
            'picked_up': 40,
            'in_transit': 60,
            'out_for_delivery': 80,
            'delivered': 100,
            'failed': 80,
            'returned': 0,
        }
        return steps.get(self.status, 0)


class ShipmentEvent(models.Model):
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='Envío'
    )
    status = models.CharField('Estado', max_length=20, choices=Shipment.STATUS_CHOICES)
    description = models.CharField('Descripción', max_length=500)
    location = models.CharField('Ubicación', max_length=200, blank=True)
    created_at = models.DateTimeField('Fecha', auto_now_add=True)

    class Meta:
        verbose_name = 'Evento del envío'
        verbose_name_plural = 'Eventos del envío'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_status_display()} - {self.description}'
