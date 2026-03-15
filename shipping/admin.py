from django.contrib import admin
from .models import ShippingZone, ShippingMethod, ShippingConfig


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'base_price', 'estimated_days_min', 'estimated_days_max', 'is_active']
    list_editable = ['base_price', 'is_active']


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'method_type', 'is_active']
    list_editable = ['is_active']


@admin.register(ShippingConfig)
class ShippingConfigAdmin(admin.ModelAdmin):
    list_display = ['free_shipping_threshold', 'pickup_address']

    def has_add_permission(self, request):
        return not ShippingConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
