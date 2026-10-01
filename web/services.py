"""Единственная точка входа для views/API в core/. Вся бизнес-логика тут —
views и api.py её не содержат, только вызывают эти функции.

Фон реализован потоком (threading), а статус хранится прямо в поле
Task.status — отдельного in-memory хранилища задач не нужно (см. ADR-002).
"""

import threading
import time

from django.conf import settings

from core.generator import generate
from core.schemas import SudokuParams
from core.solver import MAX_STEPS, TOO_COMPLEX, solve
from web.models import PuzzleResult, Task


def create_task(user, name: str, params: SudokuParams) -> Task:
    """Создать задачу от имени пользователя; сразу записывает владельца."""
    task = Task.objects.create(
        name=name,
        kind=params.mode,
        status=Task.Status.QUEUED,
        params=params.model_dump(),
        owner=user,
    )
    # Обычно — фоновый поток. В тестах расчёт идёт синхронно (RUN_IN_THREAD=False):
    # тестовая база SQLite одна на тест и поток, и поток иногда получал
    # «database table is locked» и умирал, задача оставалась queued.
    if getattr(settings, "RUN_IN_THREAD", True):
        threading.Thread(target=_run, args=(task.id, params), daemon=True).start()
    else:
        _run(task.id, params)  # синхронно (для тестов)
    return task


def _run(task_id: int, params: SudokuParams) -> None:
    task = Task.objects.get(id=task_id)
    task.status = Task.Status.RUNNING
    task.save(update_fields=["status", "updated_at"])

    try:
        if params.mode == "solve":
            _run_solve(task, params)
        else:
            _run_generate(task, params)
    except Exception as exc:  # noqa: BLE001 — ошибку показываем через статус, не роняем поток
        task.status = Task.Status.ERROR
        task.error = str(exc)
        task.save(update_fields=["status", "error", "updated_at"])


def _run_solve(task: Task, params: SudokuParams) -> None:
    # Вторая линия защиты: схема отсекает это раньше (422 до создания задачи).
    if not params.grid:
        raise ValueError("Для mode=solve нужна сетка (grid)")

    start = time.perf_counter()
    result = solve(params.grid)
    elapsed_ms = (time.perf_counter() - start) * 1000

    if result == TOO_COMPLEX:
        task.status = Task.Status.ERROR
        task.error = (
            f"Превышен предел перебора ({MAX_STEPS} шагов, {elapsed_ms / 1000:.1f} с): "
            "сетка слишком сложная или не имеет решения"
        )
        task.save(update_fields=["status", "error", "updated_at"])
        return

    if result in ("multiple", "no solution"):
        task.status = Task.Status.ERROR
        task.error = f"Сетка не имеет единственного решения: {result}"
        task.save(update_fields=["status", "error", "updated_at"])
        return

    PuzzleResult.objects.create(
        task=task,
        puzzle=params.grid,
        solution=result,
        clues=sum(1 for c in params.grid if c != "."),
        elapsed_ms=elapsed_ms,
    )
    task.status = Task.Status.DONE
    task.save(update_fields=["status", "updated_at"])


def _run_generate(task: Task, params: SudokuParams) -> None:
    start = time.perf_counter()
    puzzle, solution = generate(difficulty=params.difficulty, seed=params.seed)
    elapsed_ms = (time.perf_counter() - start) * 1000

    PuzzleResult.objects.create(
        task=task,
        puzzle=puzzle,
        solution=solution,
        clues=sum(1 for c in puzzle if c != "."),
        elapsed_ms=elapsed_ms,
    )
    task.status = Task.Status.DONE
    task.save(update_fields=["status", "updated_at"])


def get_task(user, task_id: int) -> Task | None:
    """Ищем по номеру И владельцу. Единственное место правила «только
    свои» — его вызывают и страница (views.task_detail), и API.
    Чужая задача -> None -> вызывающий отвечает 404, ровно как на
    несуществующий номер (см. docs/ADR-003.md: почему 404, а не 403)."""
    return Task.objects.filter(id=task_id, owner=user).first()


def list_tasks(user, limit: int = 10):
    """Последние задачи пользователя для главной страницы. Только свои:
    без owner=user список выдал бы все задачи всех — и перебирать номера
    даже не пришлось бы (docs/ADR-003.md)."""
    return Task.objects.filter(owner=user).select_related("result")[:limit]


def get_result(task: Task) -> dict:
    result = task.result  # OneToOne related_name="result" из PuzzleResult
    return {
        "puzzle": result.puzzle,
        "solution": result.solution,
        "clues": result.clues,
        "elapsed_ms": result.elapsed_ms,
    }
