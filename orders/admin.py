from django.contrib import admin
from .models import Order, OrderItem, OrderMessage
from shipping.models import Shipment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0


class ShipmentInline(admin.StackedInline):
    model = Shipment
    extra = 0
    max_num = 1
    fields = ['carrier', 'tracking_number', 'status', 'estimated_delivery', 'notes']


class OrderMessageInline(admin.TabularInline):
    model = OrderMessage
    extra = 0
    readonly_fields = ['created_at']
    fields = ['sender', 'message_type', 'subject', 'body', 'is_from_staff', 'is_read', 'created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'first_name', 'payment_status', 'status', 'total_display', 'created_at']
    list_filter = ['payment_status', 'status', 'created_at']
    list_editable = ['payment_status', 'status']
    search_fields = ['first_name', 'last_name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline, ShipmentInline, OrderMessageInline]
    list_per_page = 25

    def total_display(self, obj):
        return f'${obj.total:,.0f}'
    total_display.short_description = 'Total'


@admin.register(OrderMessage)
class OrderMessageAdmin(admin.ModelAdmin):
    list_display = ['order', 'sender', 'message_type', 'subject', 'is_from_staff', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_from_staff', 'is_read']
    list_editable = ['is_read']
