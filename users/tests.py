from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
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


class UserRegistrationTest(APITestCase):
    """Тесты для регистрации пользователей"""

    def setUp(self):
        self.client = APIClient()
        self.valid_payload = {
            "username": "testuser",
            "phone": "+1234567890",
            "email": "testuser@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        self.invalid_payload = {
            "username": "",
            "phone": "invalid_phone",
            "email": "invalid_email",
            "password1": "testpass123",
            "password2": "wrongpassword",
        }

    def test_valid_user_registration(self):
        """Тест валидной регистрации пользователя"""
        response = self.client.post(reverse("api-register"), self.valid_payload, format="json")
        print(f"Registration response: {response.status_code}")
        print(f"Registration data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_invalid_user_registration(self):
        """Тест невалидной регистрации пользователя"""
        response = self.client.post(reverse("api-register"), self.invalid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)


class UserLoginTest(APITestCase):
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
        response = self.client.post(reverse("api-login"), self.valid_payload, format="json")
        print(f"Login response: {response.status_code}")
        print(f"Login data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем, что в ответе есть сообщение об успешном входе
        self.assertIn("message", response.data)

    def test_invalid_user_login(self):
        """Тест невалидного входа пользователя"""
        response = self.client.post(reverse("api-login"), self.invalid_payload, format="json")
        print(f"Invalid login response: {response.status_code}")
        print(f"Invalid login data: {response.data}")
        # Проверяем, что возвращается ошибка (может быть 400 или 401 в зависимости от реализации)
        self.assertTrue(response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])


class UserProfileTest(APITestCase):
    """Тесты для профиля пользователя"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", phone="+1234567890", email="testuser@example.com", password="testpass123"
        )
        # Аутентифицируем пользователя
        self.client.force_authenticate(user=self.user)

    def test_user_profile_retrieval(self):
        """Тест получения профиля пользователя"""
        # Попробуем оба возможных имени маршрута
        try:
            response = self.client.get(reverse("profile-api"))
        except NoReverseMatch:
            response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone"], self.user.phone)

    def test_user_profile_update(self):
        """Тест обновления профиля пользователя"""
        # Попробуем оба возможных имени маршрута
        try:
            url = reverse("profile-api")
        except NoReverseMatch:
            url = reverse("profile")

        response = self.client.patch(url, {"username": "newusername"}, format="json")
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
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_paid)


class PaymentWebhookTest(APITestCase):
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
        # Заглушка для теста вебхука
        pass

    def test_webhook_payment_failure(self):
        """Тест неуспешного вебхука платежа"""
        # Заглушка для теста вебхука
        pass


# Тест для отладки
class DebugTest(APITestCase):
    """Тест для отладки"""

    def test_debug_registration(self):
        """Тест для отладки регистрации"""
        payload = {
            "username": "debuguser",
            "phone": "+1234567891",
            "email": "debug@example.com",
            "password1": "debugpass123",
            "password2": "debugpass123",
        }

        response = self.client.post(reverse("api-register"), payload, format="json")
        print(f"Debug registration status: {response.status_code}")
        print(f"Debug registration data: {response.data}")

        # Если есть ошибки, выведем их
        if response.status_code != 201:
            print("Errors:", response.data)
