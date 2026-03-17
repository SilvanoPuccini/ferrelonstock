import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from decimal import Decimal
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from .models import Category, Brand, Product, ProductImage, Review


# =====================================================
# RESOURCES para import/export
# =====================================================

class ProductResource(resources.ModelResource):
    category_name = fields.Field(attribute='category__name', column_name='Categoría')
    brand_name = fields.Field(attribute='brand__name', column_name='Marca')

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'category_name', 'brand_name', 'price', 'discount_price', 'stock', 'available', 'featured')
        export_order = ('id', 'name', 'category_name', 'brand_name', 'price', 'discount_price', 'stock', 'available', 'featured')
        import_id_fields = ('id',)

    def before_import_row(self, row, **kwargs):
        # Permite importar por nombre de categoría y marca
        cat_name = row.get('Categoría', '')
        if cat_name:
            cat, _ = Category.objects.get_or_create(name=cat_name, defaults={'slug': cat_name.lower().replace(' ', '-')})
            row['category'] = cat.id

        brand_name = row.get('Marca', '')
        if brand_name:
            brand, _ = Brand.objects.get_or_create(name=brand_name, defaults={'slug': brand_name.lower().replace(' ', '-')})
            row['brand'] = brand.id


class ReviewResource(resources.ModelResource):
    product_name = fields.Field(attribute='product__name', column_name='Producto')
    user_email = fields.Field(attribute='user__email', column_name='Usuario')

    class Meta:
        model = Review
        fields = ('id', 'product_name', 'user_email', 'rating', 'comment', 'created_at')
        export_order = ('id', 'product_name', 'user_email', 'rating', 'comment', 'created_at')


# =====================================================
# ADMIN
# =====================================================

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


# Funciones de descuento
def apply_discount(modeladmin, request, queryset, percent):
    factor = Decimal(str(1 - percent / 100))
    count = 0
    for product in queryset:
        product.discount_price = (product.price * factor).quantize(Decimal('1'))
        product.save()
        count += 1
    modeladmin.message_user(request, f'Descuento del {percent}%% aplicado a {count} producto(s).')


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
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = [
        'name', 'category', 'brand', 'price', 'discount_price',
        'show_discount_percent', 'show_final_price',
        'stock', 'available', 'featured', 'show_on_offer',
        'show_avg_rating', 'show_total_sold'
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
            'description': 'Pone el precio de oferta manualmente, o usa las acciones masivas para aplicar descuento por porcentaje.'
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
    show_discount_percent.short_description = '%% Desc.'

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

    def show_avg_rating(self, obj):
        if obj.review_count > 0:
            return format_html(
                '<span style="color:#f59e0b;font-weight:bold;">{}/5</span> <span style="color:#999;font-size:11px;">({})</span>',
                obj.avg_rating, obj.review_count
            )
        return '—'
    show_avg_rating.short_description = 'Valoracion'

    def show_total_sold(self, obj):
        from django.db.models import Sum
        total = obj.order_items.aggregate(Sum('quantity'))['quantity__sum'] or 0
        if total > 0:
            return format_html('<span style="font-weight:bold;">{}</span>', total)
        return '0'
    show_total_sold.short_description = 'Vendidos'


@admin.register(Review)
class ReviewAdmin(ImportExportModelAdmin):
    resource_class = ReviewResource
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__email', 'comment']
    readonly_fields = ['created_at']
