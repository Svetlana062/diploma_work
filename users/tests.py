from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from .models import Payment

User = get_user_model()


class CustomUserModelTest(TestCase):
    """Тесты для модели CustomUser"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", phone="+1234567890", email="testuser@example.com", password="testpass123"
        )

    def test_user_creation(self):
        """Тест создания пользователя"""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.phone, "+1234567890")
        self.assertEqual(self.user.email, "testuser@example.com")
        self.assertFalse(self.user.is_paid)

    def test_string_representation(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.user), "+1234567890")


class UserRegistrationTest(TestCase):
    """Тесты для регистрации пользователей"""

    def setUp(self):
        self.client = APIClient()
        self.valid_payload = {
            "username": "testuser",
            "phone": "+1234567890",
            "email": "testuser@example.com",
            "password": "testpass123",
        }
        self.invalid_payload = {
            "username": "",
            "phone": "invalid_phone",
            "email": "invalid_email",
            "password": "testpass123",
        }

    def test_valid_user_registration(self):
        """Тест валидной регистрации пользователя"""
        response = self.client.post(reverse("register"), self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_invalid_user_registration(self):
        """Тест невалидной регистрации пользователя"""
        response = self.client.post(reverse("register"), self.invalid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)


class UserLoginTest(TestCase):
    """Тесты для входа пользователей"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", phone="+1234567890", email="testuser@example.com", password="testpass123"
        )
        self.valid_payload = {"phone": "+1234567890", "password": "testpass123"}
        self.invalid_payload = {"phone": "+1234567890", "password": "wrongpassword"}

    def test_valid_user_login(self):
        """Тест валидного входа пользователя"""
        response = self.client.post(reverse("login"), self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)

    def test_invalid_user_login(self):
        """Тест невалидного входа пользователя"""
        response = self.client.post(reverse("login"), self.invalid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("user", response.data)


class UserProfileTest(TestCase):
    """Тесты для профиля пользователя"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", phone="+1234567890", email="testuser@example.com", password="testpass123"
        )
        self.client.login(phone="+1234567890", password="testpass123")

    def test_user_profile_retrieval(self):
        """Тест получения профиля пользователя"""
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone"], self.user.phone)

    def test_user_profile_update(self):
        """Тест обновления профиля пользователя"""
        response = self.client.patch(reverse("profile"), {"username": "newusername"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "newusername")


class PaymentModelTest(TestCase):
    """Тесты для модели Payment"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", phone="+1234567890", email="testuser@example.com", password="testpass123"
        )
        self.payment = Payment.objects.create(
            user=self.user, amount=100.00, stripe_session_id="test_session_id", status="pending"
        )

    def test_payment_creation(self):
        """Тест создания платежа"""
        self.assertEqual(self.payment.amount, 100.00)
        self.assertEqual(self.payment.status, "pending")

    def test_mark_as_paid(self):
        """Тест метода mark_as_paid"""
        self.payment.mark_as_paid()
        self.assertEqual(self.payment.status, "paid")
        self.assertTrue(self.user.is_paid)


class PaymentWebhookTest(TestCase):
    """Тесты для вебхука платежей"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", phone="+1234567890", email="testuser@example.com", password="testpass123"
        )
        self.payment = Payment.objects.create(
            user=self.user, amount=100.00, stripe_session_id="test_session_id", status="pending"
        )

    def test_webhook_payment_success(self):
        """Тест успешного вебхука платежа"""
        # Здесь вам нужно будет использовать библиотеку mock для имитации события Stripe
        pass  # Реализуйте тест для успешного вебхука

    def test_webhook_payment_failure(self):
        """Тест неуспешного вебхука платежа"""
        # Здесь вам нужно будет использовать библиотеку mock для имитации события Stripe
        pass  # Реализуйте тест для неуспешного вебхука
