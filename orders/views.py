from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import models, transaction
from .models import Order, OrderItem, OrderMessage
from .forms import CheckoutForm, OrderMessageForm
from .emails import send_order_confirmation, send_new_order_admin_notification
from cart.cart import Cart
from shop.models import Product
from shipping.models import ShippingMethod, ShippingZone
from shipping.services import get_zones, calculate_shipping_price


def _render_checkout(request, form, cart):
    return render(request, 'orders/checkout.html', {
        'form': form, 'cart': cart, 'zones': get_zones(),
    })


def _adjust_cart_to_stock_and_warn(request, cart, items):
    """Clamp cart quantities to the real stock and warn the user.

    Shared by the pre-check and the race-condition fallback so both paths
    converge to the same user experience: warning + corrected cart + form
    re-render. Never a 500, never a negative stock.
    """
    details = []
    for item in items:
        product = Product.objects.filter(pk=item['product'].pk).first()
        name = item['product'].name
        if product is None or product.stock <= 0:
            cart.remove(item['product'])
            available = 0
        else:
            cart.add(product=product, quantity=product.stock, override_quantity=True)
            available = product.stock
        details.append(f'"{name}" (disponibles: {available})')
    messages.warning(request, _(f'No hay stock suficiente de {", ".join(details)}.'))


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

            shipping_method_code = request.POST.get('shipping_method', 'pickup')
            shipping_zone_code = request.POST.get('shipping_zone', '')

            # El precio de envío se calcula SIEMPRE en el servidor;
            # nunca se confía en el shipping_price enviado por el cliente.
            method = ShippingMethod.objects.filter(code=shipping_method_code, is_active=True).first()
            zone = ShippingZone.objects.filter(code=shipping_zone_code, is_active=True).first() if shipping_zone_code else None

            order.shipping_method = method
            order.shipping_zone = zone
            order.shipping_price = calculate_shipping_price(method, zone, cart.get_total_price())

            # Pre-check: block checkout when the current stock can't cover the
            # cart. Cart.__iter__ re-fetches products fresh from the DB, so
            # item['product'].stock is the current committed value.
            insufficient_items = [
                item for item in cart
                if item['quantity'] > item['product'].stock
            ]
            if insufficient_items:
                _adjust_cart_to_stock_and_warn(request, cart, insufficient_items)
                return _render_checkout(request, form, cart)

            race_failed_items = []

            with transaction.atomic():
                order.save()

                for item in cart:
                    product = item['product']
                    # Atomic conditional decrement: the row is only updated when
                    # there is enough stock, closing the TOCTOU window between
                    # the pre-check above and this statement.
                    updated = Product.objects.filter(
                        pk=product.pk, stock__gte=item['quantity']
                    ).update(stock=models.F('stock') - item['quantity'])

                    if updated == 0:
                        # Stock ran out between the pre-check and this update.
                        # Roll back the whole transaction (order, items, profile)
                        # and let the user retry with a corrected cart.
                        race_failed_items.append(item)
                        transaction.set_rollback(True)
                        break

                    OrderItem.objects.create(
                        order=order, product=product,
                        price=item['price'], quantity=item['quantity']
                    )

                    # Refresh and check if stock went to zero
                    product.refresh_from_db()
                    if product.stock <= 0:
                        Product.objects.filter(pk=product.pk).update(
                            stock=0, available=False
                        )

                if not race_failed_items:
                    # Guardar datos en el perfil si están vacíos
                    profile = request.user.profile
                    if not profile.phone and order.phone:
                        profile.phone = order.phone
                    if not profile.address and order.address:
                        profile.address = order.address
                    if not profile.city and order.city:
                        profile.city = order.city
                    if not profile.region and order.region:
                        profile.region = order.region
                    if not profile.postal_code and order.postal_code:
                        profile.postal_code = order.postal_code
                    profile.save()

                    if not request.user.first_name and order.first_name:
                        request.user.first_name = order.first_name
                        request.user.last_name = order.last_name
                        request.user.save()

            if race_failed_items:
                _adjust_cart_to_stock_and_warn(request, cart, race_failed_items)
                return _render_checkout(request, form, cart)

            cart.clear()

            # Emails transaccionales: fallan silencioso (warning en logs),
            # nunca rompen el checkout.
            send_order_confirmation(order)
            send_new_order_admin_notification(order)

            messages.success(request, _(f'¡Pedido #{order.pk} creado con éxito!'))
            return redirect('payments:payment_select', order_id=order.pk)
    else:
        initial = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone': request.user.profile.phone,
            'address': request.user.profile.address,
            'city': request.user.profile.city,
            'region': request.user.profile.region,
            'postal_code': request.user.profile.postal_code,
        }
        form = CheckoutForm(initial=initial)

    return _render_checkout(request, form, cart)


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
    order_messages = order.messages.all()
    message_form = OrderMessageForm()
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'order_messages': order_messages,
        'message_form': message_form,
    })


@login_required
def order_send_message(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    if request.method == 'POST':
        form = OrderMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.order = order
            msg.sender = request.user
            msg.is_from_staff = False
            msg.save()
            messages.success(request, _('Mensaje enviado. Te responderemos pronto.'))

    return redirect('orders:order_detail', order_id=order.pk)
