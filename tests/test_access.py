"""Проверка изоляции задач: пользователь видит только свои задачи.

Задача ищется по номеру И владельцу; чужая → 404, как несуществующая
(docs/ADR-003.md). Задачи создаются прямо в базе, без расчёта."""

import pytest
from django.contrib.auth.models import User

from web.models import PuzzleResult, Task

PUZZLE = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
SOLUTION = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"


@pytest.fixture
def two_users_and_task(db):
    user1 = User.objects.create_user("user1", password="a-12345")
    user2 = User.objects.create_user("user2", password="b-12345")
    task = Task.objects.create(
        name="A", kind="solve", params={}, status="done", owner=user1
    )
    PuzzleResult.objects.create(
        task=task, puzzle=PUZZLE, solution=SOLUTION, clues=30, elapsed_ms=3.5
    )
    return user1, user2, task


def test_other_user_gets_404(client, two_users_and_task):
    _, user2, task = two_users_and_task

    client.force_login(user2)
    assert client.get(f"/api/tasks/{task.pk}").status_code == 404
    assert client.get(f"/api/tasks/{task.pk}/result").status_code == 404
    assert client.get(f"/tasks/{task.pk}/").status_code == 404


def test_owner_still_sees_own_task(client, two_users_and_task):
    """Контрольная проверка: без неё test_other_user_gets_404 прошёл бы и
    тогда, когда сломано вообще всё и любой запрос отвечает 404. Владелец
    по тем же трём адресам получает 200 и своё решение."""
    user1, _, task = two_users_and_task

    client.force_login(user1)
    assert client.get(f"/api/tasks/{task.pk}").status_code == 200
    result = client.get(f"/api/tasks/{task.pk}/result")
    assert result.status_code == 200
    assert result.json()["solution"] == SOLUTION
    page = client.get(f"/tasks/{task.pk}/")
    assert page.status_code == 200
    assert SOLUTION in page.content.decode()


def test_anonymous_gets_401_in_api(client, two_users_and_task):
    """Аноним в API: 401 «кто вы?» — до вопроса «ваша ли задача» не доходит."""
    _, _, task = two_users_and_task
    assert client.get(f"/api/tasks/{task.pk}").status_code == 401
    assert client.get(f"/api/tasks/{task.pk}/result").status_code == 401


def test_task_list_shows_only_own_tasks(client, two_users_and_task):
    """Список «Мои задачи» на главной: filter(owner=user). Без фильтра
    чужие задачи было бы видно, даже не перебирая номера."""
    user1, user2, task = two_users_and_task
    Task.objects.create(name="задача Пользователя 2", kind="generate", owner=user2)

    client.force_login(user2)
    html = client.get("/").content.decode()
    assert "задача Пользователя 2" in html
    assert f'href="/tasks/{task.pk}/"' not in html

    client.force_login(user1)
    assert f'href="/tasks/{task.pk}/"' in client.get("/").content.decode()
