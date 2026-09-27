"""Django Ninja API. Принимает name и
params, зовёт web/services.py. Вся валидация — через core.schemas.SudokuParams,
подключённую прямо в схему запроса: 422 генерируется автоматически."""

from django.http import Http404
from ninja import NinjaAPI, Schema

from core.schemas import SudokuParams
from web import services

api = NinjaAPI(title="Sudoku Service API")


class TaskIn(Schema):
    name: str
    params: SudokuParams


@api.post("/tasks", response={202: dict})
def create_task(request, payload: TaskIn):
    task = services.create_task(payload.name, payload.params)
    return 202, {"id": task.id}


@api.get("/tasks/{task_id}")
def task_status(request, task_id: int):
    task = services.get_task(task_id)
    if task is None:
        raise Http404("Задача не найдена")
    return {
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "error": task.error,
    }


@api.get("/tasks/{task_id}/result")
def task_result(request, task_id: int):
    task = services.get_task(task_id)
    if task is None or task.status != "done":
        raise Http404("Результат ещё не готов")
    return services.get_result(task)
