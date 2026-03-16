from django.contrib import admin
from django.utils.html import format_html
from decimal import Decimal
from .models import Category, Brand, Product
from .models import Category, Brand, Product, ProductImage

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


def apply_discount(modeladmin, request, queryset, percent):
    factor = Decimal(str(1 - percent / 100))
    count = 0
    for product in queryset:
        product.discount_price = (product.price * factor).quantize(Decimal('1'))
        product.save()
        count += 1
    modeladmin.message_user(request, f'Descuento del {percent}% aplicado a {count} producto(s).')


def discount_10(modeladmin, request, queryset):
    apply_discount(modeladmin, request, queryset, 10)
discount_10.short_description = 'Aplicar 10%% de descuento'


def discount_15(modeladmin, request, queryset):
    apply_discount(modeladmin, request, queryset, 15)
discount_15.short_description = 'Aplicar 15%% de descuento'


def discount_20(modeladmin, request, queryset):
    apply_discount(modeladmin, request, queryset, 20)
discount_20.short_description = 'Aplicar 20%% de descuento'


def discount_25(modeladmin, request, queryset):
    apply_discount(modeladmin, request, queryset, 25)
discount_25.short_description = 'Aplicar 25%% de descuento'


def discount_30(modeladmin, request, queryset):
    apply_discount(modeladmin, request, queryset, 30)
discount_30.short_description = 'Aplicar 30%% de descuento'


def discount_50(modeladmin, request, queryset):
    apply_discount(modeladmin, request, queryset, 50)
discount_50.short_description = 'Aplicar 50%% de descuento'


def remove_discount(modeladmin, request, queryset):
    count = queryset.update(discount_price=None)
    modeladmin.message_user(request, f'Descuento eliminado de {count} producto(s).')
remove_discount.short_description = 'Quitar descuento'


def make_available(modeladmin, request, queryset):
    queryset.update(available=True)
make_available.short_description = 'Marcar como disponible'


def make_unavailable(modeladmin, request, queryset):
    queryset.update(available=False)
make_unavailable.short_description = 'Marcar como no disponible'

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ['image', 'order']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'brand', 'price', 'discount_price',
        'show_discount_percent', 'show_final_price',
        'stock', 'available', 'featured', 'show_on_offer'
    ]
    list_filter = ['available', 'featured', 'category', 'brand', 'created_at']
    list_editable = ['price', 'discount_price', 'stock', 'available', 'featured']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    list_per_page = 25
    inlines = [ProductImageInline]

    fieldsets = (
        ('Producto', {
            'fields': ('name', 'slug', 'category', 'brand', 'description', 'image')
        }),
        ('Precios y descuento', {
            'fields': ('price', 'discount_price'),
            'description': 'Pone el precio de oferta manualmente, o usa las acciones masivas para aplicar descuento por porcentaje a varios productos.'
        }),
        ('Stock y visibilidad', {
            'fields': ('stock', 'available', 'featured')
        }),
    )

    actions = [
        make_available, make_unavailable,
        discount_10, discount_15, discount_20, discount_25, discount_30, discount_50,
        remove_discount,
    ]

    def show_discount_percent(self, obj):
        if obj.has_discount:
            return format_html(
                '<span style="background:#fee2e2;color:#dc2626;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold;">-{}%</span>',
                obj.discount_percent
            )
        return '—'
    show_discount_percent.short_description = '% Desc.'

    def show_final_price(self, obj):
        if obj.has_discount:
            price_str = '${:,.0f}'.format(obj.final_price)
            return format_html('<span style="color:#ea580c;font-weight:bold;">{}</span>', price_str)
        return '${:,.0f}'.format(obj.price)
    show_final_price.short_description = 'Precio final'

    def show_on_offer(self, obj):
        if obj.has_discount:
            return format_html(
                '<span style="background:#dcfce7;color:#16a34a;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold;">EN OFERTA</span>'
            )
        return ''
    show_on_offer.short_description = 'Oferta'
