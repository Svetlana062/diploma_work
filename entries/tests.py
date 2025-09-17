from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from .models import Entry
from .serializers import EntrySerializer
from entries.utils import user_has_subscription

User = get_user_model()


class EntryModelTest(TestCase):
    """Тесты для модели Entry."""

    def setUp(self):
        """Настройка тестового пользователя перед каждым тестом."""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", phone="+71234567890"  # Добавляем обязательное поле phone
        )

    def test_create_entry(self):
        """Тест создания записи Entry."""
        entry = Entry.objects.create(
            title="Тестовая запись",
            content="Это содержание тестовой записи.",
            author=self.user,
            is_paid=True,
            price=49.99,
        )
        self.assertEqual(entry.title, "Тестовая запись")
        self.assertEqual(entry.content, "Это содержание тестовой записи.")
        self.assertEqual(entry.author, self.user)
        self.assertTrue(entry.is_paid)
        self.assertEqual(entry.price, 49.99)

    def test_str_method_returns_title(self):
        """Тест метода __str__ для модели Entry."""
        entry = Entry.objects.create(
            title="Заголовок для str",
            content="Контент",
            author=self.user,
        )
        self.assertEqual(str(entry), "Заголовок для str")

    def test_default_values_for_is_paid_and_price(self):
        """Тест значений по умолчанию для полей is_paid и price."""
        entry = Entry.objects.create(
            title="Запись с дефолтными значениями",
            content="Контент",
            author=self.user,
        )
        self.assertFalse(entry.is_paid)
        self.assertEqual(entry.price, 0)

    def test_ordering_of_entries(self):
        """Тест порядка записей в базе данных."""
        entry1 = Entry.objects.create(
            title="Первая запись",
            content="Контент 1",
            author=self.user,
        )
        entry2 = Entry.objects.create(
            title="Вторая запись",
            content="Контент 2",
            author=self.user,
        )
        entries = list(Entry.objects.all())
        self.assertEqual(entries[0], entry2)
        self.assertEqual(entries[1], entry1)

    def test_content_field_max_length(self):
        """Тест максимальной длины поля title."""
        max_length_title = "A" * 200
        entry = Entry.objects.create(
            title=max_length_title,
            content="Контент",
            author=self.user,
        )
        self.assertEqual(entry.title, max_length_title)

    def test_delete_author_deletes_entries(self):
        """Тест удаления автора и связанных с ним записей."""
        entry = Entry.objects.create(
            title="Запись для удаления автора",
            content="Контент",
            author=self.user,
        )
        self.user.delete()
        self.assertFalse(Entry.objects.filter(id=entry.id).exists())


