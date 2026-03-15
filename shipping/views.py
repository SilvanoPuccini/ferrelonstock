from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from cart.cart import Cart
from .services import get_shipping_options, get_zones
from .models import Shipment


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


@login_required
def tracking_view(request, order_id):
    shipment = get_object_or_404(
        Shipment,
        order__pk=order_id,
        order__user=request.user
    )
    events = shipment.events.all()
    return render(request, 'shipping/tracking.html', {
        'shipment': shipment,
        'events': events,
    })
