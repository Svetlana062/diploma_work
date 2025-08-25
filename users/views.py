from django.shortcuts import render, redirect
from .forms import LoginForm, RegistrationForm
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from django.contrib.auth import authenticate, login
import stripe
from .models import Payment
from .serializers import UserRegistrationSerializer, UserProfileSerializer
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        form = RegistrationForm()
        return render(request, "users/register.html", {"form": form})

    def post(self, request):
        # Для HTML формы
        if request.content_type == "application/x-www-form-urlencoded":
            form = RegistrationForm(request.POST)
            if form.is_valid():
                # Создаем пользователя через сериализатор
                serializer = UserRegistrationSerializer(data=form.cleaned_data)
                if serializer.is_valid():
                    user = serializer.save()
                    login(request, user)
                    return redirect("/entries/")  # Редирект на страницу записей после регистрации
                else:
                    # Добавляем ошибки сериализатора к форме
                    for field, errors in serializer.errors.items():
                        for error in errors:
                            form.add_error(field, error)
            return render(request, "users/register.html", {"form": form})

        # Для API запросов (JSON)
        else:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        form = LoginForm()
        return render(request, "users/login.html", {"form": form})

    def post(self, request):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            phone = form.cleaned_data["phone"]
            password = request.POST.get("password")
            user = authenticate(request, phone=phone, password=password)
            if user is not None:
                login(request, user)
                # Редирект на главную страницу или другую нужную вам страницу
                return redirect("/entries/")  # Редирект на страницу записей после входа
            else:
                form.add_error(None, "Неверные учетные данные")
        return render(request, "users/login.html", {"form": form})


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserProfileHTMLView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        return context


class SubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "rub",
                            "product_data": {
                                "name": "Premium Subscription",
                            },
                            "unit_amount": 50000,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=settings.STRIPE_SUCCESS_URL,
                cancel_url=settings.STRIPE_CANCEL_URL,
                customer_email=request.user.email,
                metadata={"user_id": request.user.id},
            )

            Payment.objects.create(user=request.user, amount=500, stripe_session_id=session.id, status="pending")

            return Response({"session_id": session.id, "url": session.url})

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaymentWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META["HTTP_STRIPE_SIGNATURE"]

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]

            try:
                payment = Payment.objects.get(stripe_session_id=session.id, status="pending")
                payment.mark_as_paid()

            except Payment.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_200_OK)


# Для восстановления пароля


class UserPasswordResetView(PasswordResetView):
    template_name = "users/registration/password_reset.html"
    email_template_name = "users/registration/password_reset_email.html"
    success_url = reverse_lazy("password_reset_done")


class UserPasswordResetDoneView(PasswordResetDoneView):
    template_name = "users/registration/password_reset_done.html"


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "users/registration/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class UserPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "users/registration/password_reset_complete.html"
