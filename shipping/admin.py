from django.contrib import admin
from .models import ShippingZone, ShippingMethod, ShippingConfig, Carrier, Shipment, ShipmentEvent


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


@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'phone', 'is_active']
    list_editable = ['is_active']


class ShipmentEventInline(admin.TabularInline):
    model = ShipmentEvent
    extra = 1
    readonly_fields = ['created_at']


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'carrier', 'tracking_number', 'status', 'estimated_delivery', 'updated_at']
    list_filter = ['status', 'carrier', 'created_at']
    list_editable = ['status']
    search_fields = ['tracking_number', 'order__id']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ShipmentEventInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if 'status' in form.changed_data:
            ShipmentEvent.objects.create(
                shipment=obj,
                status=obj.status,
                description=f'Estado actualizado a: {obj.get_status_display()}'
            )
            if obj.status == 'delivered':
                obj.order.status = 'delivered'
                obj.order.save()
            elif obj.status in ['in_transit', 'out_for_delivery', 'picked_up']:
                obj.order.status = 'shipped'
                obj.order.save()
