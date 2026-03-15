from django.views.generic import ListView, DetailView
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
from .models import Product, Category, Brand


class ProductListView(ListView):
    model = Product
    template_name = 'shop/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(available=True).select_related('category', 'brand')
        category_slug = self.kwargs.get('category_slug')
        brand_slug = self.kwargs.get('brand_slug')
        search = self.request.GET.get('q', '').strip()

        if category_slug:
            self.current_category = Category.objects.get(slug=category_slug)
            queryset = queryset.filter(category=self.current_category)
        else:
            self.current_category = None

        if brand_slug:
            self.current_brand = Brand.objects.get(slug=brand_slug)
            queryset = queryset.filter(brand=self.current_brand)
        else:
            self.current_brand = None

        if search:
            queryset = queryset.annotate(
                name_sim=TrigramSimilarity('name', search),
                brand_sim=TrigramSimilarity('brand__name', search),
            ).filter(
                Q(name_sim__gt=0.1) | Q(brand_sim__gt=0.3)
            ).order_by('-name_sim', '-brand_sim')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['brands'] = Brand.objects.all()
        context['current_category'] = getattr(self, 'current_category', None)
        context['current_brand'] = getattr(self, 'current_brand', None)
        context['search_query'] = self.request.GET.get('q', '')
        return context

    def get_template_names(self):
        if self.request.htmx:
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
        return context
