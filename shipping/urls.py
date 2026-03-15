from django.urls import path
from . import views

app_name = 'shipping'

urlpatterns = [
    path('calculator/', views.shipping_calculator, name='calculator'),
    path('tracking/<int:order_id>/', views.tracking_view, name='tracking'),
]
