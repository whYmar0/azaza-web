"""Путь через сайт (чекпоинт 21.09): форма -> расчёт -> страница результата.

transaction=True — расчёт идёт в отдельном потоке (web/services.py), и поток
должен видеть закоммиченную задачу; в обычном django_db-тесте всё внутри
одной незакоммиченной транзакции, поток бы её не увидел."""

import time

import pytest

from web.models import Task

PUZZLE = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
SOLUTION = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"


def _wait_until_finished(task_id: int, timeout: float = 10.0) -> Task:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        task = Task.objects.get(id=task_id)
        if task.status in (Task.Status.DONE, Task.Status.ERROR):
            return task
        time.sleep(0.05)
    raise AssertionError("Задача зависла в queued/running")


@pytest.mark.django_db(transaction=True)
def test_form_solve_redirects_and_shows_known_solution(client):
    response = client.post(
        "/", {"mode": "solve", "grid": PUZZLE, "difficulty": "medium", "seed": ""}
    )
    assert response.status_code == 302
    task_id = int(response.url.strip("/").split("/")[-1])

    task = _wait_until_finished(task_id)
    assert task.status == Task.Status.DONE
    assert task.result.solution == SOLUTION
    assert task.result.elapsed_ms > 0  # настоящее время, не заглушка 0.0

    page = client.get(response.url)
    assert SOLUTION in page.content.decode()


@pytest.mark.django_db(transaction=True)
def test_form_generate_produces_result(client):
    response = client.post(
        "/", {"mode": "generate", "grid": "", "difficulty": "easy", "seed": "42"}
    )
    assert response.status_code == 302
    task = _wait_until_finished(int(response.url.strip("/").split("/")[-1]))
    assert task.status == Task.Status.DONE
    assert task.result.elapsed_ms > 0


@pytest.mark.django_db(transaction=True)
def test_form_rejects_duplicate_digit_without_creating_task(client):
    bad = "55" + PUZZLE[2:]
    response = client.post(
        "/", {"mode": "solve", "grid": bad, "difficulty": "medium", "seed": ""}
    )
    assert response.status_code == 200  # форма показана снова, не 500
    assert "Повтор цифры 5" in response.content.decode()
    assert Task.objects.count() == 0
