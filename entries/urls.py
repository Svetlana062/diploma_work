from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    EntryViewSet,
    EntryListView,
    EntryDetailView,
    EntryCreateView,
    EntryUpdateView,
    EntryDeleteView,
    MyEntriesListView,
    FreeEntriesListView,
    PaidEntriesListView,
    subscribe_view,
    subscription_info,
    custom_logout,
)

# Создаем роутер для API
router = DefaultRouter()
router.register(r"entries", EntryViewSet, basename="entry")

# Определяем HTML маршруты
html_urlpatterns = [
    path("", EntryListView.as_view(), name="entry-list"),  # Главная страница со списком записей
    path("free/", FreeEntriesListView.as_view(), name="free-entries"),  # Бесплатные записи
    path("my/", MyEntriesListView.as_view(), name="my-entries"),  # Мои записи
    path("create/", EntryCreateView.as_view(), name="entry-create"),  # Создание новой записи
    path("<int:pk>/", EntryDetailView.as_view(), name="entry-detail"),  # Детали записи
    path("<int:pk>/update/", EntryUpdateView.as_view(), name="entry-update"),  # Обновление записи
    path("<int:pk>/delete/", EntryDeleteView.as_view(), name="entry-delete"),  # Удаление записи
    path("paid/", PaidEntriesListView.as_view(), name="paid-entries"),  # Платные записи
    path("subscribe/", subscribe_view, name="subscribe"),  # Подписка
    path("subscription-info/", subscription_info, name="subscription-info"),  # Информация о подписке
    path("users/logout/", custom_logout, name="logout"),
]

urlpatterns = [
    path("api/", include(router.urls)),  # API маршруты: /api/entries/
    path("", include(html_urlpatterns)),  # HTML маршруты: /, /free/, /create/, etc.
]
