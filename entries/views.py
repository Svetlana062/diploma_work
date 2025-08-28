from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import logout
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Entry
from .serializers import EntrySerializer
from django.contrib import messages
from django.shortcuts import redirect, render

from .utils import user_has_subscription


class EntryViewSet(viewsets.ModelViewSet):
    """ViewSet для модели Entry, обеспечивающий стандартные CRUD-операции."""
    model = Entry
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Показываем все бесплатные записи. Платные только если пользователь
        аутентифицирован и имеет подписку."""
        queryset = Entry.objects.all()

        if self.request.user.is_authenticated:
            if user_has_subscription(self.request.user):
                return queryset  # Показываем все записи подписчику
            else:
                # Показываем бесплатные + свои платные записи
                return queryset.filter(Q(is_paid=False) | Q(author=self.request.user))
        else:
            return queryset.filter(is_paid=False)  # Только бесплатные для анонимов

    def perform_create(self, serializer):
        """Устанавливает текущего пользователя как автора новой записи."""
        serializer.save(author=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def my_entries(self, request):
        """Возвращает список записей текущего пользователя."""
        entries = Entry.objects.filter(author=request.user)
        serializer = self.get_serializer(entries, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def free_entries(self, request):
        """Возвращает список всех бесплатных записей."""
        entries = Entry.objects.filter(is_paid=False)
        serializer = self.get_serializer(entries, many=True)
        return Response(serializer.data)


class EntryListView(ListView):
    """HTML-страница со списком всех записей."""
    model = Entry
    template_name = "entries/entry_list.html"
    context_object_name = "entries"
    paginate_by = 10

    def get_queryset(self):
        """Возвращает queryset в зависимости от статуса подписки пользователя."""
        queryset = Entry.objects.all()

        if self.request.user.is_authenticated:
            # Проверяем подписку
            if hasattr(self.request.user, "is_paid") and self.request.user.is_paid:
                return queryset  # Показываем все записи подписчику
            else:
                # Показываем бесплатные + свои платные записи
                return queryset.filter(Q(is_paid=False) | Q(author=self.request.user))
        else:
            return queryset.filter(is_paid=False)

    def get_context_data(self, **kwargs):
        """Добавляет заголовок страницы в контекст."""
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Все записи"
        return context


class FreeEntriesListView(ListView):
    """Страница со списком только бесплатных записей."""
    model = Entry
    template_name = "entries/entry_list.html"
    context_object_name = "entries"
    paginate_by = 10

    def get_queryset(self):
        """Возвращает только бесплатные записи."""
        # Только бесплатные записи для всех пользователей
        return Entry.objects.filter(is_paid=False)

    def get_context_data(self, **kwargs):
        """Добавляет заголовок страницы в контекст."""
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Бесплатные записи"
        return context


class EntryDetailView(DetailView):
    """Страница с подробным просмотром одной записи."""
    model = Entry
    template_name = "entries/entry_detail.html"
    context_object_name = "entry"

    def dispatch(self, request, *args, **kwargs):
        """Проверяет права доступа к платной записи перед отображением."""
        entry = self.get_object()
        user = request.user

        # Разрешаем доступ если: запись бесплатная, пользователь - автор записи,
        # пользователь имеет подписку
        if entry.is_paid and not (user == entry.author or (hasattr(user, "is_paid") and user.is_paid)):

            if user.is_authenticated:
                messages.warning(request, "Для просмотра этой записи нужна подписка")
                return redirect("subscription-info")
            else:
                messages.warning(request, "Войдите в систему для доступа к платному контенту")
                return redirect("login")

        return super().dispatch(request, *args, **kwargs)


class EntryCreateView(LoginRequiredMixin, CreateView):
    """Создает новую запись. Требует входа в систему."""
    model = Entry
    template_name = "entries/entry_form.html"
    fields = ["title", "content", "is_paid"]
    success_url = reverse_lazy("entry-list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        # Добавляем сообщение об успешном создании
        messages.success(self.request, "Запись успешно создана!")
        return response


class EntryUpdateView(LoginRequiredMixin, UpdateView):
    """Ограничивает редактирование только записями текущего пользователя."""
    model = Entry
    template_name = "entries/entry_form.html"
    fields = ["title", "content", "is_paid"]
    success_url = reverse_lazy("entry-list")

    def get_queryset(self):
        return Entry.objects.filter(author=self.request.user)

    def form_valid(self, form):
        """Обрабатывает успешную отправку формы."""
        response = super().form_valid(form)
        messages.success(self.request, "Запись успешно обновлена!")
        return response


class EntryDeleteView(LoginRequiredMixin, DeleteView):
    """Удаляет запись. Требует входа в систему."""
    model = Entry
    template_name = "entries/entry_confirm_delete.html"
    success_url = reverse_lazy("entry-list")

    def get_queryset(self):
        """Ограничивает удаление только записями текущего пользователя."""
        return Entry.objects.filter(author=self.request.user)

    def delete(self, request, *args, **kwargs):
        """Обрабатывает удаление и показывает сообщение."""
        messages.success(request, "Запись успешно удалена!")
        return super().delete(request, *args, **kwargs)


class MyEntriesListView(LoginRequiredMixin, ListView):
    """Страница со списком собственных записей пользователя."""
    model = Entry
    template_name = "entries/entry_list.html"  # Используем шаблон для списка
    context_object_name = "entries"
    paginate_by = 10

    def get_queryset(self):
        """Возвращает все записи текущего пользователя."""
        return Entry.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        """Добавляет заголовок страницы в контекст."""
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Мои записи"
        return context


class PaidEntriesListView(ListView):
    """Страница со списком платных записей."""

    model = Entry
    template_name = "entries/entry_list.html"
    context_object_name = "entries"
    paginate_by = 10

    def get_queryset(self):
        """Возвращает только платные записи."""
        # Только платные записи
        return Entry.objects.filter(is_paid=True)

    def get_context_data(self, **kwargs):
        """Добавляет заголовок страницы в контекст."""
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Платные записи"
        return context


@login_required
def subscribe_view(request):
    """Представление для оформления подписки."""
    if request.method == "POST":
        # Здесь будет логика обработки платежа
        # Временно просто устанавливаем флаг подписки
        if not getattr(request.user, "is_subscribed", False):
            request.user.is_subscribed = True
            request.user.save()
            messages.success(request, "Подписка успешно оформлена! Теперь у вас есть доступ ко всем платным записям.")
        else:
            messages.warning(request, "У вас уже активная подписка.")

        return redirect("entry-list")

    # GET запрос - показываем страницу с информацией о подписке
    return render(request, "entries/subscription_info.html")


def subscription_info(request):
    """Страница с информацией о подписке"""
    return render(request, "entries/subscription_info.html")


@require_POST
@login_required
def custom_logout(request):
    logout(request)
    return redirect("entry-list")
