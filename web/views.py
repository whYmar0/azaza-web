"""Страница: форма принимает данные, запускает расчёт через web/services.py
и показывает результат. Сама view не считает и не валидирует правила
судоку — только собирает вход в SudokuParams (это делает core/schemas.py)
и передаёт его в services.create_task."""

from django.shortcuts import get_object_or_404, redirect, render
from pydantic import ValidationError

from core.schemas import SudokuParams
from web import services
from web.forms import SudokuTaskForm
from web.models import Task

PROJECT_NAME = "Sudoku Service"


def index(request):
    if request.method == "POST":
        form = SudokuTaskForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                params = SudokuParams(
                    mode=data["mode"],
                    grid=data["grid"] or None,
                    difficulty=data["difficulty"],
                    seed=data["seed"],
                )
            except ValidationError as exc:
                # Django-форма проверяет только длину поля; проверку правил
                # судоку (дубли в строке/столбце/блоке) делает core/schemas.py
                # — её ошибку показываем тем же способом, что и обычную
                # ошибку формы, чтобы пользователь увидел причину на странице.
                # exc.errors() даёт короткий текст без служебных деталей pydantic.
                message = "; ".join(
                    err["msg"].removeprefix("Value error, ") for err in exc.errors()
                )
                form.add_error("grid", message)
            else:
                task = services.create_task(
                    name=f"{data['mode']} с сайта", params=params
                )
                return redirect("task_detail", task_id=task.id)
    else:
        form = SudokuTaskForm()
    return render(request, "web/index.html", {"project_name": PROJECT_NAME, "form": form})


def task_detail(request, task_id: int):
    """Страница результата: статус задачи, а когда готово — решение.
    Ошибка (например, сетка без единственного решения) показывается
    честно, а не бесконечным "выполняется"."""
    task = get_object_or_404(Task, id=task_id)
    context = {"project_name": PROJECT_NAME, "task": task}
    if task.status == Task.Status.DONE:
        context["result"] = services.get_result(task)
    return render(request, "web/task_detail.html", context)