class EntrySerializerTest(TestCase):
    """Тесты для сериализатора EntrySerializer"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser", password="testpass123", phone="+71234567890")
        self.entry = Entry.objects.create(title="Test Entry", content="Test content", author=self.user, is_paid=False)
        self.paid_entry = Entry.objects.create(
            title="Paid Entry", content="Paid content", author=self.user, is_paid=True, price=100.00
        )

    def test_can_view_paid_content_anonymous(self):
        """Тест доступа к платному контенту для анонимного пользователя"""
        request = self.factory.get("/")
        request.user = AnonymousUser()

        serializer = EntrySerializer(self.paid_entry, context={"request": request})
        self.assertFalse(serializer.data["can_view"])
        self.assertEqual(serializer.data["content"], "Для просмотра платного контента необходима подписка")

    def test_can_view_paid_content_author(self):
        """Тест доступа к платному контенту для автора"""
        request = self.factory.get("/")
        request.user = self.user

        # Добавляем атрибут is_subscribed для теста
        request.user.is_subscribed = True

        serializer = EntrySerializer(self.paid_entry, context={"request": request})
        self.assertTrue(serializer.data["can_view"])
        self.assertEqual(serializer.data["content"], "Paid content")

    def test_can_view_free_content_anonymous(self):
        """Тест доступа к бесплатному контенту для анонимного пользователя"""
        request = self.factory.get("/")
        request.user = AnonymousUser()

        serializer = EntrySerializer(self.entry, context={"request": request})
        self.assertTrue(serializer.data["can_view"])
        self.assertEqual(serializer.data["content"], "Test content")

    def test_validate_paid_entry_without_price(self):
        """Тест валидации платной записи без цены"""
        data = {"title": "Test", "content": "Test content", "is_paid": True, "price": None}
        serializer = EntrySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("price", serializer.errors)


class EntryListViewTest(TestCase):
    """Тесты для HTML представлений списка записей"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123", phone="+71234567890")
        self.entry = Entry.objects.create(title="Free Entry", content="Free content", author=self.user, is_paid=False)
        self.paid_entry = Entry.objects.create(
            title="Paid Entry", content="Paid content", author=self.user, is_paid=True, price=100.00
        )

    def test_entry_list_anonymous(self):
        """Тест главной страницы для анонимного пользователя."""
        response = self.client.get(reverse("entry-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Free Entry")
        # Анонимный пользователь не должен видеть платный контент
        self.assertNotContains(response, "Paid Entry")

    def test_my_entries_list_anonymous_redirect(self):
        """Тест редиректа для анонимного пользователя на странице моих записей"""
        response = self.client.get(reverse("my-entries"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response.url)


class EntryCreateUpdateDeleteTest(TestCase):
    """Тесты для создания, обновления и удаления записей"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123", phone="+71234567890")
        self.entry = Entry.objects.create(title="Test Entry", content="Test content", author=self.user, is_paid=False)

    def test_create_entry_anonymous_redirect(self):
        """Тест редиректа при попытке создания записи анонимным пользователем."""
        response = self.client.post(
            reverse("entry-create"), {"title": "New Entry", "content": "New content", "is_paid": "false"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response.url)


class UtilsTest(TestCase):
    """Тесты для утилит приложения entries."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123", phone="+71234567890")

    def test_user_has_subscription_authenticated_with_subscription(self):
        """Тест для аутентифицированного пользователя с подпиской."""
        self.user.is_paid = True
        self.user.save()
        self.assertTrue(user_has_subscription(self.user))

    def test_user_has_subscription_authenticated_without_subscription(self):
        """Тест для аутентифицированного пользователя без подписки."""
        self.user.is_paid = False
        self.user.save()
        self.assertFalse(user_has_subscription(self.user))

    def test_user_has_subscription_anonymous(self):
        """Тест для анонимного пользователя."""
        self.assertFalse(user_has_subscription(User()))


class EntryModelAdditionalTest(TestCase):
    """Дополнительные тесты для модели Entry."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123", phone="+71234567890")

    def test_created_at_auto_now_add(self):
        """Тест автоматического добавления даты создания."""
        entry = Entry.objects.create(title="Тестовая запись", content="Содержание", author=self.user)
        self.assertIsNotNone(entry.created_at)

    def test_updated_at_auto_now(self):
        """Тест автоматического обновления даты изменения."""
        entry = Entry.objects.create(title="Тестовая запись", content="Содержание", author=self.user)
        original_updated_at = entry.updated_at

        # Изменяем запись
        entry.title = "Измененный заголовок"
        entry.save()

        self.assertNotEqual(entry.updated_at, original_updated_at)

    def test_price_field_decimal_places(self):
        """Тест корректности десятичных знаков в поле цены."""
        entry = Entry.objects.create(
            title="Тестовая запись", content="Содержание", author=self.user, is_paid=True, price=19.99
        )
        self.assertEqual(entry.price, 19.99)

    def test_verbose_names(self):
        """Тест корректности verbose_name полей."""
        entry = Entry.objects.create(title="Тестовая запись", content="Содержание", author=self.user)

        self.assertEqual(entry._meta.get_field("title").verbose_name, "Заголовок")
        self.assertEqual(entry._meta.get_field("content").verbose_name, "Содержание")
        self.assertEqual(entry._meta.get_field("author").verbose_name, "Автор")
        self.assertEqual(entry._meta.get_field("created_at").verbose_name, "Дата создания")
        self.assertEqual(entry._meta.get_field("updated_at").verbose_name, "Дата обновления")
        self.assertEqual(entry._meta.get_field("is_paid").verbose_name, "Платный контент")
        self.assertEqual(entry._meta.get_field("price").verbose_name, "Цена")


class EntryViewsAdditionalTest(TestCase):
    """Дополнительные тесты для представлений entries."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123", phone="+71234567890")
        self.entry = Entry.objects.create(title="Тестовая запись", content="Содержание", author=self.user)

    def test_free_entries_list_view(self):
        """Тест представления списка бесплатных записей."""
        response = self.client.get(reverse("free-entries"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "entries/entry_list.html")

    def test_paid_entries_list_view(self):
        """Тест представления списка платных записей."""
        response = self.client.get(reverse("paid-entries"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "entries/entry_list.html")

    def test_subscription_info_view(self):
        """Тест представления информации о подписке."""
        response = self.client.get(reverse("subscription-info"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "entries/subscription_info.html")
