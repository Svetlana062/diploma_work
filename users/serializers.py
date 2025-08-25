from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, Payment


class UserRegistrationSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ["phone", "email", "username", "password1", "password2"]

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError("Пароли не совпадают")
        return data

    def create(self, validated_data):
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
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
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
    class Meta:
        model = CustomUser
        fields = ["id", "phone", "email", "username", "is_paid"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "amount", "status", "created_at"]
