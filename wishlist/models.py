from django.conf import settings
from django.db import models
from shop.models import Product


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='wishlist_items', verbose_name='Usuario'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='wishlist_items', verbose_name='Producto'
    )
    created_at = models.DateTimeField('Fecha', auto_now_add=True)

    class Meta:
        verbose_name = 'Ítem de favoritos'
        verbose_name_plural = 'Ítems de favoritos'
        ordering = ['-created_at']
        unique_together = ['user', 'product']

    def __str__(self):
        return f'{self.user.email} - {self.product.name}'