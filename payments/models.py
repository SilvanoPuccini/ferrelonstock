from django.db import models
from orders.models import Order


class Payment(models.Model):
    PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('mercadopago', 'Mercado Pago'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('refunded', 'Reembolsado'),
    ]

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name='Pedido'
    )
    provider = models.CharField(
        'Proveedor',
        max_length=20,
        choices=PROVIDER_CHOICES
    )
    transaction_id = models.CharField(
        'ID de transacción',
        max_length=250,
        blank=True
    )
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    amount = models.DecimalField('Monto', max_digits=10, decimal_places=2)
    created_at = models.DateTimeField('Fecha', auto_now_add=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-created_at']

    def __str__(self):
        return f'Pago {self.provider} - Pedido #{self.order.pk} - {self.get_status_display()}'
