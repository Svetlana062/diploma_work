from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from .models import Payment
from .forms import CustomUserCreationForm, RegistrationForm, LoginForm
from .models import CustomUser
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer

User = get_user_model()


class CustomUserModelTest(TestCase):
    """Тесты для модели CustomUser."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", phone="+1234567890", email="testuser@example.com", password="testpass123"
        )

    def test_user_creation(self):
        """Тест создания пользователя."""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.phone, "+1234567890")
        self.assertEqual(self.user.email, "testuser@example.com")
        self.assertFalse(self.user.is_paid)

    def test_string_representation(self):
        """Тест строкового представления."""
        self.assertEqual(str(self.user), "+1234567890")


class UserRegistrationTest(APITestCase):
    """Тесты для регистрации пользователей."""

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
        """Тест валидной регистрации пользователя."""
        response = self.client.post(reverse("api-register"), self.valid_payload, format="json")
        print(f"Registration response: {response.status_code}")
        print(f"Registration data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_invalid_user_registration(self):
        """Тест невалидной регистрации пользователя."""
        response = self.client.post(reverse("api-register"), self.invalid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)


class UserLoginTest(APITestCase):
    """Тесты для входа пользователей."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", phone="+1234567890", email="testuser@example.com", password="testpass123"
        )
        self.valid_payload = {"phone": "+1234567890", "password": "testpass123"}
        self.invalid_payload = {"phone": "+1234567890", "password": "wrongpassword"}

    def test_valid_user_login(self):
        """Тест валидного входа пользователя."""
        response = self.client.post(reverse("api-login"), self.valid_payload, format="json")
        print(f"Login response: {response.status_code}")
        print(f"Login data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем, что в ответе есть сообщение об успешном входе
        self.assertIn("message", response.data)

    def test_invalid_user_login(self):
        """Тест невалидного входа пользователя."""
        response = self.client.post(reverse("api-login"), self.invalid_payload, format="json")
        print(f"Invalid login response: {response.status_code}")
        print(f"Invalid login data: {response.data}")
        # Проверяем, что возвращается ошибка (может быть 400 или 401 в зависимости от реализации)
        self.assertTrue(response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])


class UserProfileTest(APITestCase):
    """Тесты для профиля пользователя."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", phone="+1234567890", email="testuser@example.com", password="testpass123"
        )
        # Аутентифицируем пользователя
        self.client.force_authenticate(user=self.user)

    def test_user_profile_retrieval(self):
        """Тест получения профиля пользователя."""
        # Попробуем оба возможных имени маршрута
        try:
            response = self.client.get(reverse("profile-api"))
        except NoReverseMatch:
            response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone"], self.user.phone)

    def test_user_profile_update(self):
        """Тест обновления профиля пользователя."""
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
    """Тесты для модели Payment."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", phone="+1234567890", email="testuser@example.com", password="testpass123"
        )
        self.payment = Payment.objects.create(
            user=self.user, amount=100.00, stripe_session_id="test_session_id", status="pending"
        )

    def test_payment_creation(self):
        """Тест создания платежа."""
        self.assertEqual(self.payment.amount, 100.00)
        self.assertEqual(self.payment.status, "pending")

    def test_mark_as_paid(self):
        """Тест метода mark_as_paid."""
        self.payment.mark_as_paid()
        self.assertEqual(self.payment.status, "paid")
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_paid)


