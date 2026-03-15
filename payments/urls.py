from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('select/<int:order_id>/', views.payment_select, name='payment_select'),
    path('stripe/<int:order_id>/', views.stripe_checkout, name='stripe_checkout'),
    path('stripe/success/<int:order_id>/', views.stripe_success, name='stripe_success'),
    path('mp/<int:order_id>/', views.mp_checkout, name='mp_checkout'),
    path('mp/success/<int:order_id>/', views.mp_success, name='mp_success'),
    path('cancel/<int:order_id>/', views.payment_cancel, name='payment_cancel'),
]
