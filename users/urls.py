from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views

from users import views
from users.views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
    SubscriptionView,
    PaymentWebhookView,
    UserProfileHTMLView,
)


router = DefaultRouter()

urlpatterns = [
    path("api/", include(router.urls)),  # API маршруты
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("profile/api/", UserProfileView.as_view(), name="profile-api"),  # для API
    path("profile/", UserProfileHTMLView.as_view(), name="profile"),  # для HTML
    path("subscribe/", SubscriptionView.as_view(), name="subscribe"),
    path("webhook/stripe/", PaymentWebhookView.as_view(), name="stripe-webhook"),
    # Маршруты для восстановления пароля
    path("password_reset/", views.UserPasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", views.UserPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", views.UserPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", views.UserPasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
