from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

tw = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm'


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': tw, 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': tw, 'placeholder': 'Apellido'}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'city', 'region', 'postal_code', 'avatar']
        widgets = {
            'phone': forms.TextInput(attrs={'class': tw, 'placeholder': '+54 11 1234-5678'}),
            'address': forms.TextInput(attrs={'class': tw, 'placeholder': 'Av. Corrientes 1234'}),
            'city': forms.TextInput(attrs={'class': tw, 'placeholder': 'CABA'}),
            'region': forms.TextInput(attrs={'class': tw, 'placeholder': 'Buenos Aires'}),
            'postal_code': forms.TextInput(attrs={'class': tw, 'placeholder': 'C1043'}),
            'avatar': forms.FileInput(attrs={'class': 'text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100'}),
        }
