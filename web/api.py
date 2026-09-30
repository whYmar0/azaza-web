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


@api.get("/tasks/{task_id}/result", response={200: dict, 409: dict})
def task_result(request, task_id: int):
    """Два разных случая — два разных кода (правило курса: коды ответа
    HTTP — часть договора с клиентом).

    Раньше и "задачи нет", и "задача ещё считается" отвечали одним и тем
    же 404 с текстом "Результат ещё не готов" — клиент не мог понять,
    ждать ему или запрос был ошибочным. Теперь:
    - задачи с таким id вообще нет -> 404 "задача не найдена" (ждать
      бессмысленно, номер неверный);
    - задача есть, но ещё не done -> 409 с текущим статусом (можно
      повторить запрос позже);
    - задача готова -> 200 и результат.
    """
    task = services.get_task(task_id)
    if task is None:
        raise Http404("задача не найдена")
    if task.status != "done":
        return 409, {"detail": f"статус: {task.status}"}
    return 200, services.get_result(task)
