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


class EntryViewSet(viewsets.ModelViewSet):
    model = Entry
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Показываем все бесплатные записи. Платные только если пользователь
        аутентифицирован и имеет подписку."""
        queryset = Entry.objects.all()

        if self.request.user.is_authenticated:
            if getattr(self.request.user, "is_subscribed", False):
                return queryset  # Показываем все записи
            else:
                return queryset.filter(is_paid=False)  # Только бесплатные
        else:
            return queryset.filter(is_paid=False)  # Только бесплатные для анонимов

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def my_entries(self, request):
        entries = Entry.objects.filter(author=request.user)
        serializer = self.get_serializer(entries, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def free_entries(self, request):
        entries = Entry.objects.filter(is_paid=False)
        serializer = self.get_serializer(entries, many=True)
        return Response(serializer.data)


# HTML представления
class EntryListView(ListView):
    model = Entry
    template_name = "entries/entry_list.html"
    context_object_name = "entries"
    paginate_by = 10

    def get_queryset(self):
        queryset = Entry.objects.all()

        # Если пользователь авторизован
        if self.request.user.is_authenticated:
            # Если пользователь подписан - показываем все записи
            if hasattr(self.request.user, "is_subscribed") and self.request.user.is_subscribed:
                return queryset
            # Если не подписан - показываем бесплатные + свои платные
            else:
                return queryset.filter(Q(is_paid=False) | Q(author=self.request.user))
        # Если не авторизован - только бесплатные
        else:
            return queryset.filter(is_paid=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Все записи"
        return context


class FreeEntriesListView(ListView):
    model = Entry
    template_name = "entries/entry_list.html"
    context_object_name = "entries"
    paginate_by = 10

    def get_queryset(self):
        # Только бесплатные записи для всех пользователей
        return Entry.objects.filter(is_paid=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Бесплатные записи"
        return context


class EntryDetailView(DetailView):
    model = Entry
    template_name = "entries/entry_detail.html"
    context_object_name = "entry"

    def dispatch(self, request, *args, **kwargs):
        entry = self.get_object()
        user = request.user

        if entry.is_paid and not (user == entry.author or getattr(user, "is_subscribed", False)):
            if user.is_authenticated:
                messages.warning(request, "Для просмотра этой записи нужна подписка")
                return redirect("subscription-info")  # Перенаправляем на страницу информации о подписке
            else:
                messages.warning(request, "Войдите в систему для доступа к платному контенту")
                return redirect("login")

        return super().dispatch(request, *args, **kwargs)


class EntryCreateView(LoginRequiredMixin, CreateView):
    model = Entry
    template_name = "entries/entry_form.html"
    fields = ["title", "content", "is_paid"]
    success_url = reverse_lazy("entry-list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class EntryUpdateView(LoginRequiredMixin, UpdateView):
    model = Entry
    template_name = "entries/entry_form.html"
    fields = ["title", "content", "is_paid"]
    success_url = reverse_lazy("entry-list")

    def get_queryset(self):
        return Entry.objects.filter(author=self.request.user)


class EntryDeleteView(LoginRequiredMixin, DeleteView):
    model = Entry
    template_name = "entries/entry_confirm_delete.html"
    success_url = reverse_lazy("entry-list")

    def get_queryset(self):
        return Entry.objects.filter(author=self.request.user)


class MyEntriesListView(LoginRequiredMixin, ListView):
    model = Entry
    template_name = "entries/entry_list.html"  # Используем шаблон для списка
    context_object_name = "entries"
    paginate_by = 10

    def get_queryset(self):
        return Entry.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Мои записи"
        return context


class PaidEntriesListView(ListView):
    """Для отображения платных записей."""

    model = Entry
    template_name = "entries/entry_list.html"
    context_object_name = "entries"
    paginate_by = 10

    def get_queryset(self):
        # Только платные записи
        return Entry.objects.filter(is_paid=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Платные записи"
        return context


@login_required
def subscribe_view(request):
    """Представление для оформления подписки"""
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
