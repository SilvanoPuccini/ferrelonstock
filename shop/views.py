from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.contrib.postgres.search import TrigramSimilarity
from .models import Product, Category, Brand


class ProductListView(ListView):
    model = Product
    template_name = 'shop/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.filter(available=True).select_related('category', 'brand')

        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        brand_slug = self.kwargs.get('brand_slug')
        if brand_slug:
            qs = qs.filter(brand__slug=brand_slug)

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.annotate(
                name_sim=TrigramSimilarity('name', q),
                brand_sim=TrigramSimilarity('brand__name', q),
            ).filter(
                Q(name_sim__gt=0.1) | Q(brand_sim__gt=0.1) |
                Q(name__icontains=q) | Q(brand__name__icontains=q)
            ).order_by('-name_sim', '-brand_sim')

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['brands'] = Brand.objects.all()
        context['current_category'] = self.kwargs.get('category_slug', '')
        context['current_brand'] = self.kwargs.get('brand_slug', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context
	
    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['shop/_product_grid.html']
        return [self.template_name]

class ProductDetailView(DetailView):
    model = Product
    template_name = 'shop/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Product.objects.filter(available=True).select_related('category', 'brand')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_products'] = Product.objects.filter(
            category=self.object.category, available=True
        ).exclude(pk=self.object.pk).select_related('brand')[:4]
        context['gallery'] = self.object.images.all()
        return context


def offers_list(request):
    products = Product.objects.filter(
        available=True,
        discount_price__isnull=False
    ).select_related('category', 'brand')
    return render(request, 'shop/offers.html', {'products': products})
