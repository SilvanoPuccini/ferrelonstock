from decimal import Decimal
from .models import ShippingZone, ShippingMethod, ShippingConfig


def get_shipping_options(cart_total, zone_code=None):
    config = ShippingConfig.get_config()
    options = []

    # Retiro en local (siempre gratis)
    pickup = ShippingMethod.objects.filter(code='pickup', is_active=True).first()
    if pickup:
        options.append({
            'method': pickup,
            'price': Decimal('0'),
            'estimated_days': '0',
            'label': f'{pickup.name} - GRATIS',
            'sublabel': f'{config.pickup_address} | {config.pickup_hours}',
            'is_free': True,
        })

    # Envío por zona
    if zone_code:
        zone = ShippingZone.objects.filter(code=zone_code, is_active=True).first()
    else:
        zone = ShippingZone.objects.filter(is_active=True).first()

    if zone:
        standard = ShippingMethod.objects.filter(code='standard', is_active=True).first()
        if standard:
            price = zone.base_price
            is_free = cart_total >= config.free_shipping_threshold

            options.append({
                'method': standard,
                'zone': zone,
                'price': Decimal('0') if is_free else price,
                'original_price': price,
                'estimated_days': f'{zone.estimated_days_min}-{zone.estimated_days_max}',
                'label': f'{standard.name} - {"GRATIS" if is_free else "$" + str(int(price))}',
                'sublabel': f'{zone.name} | {zone.estimated_days_min}-{zone.estimated_days_max} días hábiles' + (f' | Gratis en compras de ${int(config.free_shipping_threshold)}+' if not is_free else ''),
                'is_free': is_free,
            })

        express = ShippingMethod.objects.filter(code='express', is_active=True).first()
        if express:
            express_price = zone.base_price * Decimal('1.8')
            options.append({
                'method': express,
                'zone': zone,
                'price': express_price,
                'estimated_days': f'{max(1, zone.estimated_days_min - 1)}-{max(1, zone.estimated_days_max - 2)}',
                'label': f'{express.name} - ${int(express_price)}',
                'sublabel': f'{zone.name} | {max(1, zone.estimated_days_min - 1)}-{max(1, zone.estimated_days_max - 2)} días hábiles',
                'is_free': False,
            })

    return options


def get_zones():
    return ShippingZone.objects.filter(is_active=True)
