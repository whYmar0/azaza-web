"""Страница: форма принимает данные, запускает расчёт через web/services.py
и показывает результат. Сама view не считает и не валидирует правила
судоку — только собирает вход в SudokuParams (это делает core/schemas.py)
и передаёт его в services.create_task."""

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from pydantic import ValidationError

from core.schemas import SudokuParams
from web import services
from web.forms import SudokuTaskForm
from web.models import Task

PROJECT_NAME = "Sudoku Service"

# Примеры для кнопок на форме — те же эталоны, что в тестах и README.
EXAMPLES = [
    ("Классическая", "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"),
    ("Инкала, 2012", "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."),
    ("Без решения", ".....5.8....6.1.43..........1.5........1.6...3.......553.....61........4........."),
]


def grid_cells(puzzle: str | None, solution: str | None = None) -> list[dict]:
    """81 клетка для шаблона: цифра, подсказка это или найденная, и где
    проходят жирные границы блоков 3×3. Только раскладка для показа —
    правила судоку здесь не проверяются."""
    puzzle = puzzle or "." * 81
    cells = []
    for i in range(81):
        row, col = divmod(i, 9)
        given = puzzle[i] != "."
        digit = puzzle[i] if given else (solution[i] if solution else "")
        cells.append({
            "digit": digit,
            "given": given,
            "solved": not given and bool(digit),
            "right_edge": col in (2, 5),
            "bottom_edge": row in (2, 5),
            "order": row + col,  # для волны появления найденных цифр
        })
    return cells


@login_required
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
                # Ошибку — под своё поле (seed — под seed);
                # ошибки сочетания полей (model_validator) — под grid.
                for err in exc.errors():
                    field = err["loc"][0] if err["loc"] else "grid"
                    if field not in form.fields:
                        field = "grid"
                    form.add_error(field, err["msg"].removeprefix("Value error, "))
            else:
                task = services.create_task(
                    request.user, name=f"{data['mode']} с сайта", params=params
                )
                return redirect("task_detail", task_id=task.id)
    else:
        form = SudokuTaskForm()
    entered = form["grid"].value() or ""
    return render(request, "web/index.html", {
        "project_name": PROJECT_NAME,
        "form": form,
        "cells": grid_cells(entered if len(entered) == 81 else None),
        "examples": EXAMPLES,
        "recent_tasks": services.list_tasks(request.user),
    })


@login_required
def task_detail(request, task_id: int):
    """Страница результата: статус задачи, а когда готово — решение.
    Ошибка (например, сетка без единственного решения) показывается
    честно, а не бесконечным "выполняется".

    Задача ищется по номеру И владельцу через services.get_task,
    чтобы правило «только свои» жило в одном месте. Чужая задача → None → 404."""
    task = services.get_task(request.user, task_id)
    if task is None:
        raise Http404("задача не найдена")
    context = {"project_name": PROJECT_NAME, "task": task}
    if task.status == Task.Status.DONE:
        result = services.get_result(task)
        context["result"] = result
        context["cells"] = grid_cells(result["puzzle"], result["solution"])
    else:
        # Пока считается или если ошибка — показываем то, что прислали.
        context["cells"] = grid_cells((task.params or {}).get("grid"))
    context["in_progress"] = task.status in (Task.Status.QUEUED, Task.Status.RUNNING)
    return render(request, "web/task_detail.html", context)
