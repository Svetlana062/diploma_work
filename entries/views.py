from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Entry
from .serializers import EntrySerializer


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
            if getattr(self.request.user, 'is_subscribed', False):
                return queryset  # Показываем все записи
            else:
                return queryset.filter(is_paid=False)  # Только бесплатные
        else:
            return queryset.filter(is_paid=False)  # Только бесплатные для анонимов


    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_entries(self, request):
        entries = Entry.objects.filter(author=request.user)
        serializer = self.get_serializer(entries, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def free_entries(self, request):
        entries = Entry.objects.filter(is_paid=False)
        serializer = self.get_serializer(entries, many=True)
        return Response(serializer.data)
