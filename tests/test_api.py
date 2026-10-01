"""Тест уровня API."""

import pytest

from web.models import Task


@pytest.mark.django_db
def test_bad_field_value_returns_422(auth_client):
    response = auth_client.post(
        "/api/tasks", data={"name": "bad", "params": {"mode": "wrong-mode"}}, content_type="application/json"
    )
    assert response.status_code == 422


@pytest.mark.django_db
def test_result_for_missing_task_returns_404(auth_client):
    """Несуществующий id — 404, задача не найдена."""
    response = auth_client.get("/api/tasks/999/result")
    assert response.status_code == 404


@pytest.mark.django_db
def test_result_for_unfinished_task_returns_409(auth_client, user):
    """Задача существует, но ещё не done — ответ 409 с текущим статусом."""
    task = Task.objects.create(kind="solve", status=Task.Status.QUEUED, owner=user)
    response = auth_client.get(f"/api/tasks/{task.id}/result")
    assert response.status_code == 409


@pytest.mark.django_db
def test_anonymous_cannot_create_task_401(client):
    """Аноним не проходит аутентификацию — 401, задача не создаётся."""
    response = client.post(
        "/api/tasks",
        data={"name": "x", "params": {"mode": "generate", "difficulty": "easy"}},
        content_type="application/json",
    )
    assert response.status_code == 401
    assert Task.objects.count() == 0


# --- Тест полного цикла: создание задачи → 202 → результат ---

WIKI_PUZZLE = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
WIKI_SOLUTION = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"


@pytest.mark.django_db
def test_create_task_returns_202_and_id_then_result(auth_client):
    """POST /api/tasks → 202 + id; по id задача done, решение совпадает
    с опубликованным ответом. Расчёт в тестах синхронный (conftest.py)."""
    r = auth_client.post(
        "/api/tasks",
        data={"name": "t", "params": {"mode": "solve", "grid": WIKI_PUZZLE}},
        content_type="application/json",
    )
    assert r.status_code == 202
    task_id = r.json()["id"]
    assert isinstance(task_id, int)

    status = auth_client.get(f"/api/tasks/{task_id}")
    assert status.json()["status"] == "done"

    r2 = auth_client.get(f"/api/tasks/{task_id}/result")
    assert r2.status_code == 200
    assert r2.json()["solution"] == WIKI_SOLUTION


@pytest.mark.django_db
def test_normal_mode_still_uses_background_thread(auth_client, settings, monkeypatch):
    """При RUN_IN_THREAD=True запрос запускает поток и сразу отвечает 202
    (задача ещё queued). Поток подменён — проверяем запуск, не расчёт."""
    settings.RUN_IN_THREAD = True
    started = []

    class FakeThread:
        def __init__(self, target, args, daemon):
            started.append((target, args, daemon))

        def start(self):
            pass

    from web import services
    monkeypatch.setattr(services.threading, "Thread", FakeThread)

    r = auth_client.post(
        "/api/tasks",
        data={"name": "t", "params": {"mode": "solve", "grid": WIKI_PUZZLE}},
        content_type="application/json",
    )
    assert r.status_code == 202
    assert len(started) == 1
    target, _args, daemon = started[0]
    assert target is services._run and daemon is True
    assert Task.objects.get(id=r.json()["id"]).status == Task.Status.QUEUED
