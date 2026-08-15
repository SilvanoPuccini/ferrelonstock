from django.contrib import admin
from django.http import HttpResponse
from import_export import resources, fields
from import_export.admin import ExportMixin
from .models import Order, OrderItem, OrderMessage
from shipping.models import Shipment
import csv


class OrderResource(resources.ModelResource):
    total = fields.Field(column_name='Total')
    items_count = fields.Field(column_name='Items')

    class Meta:
        model = Order
        fields = ('id', 'first_name', 'last_name', 'email', 'phone',
                  'address', 'city', 'region', 'postal_code',
                  'payment_status', 'status', 'shipping_price',
                  'total', 'items_count', 'created_at')
        export_order = ('id', 'created_at', 'first_name', 'last_name', 'email',
                       'payment_status', 'status', 'items_count', 'total',
                       'city', 'region')

    def dehydrate_total(self, order):
        return str(order.total)

    def dehydrate_items_count(self, order):
        return str(order.total_items)


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


def _change_status(queryset, status):
    """Cambia el estado guardando cada pedido para que el email de
    actualización se dispare (queryset.update() bypasea Order.save())."""
    for order in queryset:
        order.status = status
        order.save(update_fields=['status'])


def mark_preparing(modeladmin, request, queryset):
    _change_status(queryset, 'preparing')
mark_preparing.short_description = 'Marcar en preparacion'

def mark_shipped(modeladmin, request, queryset):
    _change_status(queryset, 'shipped')
mark_shipped.short_description = 'Marcar como enviado'

def mark_delivered(modeladmin, request, queryset):
    _change_status(queryset, 'delivered')
mark_delivered.short_description = 'Marcar como entregado'

def mark_cancelled(modeladmin, request, queryset):
    _change_status(queryset, 'cancelled')
mark_cancelled.short_description = 'Marcar como cancelado'

def send_test_email(modeladmin, request, queryset):
    """Envía un email de prueba real (confirmación de pedido) para verificar
    que el SMTP (Brevo) funciona desde el servidor desplegado. Va a
    NOTIFICATION_EMAIL si está configurado, sino al email del pedido."""
    from django.conf import settings
    from django.contrib import messages
    from .emails import send_order_confirmation

    order = queryset.first()
    if order is None:
        messages.warning(request, 'Seleccioná un pedido para el envío de prueba.')
        return

    target = settings.NOTIFICATION_EMAIL or order.email
    send_order_confirmation(order)
    messages.success(
        request,
        f'Email de prueba enviado a {target}. Revisá la casilla (y el spam).'
    )
send_test_email.short_description = 'Enviar email de prueba (confirmacion de pedido)'

def export_orders_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="pedidos.csv"'
    response.write('\ufeff')  # BOM para Excel
    writer = csv.writer(response)
    writer.writerow(['ID', 'Fecha', 'Cliente', 'Email', 'Telefono',
                     'Ciudad', 'Estado Pago', 'Estado Pedido', 'Items', 'Total'])
    for order in queryset.select_related('user'):
        writer.writerow([
            order.id,
            order.created_at.strftime('%d/%m/%Y %H:%M'),
            f'{order.first_name} {order.last_name}',
            order.email,
            order.phone,
            order.city,
            order.get_payment_status_display(),
            order.get_status_display(),
            order.total_items,
            f'${order.total:,.0f}',
        ])
    return response
export_orders_csv.short_description = 'Exportar seleccionados a CSV'


@admin.register(Order)
class OrderAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = OrderResource
    list_display = ['id', 'user', 'first_name', 'payment_status', 'status', 'total_display', 'created_at']
    list_filter = ['payment_status', 'status', 'created_at']
    list_editable = ['payment_status', 'status']
    search_fields = ['first_name', 'last_name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline, ShipmentInline, OrderMessageInline]
    list_per_page = 25
    actions = [mark_preparing, mark_shipped, mark_delivered, mark_cancelled, export_orders_csv, send_test_email]

    def total_display(self, obj):
        return '${:,.0f}'.format(obj.total)
    total_display.short_description = 'Total'


@admin.register(OrderMessage)
class OrderMessageAdmin(admin.ModelAdmin):
    list_display = ['order', 'sender', 'message_type', 'subject', 'is_from_staff', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_from_staff', 'is_read']
    list_editable = ['is_read']
