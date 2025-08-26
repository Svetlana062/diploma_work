from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Форма для создания нового пользователя."""

    class Meta:
        model = CustomUser
        fields = ["username", "phone", "email"]


class RegistrationForm(UserCreationForm):
    """Форма для регистрации нового пользователя."""

    phone = forms.CharField(required=True, label="Телефон", max_length=15)

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "phone",
            "email",
            "password1",
            "password2",
        )


class LoginForm(AuthenticationForm):
    """Форма входа пользователя по номеру телефона."""

    phone = forms.CharField(label="Телефон", max_length=15)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ("phone", "password")
