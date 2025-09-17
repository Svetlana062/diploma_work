from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Payment


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Административный класс для модели CustomUser."""

    model = CustomUser
    list_display = ("id", "phone", "email", "username", "is_paid", "is_active", "is_staff")
    list_filter = ("is_paid", "is_active", "is_staff")
    search_fields = ("phone", "email", "username")
    ordering = ("phone",)

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Персональная информация", {"fields": ("username", "email")}),
        ("Подписка", {"fields": ("is_paid",)}),
        ("Права доступа", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Важные даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "email", "username", "password1", "password2"),
            },
        ),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Административный класс для модели Payment."""

    list_display = ("id", "user", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__phone", "user__email", "stripe_session_id")
    readonly_fields = ("created_at",)
    list_per_page = 20
