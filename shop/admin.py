from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'available', 'featured', 'created_at']
    list_filter = ['available', 'featured', 'category', 'created_at']
    list_editable = ['price', 'stock', 'available', 'featured']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    list_per_page = 25
    actions = ['make_available', 'make_unavailable']

    @admin.action(description='Marcar como disponible')
    def make_available(self, request, queryset):
        queryset.update(available=True)

    @admin.action(description='Marcar como no disponible')
    def make_unavailable(self, request, queryset):
        queryset.update(available=False)
