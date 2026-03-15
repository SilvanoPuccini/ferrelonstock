from django import forms
from .models import Contact

tw = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm'

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': tw, 'placeholder': 'Tu nombre'}),
            'email': forms.EmailInput(attrs={'class': tw, 'placeholder': 'tu@email.com'}),
            'subject': forms.TextInput(attrs={'class': tw, 'placeholder': 'Asunto del mensaje'}),
            'message': forms.Textarea(attrs={'class': tw, 'placeholder': 'Escribí tu mensaje...', 'rows': 5}),
        }
