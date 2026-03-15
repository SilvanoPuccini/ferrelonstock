from django import forms
from .models import Order, OrderMessage

tw = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm'


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'address', 'city', 'region', 'postal_code', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': tw, 'placeholder': 'Juan'}),
            'last_name': forms.TextInput(attrs={'class': tw, 'placeholder': 'Pérez'}),
            'email': forms.EmailInput(attrs={'class': tw, 'placeholder': 'tu@email.com'}),
            'phone': forms.TextInput(attrs={'class': tw, 'placeholder': '+54 11 1234-5678'}),
            'address': forms.TextInput(attrs={'class': tw, 'placeholder': 'Calle 123, depto 4'}),
            'city': forms.TextInput(attrs={'class': tw, 'placeholder': 'CABA'}),
            'region': forms.TextInput(attrs={'class': tw, 'placeholder': 'Buenos Aires'}),
            'postal_code': forms.TextInput(attrs={'class': tw, 'placeholder': 'C1043'}),
            'notes': forms.Textarea(attrs={'class': tw, 'placeholder': 'Instrucciones especiales...', 'rows': 3}),
        }


class OrderMessageForm(forms.ModelForm):
    class Meta:
        model = OrderMessage
        fields = ['message_type', 'subject', 'body']
        widgets = {
            'message_type': forms.Select(attrs={'class': tw}),
            'subject': forms.TextInput(attrs={'class': tw, 'placeholder': 'Asunto de tu consulta'}),
            'body': forms.Textarea(attrs={'class': tw, 'placeholder': 'Escribí tu mensaje...', 'rows': 4}),
        }
