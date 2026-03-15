from django.contrib import admin
from .models import Order, OrderItem, OrderMessage


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ['get_total']

    def get_total(self, obj):
        return f'${obj.get_total:,.0f}'
    get_total.short_description = 'Total'


class OrderMessageInline(admin.TabularInline):
    model = OrderMessage
    extra = 1
    readonly_fields = ['created_at']
    fields = ['sender', 'message_type', 'subject', 'body', 'is_from_staff', 'is_read', 'created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'first_name', 'last_name', 'payment_status', 'status', 'total', 'created_at']
    list_filter = ['payment_status', 'status', 'created_at']
    list_editable = ['payment_status', 'status']
    search_fields = ['first_name', 'last_name', 'email', 'address']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline, OrderMessageInline]
    list_per_page = 25

    def total(self, obj):
        return f'${obj.total:,.0f}'
    total.short_description = 'Total'


@admin.register(OrderMessage)
class OrderMessageAdmin(admin.ModelAdmin):
    list_display = ['order', 'sender', 'message_type', 'subject', 'is_from_staff', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_from_staff', 'is_read']
    list_editable = ['is_read']