class PaymentWebhookTest(APITestCase):
    """Тесты для вебхука платежей."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", phone="+1234567890", email="testuser@example.com", password="testpass123"
        )
        self.payment = Payment.objects.create(
            user=self.user, amount=100.00, stripe_session_id="test_session_id", status="pending"
        )


# Тест для отладки
class DebugTest(APITestCase):
    """Тест для отладки."""

    def test_debug_registration(self):
        """Тест для отладки регистрации."""
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


class JWTAuthViewTest(APITestCase):
    """Тесты для аутентификации JWT."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", phone="+1234567890", email="testuser@example.com", password="testpass123"
        )
        self.valid_payload = {"phone": "+1234567890", "password": "testpass123"}
        self.invalid_payload = {"phone": "+1234567890", "password": "wrongpassword"}

    def test_valid_jwt_auth(self):
        """Тест валидной аутентификации JWT."""
        response = self.client.post(reverse("jwt-auth"), self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_invalid_jwt_auth(self):
        """Тест невалидной аутентификации JWT."""
        response = self.client.post(reverse("jwt-auth"), self.invalid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserViewsTest(APITestCase):
    """Тесты для представлений пользователей."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", phone="+1234567890", email="testuser@example.com", password="testpass123"
        )
        self.client = APIClient()

    def test_user_registration(self):
        """Тест регистрации пользователя"""
        response = self.client.post(
            reverse("api-register"),
            {
                "phone": "+1234567891",
                "email": "newuser@example.com",
                "username": "newuser",
                "password1": "newpassword123",
                "password2": "newpassword123",
            },
        )

        print("Registration response:", response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(phone="+1234567891").exists())

    def test_user_login(self):
        """Тест входа пользователя"""
        response = self.client.post(
            reverse("api-login"), {"phone": "+1234567890", "password": "testpass123"}  # Изменено на 'api-login'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

    def test_user_profile(self):
        """Тест получения и обновления профиля пользователя"""
        # Сначала логинимся
        login_response = self.client.post(
            reverse("api-login"), {"phone": "+1234567890", "password": "testpass123"}  # Изменено на 'api-login'
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Теперь получаем профиль
        response = self.client.get(reverse("profile-api"))  # Изменено на 'profile-api'
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")

    def test_subscription(self):
        """Тест подписки пользователя"""
        # Сначала логинимся
        login_response = self.client.post(
            reverse("api-login"), {"phone": "+1234567890", "password": "testpass123"}  # Изменено на 'api-login'
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        response = self.client.post(reverse("subscribe"))  # Изменено на 'subscribe'
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Payment.objects.filter(user=self.user, status="paid").exists())

    def test_jwt_auth(self):
        """Тест JWT аутентификации"""
        response = self.client.post(
            reverse("jwt-auth"), {"phone": "+1234567890", "password": "testpass123"}  # Правильное имя
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_password_reset(self):
        """Тест сброса пароля"""
        response = self.client.post(reverse("password_reset"), {"email": "testuser@example.com"})
        print(f"Password reset response status: {response.status_code}")  # Логирование статуса
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)  # Проверка на редирект


class CustomUserCreationFormTest(TestCase):
    """Тесты для формы создания пользователя."""

    def setUp(self):
        self.valid_data = {
            "username": "testuser",
            "phone": "+1234567890",
            "email": "testuser@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        self.invalid_data = {
            "username": "",
            "phone": "invalid_phone",
            "email": "invalid_email",
            "password1": "testpass123",
            "password2": "differentpass",
        }

    def test_valid_form(self):
        """Тест валидной формы создания пользователя."""
        form = CustomUserCreationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    # def test_invalid_form(self):
    #     """Тест невалидной формы создания пользователя."""
    #     form = CustomUserCreationForm(data=self.invalid_data)
    #     self.assertFalse(form.is_valid())
    #     self.assertEqual(len(form.errors), 4)  # Ожидаем 4 ошибки


class RegistrationFormTest(TestCase):
    """Тесты для формы регистрации."""

    def setUp(self):
        self.valid_data = {
            "username": "testuser",
            "phone": "+1234567890",
            "email": "testuser@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        self.invalid_data = {
            "username": "",
            "phone": "invalid_phone",
            "email": "invalid_email",
            "password1": "testpass123",
            "password2": "differentpass",
        }

    def test_valid_registration_form(self):
        """Тест валидной формы регистрации."""
        form = RegistrationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())


class LoginFormTest(TestCase):
    """Тесты для формы входа."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser",
            phone="+1234567890",
            email="testuser@example.com",
            password="testpass123",
        )
        self.valid_data = {
            "phone": "+1234567890",
            "password": "testpass123",
        }
        self.invalid_data = {
            "phone": "+1234567890",
            "password": "wrongpassword",
        }

    # def test_valid_login_form(self):
    #     """Тест валидной формы входа."""
    #     form = LoginForm(data=self.valid_data)
    #     self.assertTrue(form.is_valid())

    def test_invalid_login_form(self):
        """Тест невалидной формы входа."""
        form = LoginForm(data=self.invalid_data)
        self.assertFalse(form.is_valid())


class UserRegistrationSerializerTest(TestCase):
    """Тесты для сериализатора регистрации пользователей."""

    def setUp(self):
        self.valid_data = {
            "username": "testuser",
            "phone": "+1234567890",
            "email": "testuser@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        self.invalid_data = {
            "username": "",
            "phone": "invalid_phone",
            "email": "invalid_email",
            "password1": "testpass123",
            "password2": "differentpass",
        }

    def test_valid_registration_serializer(self):
        """Тест валидного сериализатора регистрации."""
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    # def test_invalid_registration_serializer(self):
    #     """Тест невалидного сериализатора регистрации."""
    #     serializer = UserRegistrationSerializer(data=self.invalid_data)
    #     self.assertFalse(serializer.is_valid())
    #     self.assertIn("password2", serializer.errors)


class UserLoginSerializerTest(TestCase):
    """Тесты для сериализатора логина пользователей."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", phone="+1234567890", email="testuser@example.com", password="testpass123"
        )
        self.valid_data = {"phone": "+1234567890", "password": "testpass123"}
        self.invalid_data = {"phone": "+1234567890", "password": "wrongpassword"}

    def test_valid_login_serializer(self):
        """Тест валидного сериализатора логина."""
        serializer = UserLoginSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_login_serializer(self):
        """Тест невалидного сериализатора логина."""
        serializer = UserLoginSerializer(data=self.invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Invalid credentials", serializer.errors["non_field_errors"])


class UserProfileSerializerTest(TestCase):
    """Тесты для сериализатора профиля пользователя."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", phone="+1234567890", email="testuser@example.com", password="testpass123"
        )
        self.serializer = UserProfileSerializer(instance=self.user)

    def test_user_profile_serializer(self):
        """Тест сериализатора профиля пользователя."""
        data = self.serializer.data
        self.assertEqual(data["username"], self.user.username)
        self.assertEqual(data["phone"], self.user.phone)
        self.assertEqual(data["email"], self.user.email)
