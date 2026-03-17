from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.contrib.postgres.search import TrigramSimilarity
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Category, Brand
from .forms import ReviewForm


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
        return ['shop/product_list.html']

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
        context['reviews'] = self.object.reviews.select_related('user')
        context['review_form'] = ReviewForm()
        # Verificar si el usuario ya dejó review
        if self.request.user.is_authenticated:
            context['user_has_reviewed'] = self.object.reviews.filter(user=self.request.user).exists()
        return context


@login_required
def submit_review(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)

    if product.reviews.filter(user=request.user).exists():
        messages.warning(request, 'Ya dejaste una valoración para este producto.')
        return redirect('shop:product_detail', slug=slug)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Gracias por tu valoración.')

    return redirect('shop:product_detail', slug=slug)


def offers_list(request):
    products = Product.objects.filter(
        available=True,
        discount_price__isnull=False
    ).select_related('category', 'brand')
    return render(request, 'shop/offers.html', {'products': products})
