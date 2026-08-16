from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from shop.models import Product
from .models import WishlistItem


@login_required
def wishlist_detail(request):
    """Lists the current user's saved products.

    When the request is HTMX (e.g. after a `wishlistUpdated` event) it only
    returns the items grid so the page can refresh in place.
    """
    items = WishlistItem.objects.filter(user=request.user).select_related(
        'product__category', 'product__brand'
    )
    template_name = (
        'wishlist/_wishlist_items.html'
        if request.headers.get('HX-Request')
        else 'wishlist/wishlist_detail.html'
    )
    return render(request, template_name, {'items': items})


@require_POST
def wishlist_add(request, product_id):
    """Adds a product to the wishlist (idempotent via get_or_create)."""
    if not request.user.is_authenticated:
        if request.headers.get('HX-Request'):
            return HttpResponse('Iniciá sesión para guardar')
        return redirect_to_login(request.path)

    product = get_object_or_404(Product, id=product_id)
    WishlistItem.objects.get_or_create(user=request.user, product=product)

    response = HttpResponse(status=204)
    response['HX-Trigger'] = 'wishlistUpdated'
    return response


@require_POST
def wishlist_remove(request, product_id):
    """Removes a product from the wishlist."""
    if not request.user.is_authenticated:
        return redirect_to_login(request.path)

    WishlistItem.objects.filter(user=request.user, product_id=product_id).delete()

    response = HttpResponse(status=204)
    response['HX-Trigger'] = 'wishlistUpdated'
    return response


def wishlist_toggle_button(request, product_id):
    """Renders the heart toggle button with the current wishlist state.

    Used by the product detail page: the button wrapper listens for the
    `wishlistUpdated` event and re-renders itself from this endpoint.
    """
    if not request.user.is_authenticated:
        return HttpResponse('')
    product = get_object_or_404(Product, id=product_id)
    in_wishlist = WishlistItem.objects.filter(
        user=request.user, product=product
    ).exists()
    html = render_to_string(
        'wishlist/_toggle_wrapper.html',
        {'product': product, 'in_wishlist': in_wishlist},
        request=request,
    )
    return HttpResponse(html)