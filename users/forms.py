from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Форма для создания нового пользователя."""

    class Meta:
        model = CustomUser
        fields = ["username", "phone", "email"]  # Убраны лишние поля


class RegistrationForm(UserCreationForm):
    """Форма для регистрации нового пользователя."""

    email = forms.EmailField(required=True)
    phone = forms.CharField(required=True, label="Телефон", max_length=15)

    class Meta:
        model = CustomUser
        fields = (
            "phone",
            "username",
            "email",
            "password1",
            "password2",
        )


class LoginForm(AuthenticationForm):
    """Форма входа пользователя по номеру телефона."""

    phone = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
