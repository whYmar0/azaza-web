from django.urls import path

from web import views
from web.api import api

urlpatterns = [
    path("", views.index, name="index"),
    path("api/", api.urls),
]
