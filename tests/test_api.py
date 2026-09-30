"""Тест уровня API."""

import pytest

from web.models import Task


@pytest.mark.django_db
def test_bad_field_value_returns_422(client):
    response = client.post(
        "/api/tasks", data={"name": "bad", "params": {"mode": "wrong-mode"}}, content_type="application/json"
    )
    assert response.status_code == 422


@pytest.mark.django_db
def test_result_for_missing_task_returns_404(client):
    """Задачи с таким id вообще нет — не 'результат ещё не готов',
    а прямо 'задача не найдена'. Ждать нечего, номер неверный."""
    response = client.get("/api/tasks/999/result")
    assert response.status_code == 404


@pytest.mark.django_db
def test_result_for_unfinished_task_returns_409(client):
    """Задача существует (создана прямо в базе, без реального расчёта —
    нам не нужен фон, чтобы проверить именно код ответа), но ещё не done.
    Раньше это тоже был 404 с тем же текстом, что и для несуществующей
    задачи — клиент не мог отличить 'подождите' от 'вы ошиблись номером'."""
    task = Task.objects.create(kind="solve", status=Task.Status.QUEUED)
    response = client.get(f"/api/tasks/{task.id}/result")
    assert response.status_code == 409
