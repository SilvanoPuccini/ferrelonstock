from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from cart.cart import Cart
from .models import Coupon


def _coupon_error(coupon, cart_total):
    """Spanish error message when a coupon cannot be applied, else None."""
    if coupon is None:
        return 'El código de cupón no existe.'
    now = timezone.now()
    if not coupon.active:
        return 'El cupón no está activo.'
    if coupon.valid_from and now < coupon.valid_from:
        return 'El cupón todavía no es válido.'
    if coupon.valid_until and now > coupon.valid_until:
        return 'El cupón ya venció.'
    if coupon.max_uses and coupon.used_count >= coupon.max_uses:
        return 'El cupón ya agotó sus usos.'
    if cart_total < coupon.minimum_order:
        return f'El cupón requiere una compra mínima de ${coupon.minimum_order:,.0f}.'
    return None


@require_POST
def coupon_apply(request):
    cart = Cart(request)
    code = request.POST.get('code', '').strip().upper()
    coupon = Coupon.objects.filter(code=code).first()
    cart_total = cart.get_total_price()

    error = _coupon_error(coupon, cart_total)
    if error:
        messages.error(request, error)
    else:
        cart.set_coupon(coupon)
        messages.success(request, f'¡Cupón {coupon.code} aplicado!')

    if request.headers.get('HX-Request'):
        html = render_to_string('cart/_cart_totals.html', {'cart': cart}, request=request)
        response = HttpResponse(html)
        response['HX-Trigger'] = 'cartUpdated'
        return response
    return redirect('cart:cart_detail')


@require_POST
def coupon_remove(request):
    cart = Cart(request)
    cart.remove_coupon()
    messages.info(request, 'Cupón quitado del carrito.')

    if request.headers.get('HX-Request'):
        html = render_to_string('cart/_cart_totals.html', {'cart': cart}, request=request)
        response = HttpResponse(html)
        response['HX-Trigger'] = 'cartUpdated'
        return response
    return redirect('cart:cart_detail')