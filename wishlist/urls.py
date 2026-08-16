from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('', views.wishlist_detail, name='detail'),
    path('add/<int:product_id>/', views.wishlist_add, name='add'),
    path('remove/<int:product_id>/', views.wishlist_remove, name='remove'),
    path('toggle/<int:product_id>/', views.wishlist_toggle_button, name='toggle_button'),
]