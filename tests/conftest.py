"""Общие фикстуры для тестов уровня сайта и API.

Весь сайт и весь API защищены аутентификацией. `auth_client` —
тестовый клиент Django с force_login (без формы входа)."""

import pytest
from django.contrib.auth.models import User


@pytest.fixture(autouse=True)
def _no_threads(settings):
    """Расчёт в тестах идёт синхронно (RUN_IN_THREAD=False): тестовая база
    SQLite одна на тест и фоновый поток, поток иногда получал
    «database table is locked» и умирал, задача оставалась queued."""
    settings.RUN_IN_THREAD = False


@pytest.fixture
def user(db):
    return User.objects.create_user("user1", password="a-12345")


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client
