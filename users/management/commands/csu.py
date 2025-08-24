from django.core.management import BaseCommand
from users.models import CustomUser


class Command(BaseCommand):
    """Команда для создания суперпользователя с предустановленными
    данными (email, пароль, активность, статус администратора)."""

    def handle(self, *args, **options):
        if not CustomUser.objects.filter(email="admin@example.com").exists():
            user = CustomUser.objects.create(email="admin@example.com")
            user.set_password("123qwe")
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS("Суперпользователь создан."))
        else:
            self.stdout.write(self.style.WARNING("Суперпользователь уже существует."))
