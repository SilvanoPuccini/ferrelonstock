from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from decimal import Decimal, InvalidOperation
from .models import Order, OrderItem
from .forms import CheckoutForm
from cart.cart import Cart
from shipping.models import ShippingMethod, ShippingZone
from shipping.services import get_zones


@login_required
def checkout(request):
    cart = Cart(request)

    if cart.get_total_items() == 0:
        messages.warning(request, _('Tu carrito está vacío.'))
        return redirect('shop:product_list')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user

            # Envío - parseo seguro
            shipping_method_code = request.POST.get('shipping_method', 'pickup')
            shipping_zone_code = request.POST.get('shipping_zone', '')

            try:
                raw = request.POST.get('shipping_price', '0')
                raw = raw.strip().replace(',', '.')
                shipping_price = Decimal(raw) if raw else Decimal('0')
            except (InvalidOperation, ValueError):
                shipping_price = Decimal('0')

            method = ShippingMethod.objects.filter(code=shipping_method_code).first()
            zone = ShippingZone.objects.filter(code=shipping_zone_code).first() if shipping_zone_code else None

            order.shipping_method = method
            order.shipping_zone = zone
            order.shipping_price = shipping_price
            order.save()

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )
                product = item['product']
                product.stock -= item['quantity']
                if product.stock <= 0:
                    product.stock = 0
                    product.available = False
                product.save()

            cart.clear()
            messages.success(request, _(f'¡Pedido #{order.pk} creado con éxito!'))
            return redirect('payments:payment_select', order_id=order.pk)
    else:
        initial = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = CheckoutForm(initial=initial)

    return render(request, 'orders/checkout.html', {
        'form': form,
        'cart': cart,
        'zones': get_zones(),
    })


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/order_history.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})
