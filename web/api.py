"""Django Ninja API. Принимает name и
params, зовёт web/services.py. Вся валидация — через core.schemas.SudokuParams,
подключённую прямо в схему запроса: 422 генерируется автоматически."""

from django.http import Http404
from ninja import Field, NinjaAPI, Schema
from ninja.security import django_auth

from core.schemas import SudokuParams
from web import services

# Весь API — только после входа. django_auth берёт ту же cookie сессии,
# что и сайт; аноним → 401.
api = NinjaAPI(title="Sudoku Service API", auth=django_auth)


class TaskIn(Schema):
    # Длина name ограничена здесь, до базы (SQLite длину не проверяет).
    name: str = Field(max_length=100)
    params: SudokuParams


@api.post("/tasks", response={202: dict})
def create_task(request, payload: TaskIn):
    task = services.create_task(request.user, payload.name, payload.params)
    return 202, {"id": task.id}


@api.get("/tasks/{task_id}")
def task_status(request, task_id: int):
    task = services.get_task(request.user, task_id)
    if task is None:
        raise Http404("Задача не найдена")
    return {
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "error": task.error,
    }


@api.get("/tasks/{task_id}/result", response={200: dict, 409: dict})
def task_result(request, task_id: int):
    """Два разных случая — два разных кода ответа:
    - задачи с таким id нет → 404;
    - задача есть, но ещё не done → 409 с текущим статусом;
    - задача готова → 200 и результат.
    """
    task = services.get_task(request.user, task_id)
    if task is None:
        raise Http404("задача не найдена")
    if task.status != "done":
        return 409, {"detail": f"статус: {task.status}"}
    return 200, services.get_result(task)
