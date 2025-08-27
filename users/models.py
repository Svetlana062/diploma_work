from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    """Пользовательская модель, расширяющая стандартную AbstractUser."""
    username = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(
        max_length=16,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
            )
        ],
        unique=True,
    )
    is_paid = models.BooleanField(default=False)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.phone}"


class Payment(models.Model):
    """Модель, представляющая платеж, совершенный пользователем."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_session_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_as_paid(self):
        """Помечает платеж как оплаченный и обновляет статус оплаты пользователя."""
        self.status = "paid"
        self.user.is_paid = True
        self.user.save()
        self.save()
