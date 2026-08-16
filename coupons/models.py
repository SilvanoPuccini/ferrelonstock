from decimal import Decimal

from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percent', 'Porcentaje'),
        ('fixed', 'Monto fijo'),
    ]

    code = models.CharField('Código', max_length=50, unique=True)
    discount_type = models.CharField(
        'Tipo de descuento', max_length=10, choices=DISCOUNT_TYPE_CHOICES
    )
    discount_value = models.DecimalField('Valor del descuento', max_digits=10, decimal_places=2)
    minimum_order = models.DecimalField(
        'Monto mínimo de compra', max_digits=10, decimal_places=2, default=0
    )
    valid_from = models.DateTimeField('Válido desde', null=True, blank=True)
    valid_until = models.DateTimeField('Válido hasta', null=True, blank=True)
    active = models.BooleanField('Activo', default=True)
    max_uses = models.PositiveIntegerField(
        'Usos máximos', default=0, help_text='0 = ilimitado'
    )
    used_count = models.PositiveIntegerField('Usos realizados', default=0)
    created_at = models.DateTimeField('Creado', auto_now_add=True)

    class Meta:
        verbose_name = 'Cupón'
        verbose_name_plural = 'Cupones'
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.upper().strip()
        super().save(*args, **kwargs)

    def is_valid_for(self, cart_total, at=None):
        """True when the coupon can currently be applied to a cart total."""
        if not self.active:
            return False
        now = at or timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        if Decimal(cart_total) < self.minimum_order:
            return False
        return True

    def calculate_discount(self, cart_total):
        """Discount in absolute money for a cart total (never negative)."""
        total = Decimal(cart_total)
        value = Decimal(str(self.discount_value))
        if value <= 0:
            return Decimal('0')
        if self.discount_type == 'percent':
            if value > 100:
                return Decimal('0')
            return (total * value / Decimal('100')).quantize(Decimal('0.01'))
        return min(value, total)