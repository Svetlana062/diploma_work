from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserRegistrationView, UserLoginView, UserProfileView, SubscriptionView, PaymentWebhookView

router = DefaultRouter()

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("subscribe/", SubscriptionView.as_view(), name="subscribe"),
    path("webhook/stripe/", PaymentWebhookView.as_view(), name="stripe-webhook"),
    path("", include(router.urls)),
]
