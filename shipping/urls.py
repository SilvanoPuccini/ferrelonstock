from django.urls import path
from . import views
from . import webhooks

app_name = 'shipping'

urlpatterns = [
    path('calculator/', views.shipping_calculator, name='calculator'),
    path('tracking/<int:order_id>/', views.tracking_view, name='tracking'),

    # Webhooks (los correos llaman a estos endpoints)
    path('webhook/update/', webhooks.generic_webhook, name='webhook_generic'),
    path('webhook/andreani/', webhooks.andreani_webhook, name='webhook_andreani'),
    path('webhook/oca/', webhooks.oca_webhook, name='webhook_oca'),
]
