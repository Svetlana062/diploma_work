from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from .models import Entry
from .serializers import EntrySerializer

User = get_user_model()


class EntryModelTest(TestCase):
    """Тесты для модели Entry"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.entry = Entry.objects.create(
            title="Test Entry", content="Test Content", author=self.user, is_paid=False, price=0
        )

    def test_entry_creation(self):
        """Тест создания записи"""
        self.assertEqual(self.entry.title, "Test Entry")
        self.assertEqual(self.entry.content, "Test Content")
        self.assertEqual(self.entry.author, self.user)
        self.assertFalse(self.entry.is_paid)
        self.assertEqual(float(self.entry.price), 0.0)

    def test_string_representation(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.entry), "Test Entry")

    def test_verbose_names(self):
        """Тест verbose names"""
        self.assertEqual(Entry._meta.verbose_name, "Запись")
        self.assertEqual(Entry._meta.verbose_name_plural, "Записи")


class EntrySerializerTest(TestCase):
    """Тесты для сериализатора Entry"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.entry_data = {"title": "Test Entry", "content": "Test Content", "is_paid": False, "price": "0.00"}

    def test_valid_serializer(self):
        """Тест валидного сериализатора"""
        serializer = EntrySerializer(data=self.entry_data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_validation_paid_without_price(self):
        """Тест валидации платной записи без цены"""
        invalid_data = {"title": "Paid Entry", "content": "Paid Content", "is_paid": True, "price": None}
        serializer = EntrySerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_serializer_with_author(self):
        """Тест сериализатора с автором"""
        entry = Entry.objects.create(title="Test Entry", content="Test Content", author=self.user, is_paid=False)
        serializer = EntrySerializer(instance=entry)
        self.assertEqual(serializer.data["author"], self.user.id)
        self.assertEqual(serializer.data["author_name"], "testuser")


class EntryViewSetTest(APITestCase):
    """Тесты для ViewSet API"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.user.is_subscribed = True  # Добавляем атрибут подписки
        self.user.save()

        self.entry = Entry.objects.create(title="Test Entry", content="Test Content", author=self.user, is_paid=False)

        self.paid_entry = Entry.objects.create(
            title="Paid Entry", content="Paid Content", author=self.user, is_paid=True, price=10.00
        )

    def test_get_entries_list_authenticated(self):
        """Тест получения списка записей (аутентифицированный пользователь)"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/entries/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Видит все записи

    def test_get_entries_list_anonymous(self):
        """Тест получения списка записей (анонимный пользователь)"""
        response = self.client.get("/api/entries/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Видит только бесплатные
        self.assertFalse(response.data[0]["is_paid"])

    def test_create_entry_authenticated(self):
        """Тест создания записи"""
        self.client.force_authenticate(user=self.user)
        data = {"title": "New Entry", "content": "New Content", "is_paid": False}
        response = self.client.post("/api/entries/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Entry.objects.count(), 3)

    def test_my_entries_endpoint(self):
        """Тест endpoint /my_entries/"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/entries/my_entries/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Обе записи пользователя


class HTMLViewsTest(TestCase):
    """Тесты для HTML представлений"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.entry = Entry.objects.create(title="Test Entry", content="Test Content", author=self.user, is_paid=False)

    def test_entry_list_view(self):
        """Тест списка записей"""
        response = self.client.get(reverse("entry-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Entry")

    def test_entry_detail_view(self):
        """Тест детальной страницы записи"""
        response = self.client.get(reverse("entry-detail", args=[self.entry.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Content")

    def test_create_entry_view_authenticated(self):
        """Тест создания записи (аутентифицированный)"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("entry-create"))
        self.assertEqual(response.status_code, 200)

    def test_create_entry_view_anonymous(self):
        """Тест создания записи (анонимный) - должен редиректить на login"""
        response = self.client.get(reverse("entry-create"))
        self.assertEqual(response.status_code, 302)  # Редирект на login


class AccessControlTest(TestCase):
    """Тесты контроля доступа"""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")
        self.entry = Entry.objects.create(
            title="User1 Entry", content="Private Content", author=self.user1, is_paid=False
        )

    def test_update_own_entry(self):
        """Тест обновления своей записи"""
        self.client.login(username="user1", password="pass123")
        response = self.client.get(reverse("entry-update", args=[self.entry.pk]))
        self.assertEqual(response.status_code, 200)

    def test_update_other_user_entry(self):
        """Тест попытки обновления чужой записи"""
        self.client.login(username="user2", password="pass123")
        response = self.client.get(reverse("entry-update", args=[self.entry.pk]))
        self.assertEqual(response.status_code, 404)  # Не должен находить запись
