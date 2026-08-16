from django.urls import path
from .views import HomeView, ContactView, AboutView, TermsView, PrivacyView
from .reports import sales_report, stock_report

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('terms/', TermsView.as_view(), name='terms'),
    path('privacy/', PrivacyView.as_view(), name='privacy'),
    path('reports/sales/', sales_report, name='sales_report'),
    path('reports/stock/', stock_report, name='stock_report'),
]
