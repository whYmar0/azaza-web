from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Стандартные страницы Django — /accounts/login/ и /accounts/logout/
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("web.urls")),
]
