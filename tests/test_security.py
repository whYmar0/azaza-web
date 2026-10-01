"""Проверка безопасности: вход, аутентификация, CSRF, XSS, конфигурация.
См. также docs/security_review.md."""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from django.test import Client

from web.models import Task

NORVIG_NO_SOLUTION = (
    ".....5.8." "...6.1.43" "........." ".1.5....." "...1.6..."
    "3.......5" "53.....61" "........4" "........."
)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# --- 4. Границы входа -------------------------------------------------------

@pytest.mark.django_db
def test_solve_without_grid_is_422_and_no_task(auth_client):
    """mode=solve без grid — 422, задача не создаётся."""
    response = auth_client.post(
        "/api/tasks", data={"name": "x", "params": {"mode": "solve"}},
        content_type="application/json",
    )
    assert response.status_code == 422
    assert "grid" in response.content.decode()
    assert Task.objects.count() == 0


@pytest.mark.django_db
def test_form_solve_without_grid_shows_error_and_no_task(auth_client):
    response = auth_client.post("/", {"mode": "solve", "grid": "", "difficulty": "medium"})
    assert response.status_code == 200
    assert "нужна сетка" in response.content.decode()
    assert Task.objects.count() == 0


@pytest.mark.django_db
def test_long_name_is_422(auth_client):
    """name длиннее 100 символов — 422, задача не создаётся."""
    response = auth_client.post(
        "/api/tasks",
        data={"name": "a" * 1000, "params": {"mode": "generate", "difficulty": "easy"}},
        content_type="application/json",
    )
    assert response.status_code == 422
    assert "name" in response.content.decode()
    assert Task.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_grid_without_solution_ends_with_error_not_hang(auth_client):
    """Сетка без решения: перебор останавливается по пределу шагов, задача переходит в error."""
    response = auth_client.post(
        "/api/tasks",
        data={"name": "norvig", "params": {"mode": "solve", "grid": NORVIG_NO_SOLUTION}},
        content_type="application/json",
    )
    task_id = response.json()["id"]
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        task = Task.objects.get(id=task_id)
        if task.status in (Task.Status.DONE, Task.Status.ERROR):
            break
        time.sleep(0.1)
    assert task.status == Task.Status.ERROR
    assert "предел перебора" in task.error


# --- 6. XSS -----------------------------------------------------------------

@pytest.mark.django_db
def test_task_name_is_shown_as_text_not_html(auth_client, user):
    """Имя задачи приходит от пользователя (API) и выводится на странице.
    Django экранирует {{ }} сам; |safe в шаблонах нет — тег виден как текст."""
    task = Task.objects.create(
        name="<b>жирный</b><script>alert(1)</script>", kind="solve", owner=user
    )
    html = auth_client.get(f"/tasks/{task.id}/").content.decode()
    assert "&lt;b&gt;жирный&lt;/b&gt;" in html
    assert "<script>alert(1)</script>" not in html


# --- 7. CSRF ----------------------------------------------------------------

@pytest.mark.django_db
def test_post_without_csrf_token_is_rejected(user):
    """Чужой сайт отправляет форму/запрос от имени вошедшего пользователя:
    cookie есть, CSRF-токена нет -> 403, задача не создана. Обычный
    тестовый клиент CSRF не проверяет — здесь проверку включаем явно."""
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    api = client.post(
        "/api/tasks",
        data={"name": "x", "params": {"mode": "generate", "difficulty": "easy"}},
        content_type="application/json",
    )
    form = client.post("/", {"mode": "generate", "difficulty": "easy"})
    assert api.status_code == 403
    assert form.status_code == 403
    assert Task.objects.count() == 0


# --- 1–2. DEBUG и SECRET_KEY ------------------------------------------------

def _manage_check(env_overrides: dict[str, str]) -> subprocess.CompletedProcess:
    env = {**os.environ, **env_overrides}
    return subprocess.run(
        [sys.executable, "manage.py", "check"],
        cwd=PROJECT_ROOT, env=env, capture_output=True, text=True, check=False,
    )


def test_server_refuses_to_start_without_secret_key():
    """DEBUG по умолчанию выключен; без ключа сервер не стартует.
    Пустые значения перекрывают .env (load_dotenv не трогает уже заданные)."""
    result = _manage_check({"DJANGO_DEBUG": "0", "DJANGO_SECRET_KEY": ""})
    assert result.returncode != 0
    assert "задайте DJANGO_SECRET_KEY" in result.stderr


def test_dev_mode_starts_without_secret_key():
    result = _manage_check({"DJANGO_DEBUG": "1", "DJANGO_SECRET_KEY": ""})
    assert result.returncode == 0, result.stderr
