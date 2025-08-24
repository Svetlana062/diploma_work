from django.apps import AppConfig
from django.conf import settings
import stripe


class UsersConfig(AppConfig):
    """Конфигурация приложения 'users'."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        # Инициализация Stripe при запуске приложения
        if settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY
