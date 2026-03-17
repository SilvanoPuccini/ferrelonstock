from django.views.generic import TemplateView, CreateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from .forms import ContactForm
from .models import TeamMember


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from shop.models import Product, Category
        context['featured_products'] = Product.objects.filter(
            available=True, featured=True
        )[:8]
        context['categories'] = Category.objects.all()[:6]
        return context


class ContactView(CreateView):
    template_name = 'core/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('core:contact')

    def form_valid(self, form):
        messages.success(self.request, _('¡Mensaje enviado con éxito! Te responderemos pronto.'))
        return super().form_valid(form)


class AboutView(TemplateView):
    template_name = 'core/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = TeamMember.objects.filter(is_active=True)
        return context


class TermsView(TemplateView):
    template_name = 'core/terms.html'


class PrivacyView(TemplateView):
    template_name = 'core/privacy.html'
