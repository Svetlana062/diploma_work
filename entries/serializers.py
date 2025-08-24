from rest_framework import serializers
from .models import Entry
from django.conf import settings

class EntrySerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    can_view = serializers.SerializerMethodField()

    class Meta:
        model = Entry
        fields = [
            'id', 'title', 'content', 'author', 'author_name',
            'created_at', 'is_paid', 'price', 'can_view'
        ]
        read_only_fields = ['author']

    def get_can_view(self, obj):
        request = self.context.get('request')
        if not obj.is_paid:
            return True

        if request and request.user.is_authenticated:
            # Проверяем, что у пользователя есть атрибут is_subscribed
            return getattr(request.user, 'is_subscribed', False)

        return False

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data['can_view'] and instance.is_paid:
            data['content'] = 'Для просмотра платного контента необходима подписка'
        return data

    def validate(self, attrs):
        if attrs.get('is_paid') and attrs.get('price') is None:
            raise serializers.ValidationError("Цена должна быть указана для платных записей.")
        return attrs