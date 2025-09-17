from django.core.management import BaseCommand
from users.models import CustomUser


class Command(BaseCommand):
    """Команда для создания суперпользователя с номером телефона и паролем."""

    def handle(self, *args, **kwargs):
        phone_number = "89000000000"
        email = "admin@example.com"
        password = "123qwe"

        if not CustomUser.objects.filter(phone=phone_number).exists():
            user = CustomUser(phone=phone_number, email=email, is_active=True, is_staff=True, is_superuser=True)
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS("Суперпользователь создан."))
        else:
            self.stdout.write(self.style.WARNING("Пользователь с этим номером уже существует."))
