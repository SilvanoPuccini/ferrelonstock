from django.urls import path
from . import views
from . import invoice

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    path('history/', views.order_history, name='order_history'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('<int:order_id>/message/', views.order_send_message, name='order_send_message'),
    path('<int:order_id>/invoice/', invoice.download_invoice, name='download_invoice'),
]
