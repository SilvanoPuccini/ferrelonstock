from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ['get_total']

    def get_total(self, obj):
        return f'${obj.get_total:,.0f}'
    get_total.short_description = 'Total'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'first_name', 'last_name', 'status', 'total', 'created_at']
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    search_fields = ['first_name', 'last_name', 'email', 'address']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline]
    list_per_page = 25
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']

    def total(self, obj):
        return f'${obj.total:,.0f}'
    total.short_description = 'Total'

    @admin.action(description='Marcar como pagado')
    def mark_as_paid(self, request, queryset):
        queryset.update(status='paid')

    @admin.action(description='Marcar como enviado')
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')

    @admin.action(description='Marcar como entregado')
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')

    @admin.action(description='Marcar como cancelado')
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
