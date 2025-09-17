from rest_framework.permissions import BasePermission


class IsModerator(BasePermission):
    """Класс для определения, является ли пользователь модератором."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.groups.filter(name="Модераторы").exists()
        )


class IsOwnerOrReadOnly(BasePermission):
    """Разрешение, позволяющее пользователю редактировать только свои
    собственные данные. Просмотр разрешен всем."""

    def has_object_permission(self, request, view, obj):
        # Разрешить безопасные методы (GET, HEAD, OPTIONS) всем
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        # Разрешить изменение только владельцу объекта
        return obj.id == request.user.id
