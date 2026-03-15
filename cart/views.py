from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from shop.models import Product
from .cart import Cart


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})


def cart_drawer(request):
    """Devuelve solo el contenido del drawer para HTMX."""
    cart = Cart(request)
    html = render_to_string('cart/_cart_items.html', {'cart': cart}, request=request)
    return HttpResponse(html)


def cart_count(request):
    cart = Cart(request)
    return HttpResponse(cart.get_total_items())


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, available=True)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product=product, quantity=quantity)

    response = HttpResponse(status=204)
    response['HX-Trigger'] = 'cartUpdated'
    return response


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    if quantity > 0:
        cart.add(product=product, quantity=quantity, override_quantity=True)
    else:
        cart.remove(product)

    response = HttpResponse(status=204)
    response['HX-Trigger'] = 'cartUpdated'
    return response


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)

    response = HttpResponse(status=204)
    response['HX-Trigger'] = 'cartUpdated'
    return response
