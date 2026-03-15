from django.http import HttpResponse
from django.template.loader import render_to_string
from cart.cart import Cart
from .services import get_shipping_options, get_zones


def shipping_calculator(request):
    cart = Cart(request)
    zone_code = request.GET.get('zone', '')
    options = get_shipping_options(cart.get_total_price(), zone_code if zone_code else None)
    zones = get_zones()

    html = render_to_string('shipping/_shipping_options.html', {
        'options': options,
        'zones': zones,
        'selected_zone': zone_code,
    }, request=request)
    return HttpResponse(html)
