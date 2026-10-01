"""Минимальные настройки стартера. Секреты — только через .env."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# По умолчанию безопасно; разработку включают руками (.env: DJANGO_DEBUG=1).
DEBUG = os.environ.get("DJANGO_DEBUG", "0").strip().lower() in ("1", "true")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "").strip()
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-key"  # только на ноутбуке, где DEBUG включён руками
    else:
        # На сервере без ключа — не стартовать: ключ из кода (он же в GitHub)
        # позволил бы подделать cookie входа любого пользователя.
        raise RuntimeError(
            "задайте DJANGO_SECRET_KEY (или DJANGO_DEBUG=1 для разработки) — см. .env.example"
        )
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "web",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sudoku_service.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "sudoku_service.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_TZ = True

STATIC_URL = "static/"

# Не вошёл — на страницу входа; вошёл — на главную.
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# Расчёт в фоновом потоке (ADR-002). Тесты выключают это
# (tests/conftest.py) и считают сразу — без гонки за тестовую базу.
RUN_IN_THREAD = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
