from decimal import Decimal
from .cart import Cart
from shipping.models import ShippingConfig


def cart(request):
    c = Cart(request)
    config = ShippingConfig.get_config()
    total = c.get_total_price()
    threshold = config.free_shipping_threshold
    remaining = threshold - total

    return {
        'cart': c,
        'free_shipping_threshold': threshold,
        'free_shipping_remaining': max(remaining, Decimal('0')),
        'free_shipping_qualified': total >= threshold,
    }
