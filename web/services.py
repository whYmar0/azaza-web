"""Единственная точка входа для views/API в core/. Вся бизнес-логика тут —
views и api.py её не содержат, только вызывают эти функции.

Фон реализован потоком (threading), а статус хранится прямо в поле
Task.status — отдельного in-memory хранилища задач не нужно (см. ADR-002).
"""

import threading
import time

from core.generator import generate
from core.schemas import SudokuParams
from core.solver import solve
from web.models import PuzzleResult, Task


def create_task(name: str, params: SudokuParams) -> Task:
    task = Task.objects.create(
        name=name,
        kind=params.mode,
        status=Task.Status.QUEUED,
        params=params.model_dump(),
    )
    threading.Thread(target=_run, args=(task.id, params), daemon=True).start()
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
    if not params.grid:
        raise ValueError("Для mode=solve нужна сетка (grid)")

    start = time.perf_counter()
    result = solve(params.grid)
    elapsed_ms = (time.perf_counter() - start) * 1000

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


def get_task(task_id: int) -> Task | None:
    return Task.objects.filter(id=task_id).first()


def get_result(task: Task) -> dict:
    result = task.result  # OneToOne related_name="result" из PuzzleResult
    return {
        "puzzle": result.puzzle,
        "solution": result.solution,
        "clues": result.clues,
        "elapsed_ms": result.elapsed_ms,
    }
