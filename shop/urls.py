from django.urls import path
from . import views
from .views import ProductListView, ProductDetailView

app_name = 'shop'

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('category/<slug:category_slug>/', ProductListView.as_view(), name='product_list_by_category'),
    path('brand/<slug:brand_slug>/', ProductListView.as_view(), name='product_list_by_brand'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('product/<slug:slug>/review/', views.submit_review, name='submit_review'),
    path('offers/', views.offers_list, name='offers'),
]
