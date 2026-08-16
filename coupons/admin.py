from django.contrib import admin
from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'discount_type', 'discount_value', 'active',
        'used_count', 'max_uses', 'valid_until',
    ]
    list_filter = ['active', 'discount_type']
    search_fields = ['code']