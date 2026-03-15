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
        'Envío gratis desde ($)',
        max_digits=10, decimal_places=2,
        default=50000
    )
    pickup_address = models.CharField(
        'Dirección de retiro',
        max_length=250,
        default='Av. Corrientes 1234, CABA, Buenos Aires'
    )
    pickup_hours = models.CharField(
        'Horarios de retiro',
        max_length=250,
        default='Lunes a Viernes 8:00 - 18:00, Sábados 9:00 - 14:00'
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
