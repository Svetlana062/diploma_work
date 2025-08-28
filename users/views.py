from django.shortcuts import render, redirect
from .forms import LoginForm, RegistrationForm
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from django.contrib.auth import authenticate, login, update_session_auth_hash
import stripe
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Payment
from .serializers import UserRegistrationSerializer, UserProfileSerializer, UserLoginSerializer, JWTAuthSerializer
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy
from django.views import View
from django.contrib.auth import logout
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
import time


STRIPE_MOCK_MODE = True  # Переключить на False для реального Stripe


class UserRegistrationView(APIView):
    """API представление для регистрации нового пользователя."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """API представление для аутентификации пользователя."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            login(request, user)

            # Генерация JWT токенов
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "message": "Login successful"
            }, status=status.HTTP_200_OK)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



class UserLoginHTMLView(View):
    """HTML представление для страницы входа пользователя."""
    def get(self, request):
        form = LoginForm()
        return render(request, "users/login.html", {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["phone"]
            password = request.POST.get("password")
            user = authenticate(request, phone=phone, password=password)
            if user is not None:
                login(request, user)
                return redirect("/entries/")
            else:
                form.add_error(None, "Invalid credentials")
        return render(request, "users/login.html", {"form": form})


class UserProfileView(generics.RetrieveUpdateAPIView):
    """API представление для получения и обновления профиля пользователя."""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Возвращает объект текущего пользователя."""
        return self.request.user


class UserProfileHTMLView(LoginRequiredMixin, TemplateView):
    """HTML представление для страницы профиля пользователя."""
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        """Добавляет объект пользователя в контекст шаблона."""
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        return context


class UserRegistrationHTMLView(View):
    """HTML представление для страницы регистрации пользователя.HTML представление для страницы регистрации пользователя."""

    def get(self, request):
        """Отображает форму регистрации."""
        form = RegistrationForm()
        return render(request, "users/register.html", {"form": form})

    def post(self, request):
        """Обрабатывает отправку формы регистрации."""
        form = RegistrationForm(request.POST)
        if form.is_valid():
            serializer = UserRegistrationSerializer(data=form.cleaned_data)
            if serializer.is_valid():
                user = serializer.save()
                login(request, user)
                return redirect("/entries/")
            else:
                for field, errors in serializer.errors.items():
                    for error in errors:
                        form.add_error(field, error)
        return render(request, "users/register.html", {"form": form})


class SubscriptionView(APIView):
    """API представление для обработки подписки и платежей."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if STRIPE_MOCK_MODE:
            # Заглушка для тестирования
            mock_session_id = f"mock_session_{request.user.id}_{time.time()}"
            Payment.objects.create(
                user=request.user,
                amount=500,
                stripe_session_id=mock_session_id,
                status="paid",  # Сразу помечаем как оплаченный
            )
            request.user.is_subscribed = True
            request.user.save()
            update_session_auth_hash(request, request.user)

            return Response(
                {"session_id": mock_session_id, "url": "http://localhost:8000/entries/"}  # Редирект на главную
            )

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
    """API представление для обработки вебхуков от Stripe."""
    permission_classes = [AllowAny]

    def post(self, request):
        if STRIPE_MOCK_MODE:
            # Возвращаем успех для тестов
            return Response(status=status.HTTP_200_OK)

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
                # Обновляем сессию пользователя
                user = payment.user
                user.is_subscribed = True
                user.save()
                # Принудительно обновим все сессии пользователя
                from django.contrib.sessions.models import Session

                sessions = Session.objects.filter(session_data__contains=str(user.pk))
                for session_obj in sessions:
                    session_data = session_obj.get_decoded()
                    if "auth_user_id" in session_data and session_data["auth_user_id"] == user.pk:
                        session_obj.save()

            except Payment.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_200_OK)


class CustomLogoutView(LoginRequiredMixin, View):
    """Представление для выхода пользователя из системы."""
    def post(self, request):
        logout(request)
        return redirect("entry-list")

    def get(self, request):
        # Также разрешаем GET для совместимости
        logout(request)
        return redirect("entry-list")


# Для восстановления пароля

class UserPasswordResetView(PasswordResetView):
    """Представление для сброса пароля пользователя."""
    template_name = "registration/password_reset.html"
    email_template_name = "registration/password_reset_email.html"
    success_url = reverse_lazy("password_reset_done")


class UserPasswordResetDoneView(PasswordResetDoneView):
    """Представление для отображения страницы подтверждения отправки письма."""
    template_name = "registration/password_reset_done.html"


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    """Представление для подтверждения сброса пароля."""
    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class UserPasswordResetCompleteView(PasswordResetCompleteView):
    """Представление для отображения страницы успешного сброса пароля."""
    template_name = "registration/password_reset_complete.html"


class ForceRefreshSessionView(APIView):
    """Принудительно обновляет сессию пользователя"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        update_session_auth_hash(request, request.user)
        return Response({"status": "session refreshed"}, status=status.HTTP_200_OK)

    def get(self, request):
        update_session_auth_hash(request, request.user)
        return redirect("entry-list")


class JWTAuthView(APIView):
    """API представление для аутентификации через JWT токены."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = JWTAuthSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            return Response(
                {
                    "refresh": serializer.validated_data["refresh"],
                    "access": serializer.validated_data["access"],
                    "user": UserProfileSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JWTSignupView(APIView):
    """API представление для регистрации с JWT токенами."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Генерируем JWT токены после регистрации
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": UserProfileSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JWTLogoutView(APIView):
    """API представление для выхода из системы с JWT токенами."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)
