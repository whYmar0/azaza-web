from django.urls import path

from web import views
from web.api import api

urlpatterns = [
    path("", views.index, name="index"),
    path("tasks/<int:task_id>/", views.task_detail, name="task_detail"),
    path("api/", api.urls),
]
