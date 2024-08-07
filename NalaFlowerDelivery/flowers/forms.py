# flowers/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Order

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Enter a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')  # Убедитесь, что все необходимые поля указаны

class OrderForm(forms.Form):
    delivery_address = forms.CharField(max_length=255, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter delivery address'
    }))
    contact_phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter contact phone'
    }))

class CheckoutForm(forms.Form):
    address = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your delivery address'
    }))
    postal_code = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your postal code'
    }))
    city = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your city'
    }))
    country = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your country'
    }))