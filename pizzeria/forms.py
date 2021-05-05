import re
from datetime import datetime, timedelta

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Order, Customer

PHONE_RE = r'\b380\d{9}$\b'
NAMES_RE = r'\b[A-Z][a-z]+$\b'


def names_phone_validation(first_name, last_name, phone):
    if not re.match(PHONE_RE, phone):
        raise ValidationError('Input a valid phone number: "380" and 9 digits after')

    if not re.match(NAMES_RE, first_name):
        raise ValidationError('Input a valid first name')

    if not re.match(NAMES_RE, last_name):
        raise ValidationError('Input a valid last name')

    return first_name, last_name, phone


class OrderForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'address', 'delivery', 'comment', 'order_date_time']

    def clean(self):
        cleaned_data = super().clean()

        phone = cleaned_data['phone']
        first_name = cleaned_data['first_name']
        last_name = cleaned_data['last_name']
        names_phone_validation(first_name, last_name, phone)

        current_date_time = datetime.now()
        order_date_time = cleaned_data['order_date_time']
        if order_date_time < current_date_time + timedelta(hours=1):
            raise ValidationError('Choose the valid date and time, it must be later at least for an hour then now')

        return cleaned_data


class CreateUserForm(UserCreationForm):
    address = forms.CharField(max_length=100)
    phone_number = forms.CharField(max_length=12)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'address', 'phone_number', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()

        phone = cleaned_data['phone_number']
        first_name = cleaned_data['first_name']
        last_name = cleaned_data['last_name']
        names_phone_validation(first_name, last_name, phone)

        email = cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('Email exists')
        if Customer.objects.filter(phone_number=phone).exists():
            raise ValidationError('Phone exists')

        return cleaned_data
