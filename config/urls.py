from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path("admin/", admin.site.urls),
    # API маршруты
    path("api/users/", include("users.urls")),  # /api/users/api/ и /api/users/register/ и т.д.
    path("api/entries/", include("entries.urls")),  # /api/entries/api/ и /api/entries/ и т.д.
    # HTML маршруты
    path("entries/", include("entries.urls")),  # HTML маршруты записей: /entries/, /entries/free/, etc.
    path("users/", include("users.urls")),  # HTML маршруты пользователей: /users/register/, /users/login/, etc.
    # Перенаправление корня на список записей
    path("", RedirectView.as_view(url="/entries/", permanent=False)),
    path("users/logout/", LogoutView.as_view(next_page="/"), name="logout"),
]
