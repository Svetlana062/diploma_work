from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, Payment


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователей."""

    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ["phone", "email", "username", "password1", "password2"]

    def validate(self, data):
        """Валидация полей при регистрации."""
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError("Пароли не совпадают")
        return data

    def create(self, validated_data):
        """Создание нового пользователя."""
        # Извлекаем пароли
        password = validated_data.pop("password1")
        validated_data.pop("password2")  # Удаляем password2

        # Создаем пользователя
        user = CustomUser.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            phone=validated_data["phone"],
            password=password,  # Пароль передается отдельным аргументом
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """Сериализатор для логина пользователей."""

    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Валидация полей при логине."""
        phone = data.get("phone")
        password = data.get("password")

        if phone and password:
            user = authenticate(phone=phone, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            data["user"] = user
            return data
        raise serializers.ValidationError("Phone and password are required")


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения профиля пользователя."""

    class Meta:
        model = CustomUser
        fields = ["id", "phone", "email", "username", "is_paid"]


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор для платежей."""

    class Meta:
        model = Payment
        fields = ["id", "amount", "status", "created_at"]


class JWTAuthSerializer(serializers.Serializer):
    """Сериализатор для аутентификации с использованием JWT."""

    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        phone = data.get("phone")
        password = data.get("password")

        if phone and password:
            user = authenticate(phone=phone, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials")

            # Генерируем JWT токены
            refresh = RefreshToken.for_user(user)

            data["refresh"] = str(refresh)
            data["access"] = str(refresh.access_token)
            data["user"] = user
            return data

        raise serializers.ValidationError("Phone and password are required")
