from decimal import Decimal
from django.conf import settings
from shop.models import Product
from coupons.models import Coupon


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.final_price)
            }
        else:
            # Actualizar precio por si cambió la oferta
            self.cart[product_id]['price'] = str(product.final_price)

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        if self.cart[product_id]['quantity'] > product.stock:
            self.cart[product_id]['quantity'] = product.stock

        self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        import copy
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        # Deep copy: NUNCA mutar los items anidados de la sesión. La copia
        # superficial dejaría 'price' como Decimal y el objeto Product dentro
        # del dict de la sesión, que luego NO se puede serializar a JSON
        # (TypeError: Object of type Decimal is not JSON serializable).
        cart = copy.deepcopy(self.cart)

        for product in products:
            pid = str(product.id)
            cart[pid]['product'] = product
            # Siempre usar precio actual (por si cambió la oferta)
            cart[pid]['price'] = str(product.final_price)

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        product_ids = self.cart.keys()
        products = {str(p.id): p for p in Product.objects.filter(id__in=product_ids)}
        total = Decimal('0')
        for pid, item in self.cart.items():
            if pid in products:
                total += products[pid].final_price * item['quantity']
            else:
                total += Decimal(item['price']) * item['quantity']
        return total

    def get_total_items(self):
        return sum(item['quantity'] for item in self.cart.values())

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        # El cupón vive en una key separada de sesión pero muere con el carrito.
        if settings.COUPON_SESSION_ID in self.session:
            del self.session[settings.COUPON_SESSION_ID]
        self.save()

    def set_coupon(self, coupon):
        """Stores an applied coupon in the session with its computed discount."""
        self.session[settings.COUPON_SESSION_ID] = {
            'coupon_id': coupon.id,
            'code': coupon.code,
            'discount': str(coupon.calculate_discount(self.get_total_price())),
        }
        self.save()

    def get_coupon(self):
        """Coupon info dict {'coupon', 'code', 'discount'} or None."""
        data = self.session.get(settings.COUPON_SESSION_ID)
        if not data:
            return None
        coupon = Coupon.objects.filter(pk=data.get('coupon_id')).first()
        if coupon is None:
            return None
        return {
            'coupon': coupon,
            'code': coupon.code,
            'discount': Decimal(data.get('discount', '0')),
        }

    def remove_coupon(self):
        if settings.COUPON_SESSION_ID in self.session:
            del self.session[settings.COUPON_SESSION_ID]
            self.save()

    def get_discount(self):
        """Fresh discount against the current cart total; 0 when not applicable."""
        data = self.get_coupon()
        if not data:
            return Decimal('0')
        if not data['coupon'].is_valid_for(self.get_total_price()):
            return Decimal('0')
        return data['coupon'].calculate_discount(self.get_total_price())

    def get_total_after_discount(self):
        total = self.get_total_price() - self.get_discount()
        return max(total, Decimal('0'))
