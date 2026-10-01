"""Решатель судоку.

Формат сетки — строка из 81 символа: '1'-'9' и '.' для пустой клетки
(общепринятый текстовый формат судоку — тот же, что на слайде курса и в
Wikipedia). core/ не импортирует Django, не ходит в БД и HTTP — здесь
только чистая логика поиска решения.
"""

GRID_SIZE = 9
BOX_SIZE = 3
EMPTY = "."
DIGITS = set("123456789")

# Предел шагов перебора. limit=2 ниже — число РЕШЕНИЙ, а не шагов.
# На сетке без решения перебор идёт без конца. Предел выбран по замеру:
#   классическая сетка (Wikipedia)     —     52 шага
#   сетка Инкалы (2012)                — 18 936 шагов, ~1.4 с
#   генерация hard, худший solve()     —  1 275 шагов
#   сетка Норвига без решения          — >2 000 000 шагов, не закончила
# 50 000 — в 2.6 раза больше Инкалы; на сетке без решения ~3 с. Шаг = один вызов backtrack().
MAX_STEPS = 50_000
TOO_COMPLEX = "too complex"


class StepLimitExceeded(Exception):
    """Перебор превысил MAX_STEPS — сетка слишком сложная или без решения."""


def _candidates(grid: list[str], idx: int) -> set[str]:
    row, col = divmod(idx, GRID_SIZE)
    used: set[str] = set()
    for c in range(GRID_SIZE):
        used.add(grid[row * GRID_SIZE + c])
    for r in range(GRID_SIZE):
        used.add(grid[r * GRID_SIZE + col])
    box_row, box_col = (row // BOX_SIZE) * BOX_SIZE, (col // BOX_SIZE) * BOX_SIZE
    for r in range(box_row, box_row + BOX_SIZE):
        for c in range(box_col, box_col + BOX_SIZE):
            used.add(grid[r * GRID_SIZE + c])
    return DIGITS - used


def _find_mrv_cell(grid: list[str]) -> tuple[int, set[str]] | None:
    """Пустая клетка с наименьшим числом вариантов (MRV-эвристика)."""
    best_idx: int | None = None
    best_candidates: set[str] = set()
    for idx, value in enumerate(grid):
        if value != EMPTY:
            continue
        candidates = _candidates(grid, idx)
        if best_idx is None or len(candidates) < len(best_candidates):
            best_idx, best_candidates = idx, candidates
            if not candidates:
                return best_idx, best_candidates
    if best_idx is None:
        return None
    return best_idx, best_candidates


def _find_solutions(
    grid: list[str], limit: int = 2, max_steps: int = MAX_STEPS
) -> list[str]:
    """Найти до `limit` решений — не больше, чем нужно для проверки
    единственности (не решаем до конца, если решений уже 2).

    Больше `max_steps` шагов -> StepLimitExceeded."""
    found: list[str] = []
    steps = 0

    def backtrack() -> None:
        nonlocal steps
        if len(found) >= limit:
            return
        steps += 1
        if steps > max_steps:
            raise StepLimitExceeded(f"превышен предел перебора: {max_steps} шагов")
        cell = _find_mrv_cell(grid)
        if cell is None:
            found.append("".join(grid))
            return
        idx, candidates = cell
        # sorted(): порядок обхода set зависит от PYTHONHASHSEED (тот же баг,
        # что был в генераторе). Без сортировки число шагов, а значит и
        # срабатывание предела, менялось бы от запуска к запуску.
        for value in sorted(candidates):
            if len(found) >= limit:
                return
            grid[idx] = value
            backtrack()
            grid[idx] = EMPTY

    backtrack()
    return found


def solve(grid: str) -> str:
    """Решить судоку.

    Возвращает решение (81 символ), если оно единственное. Если решений
    несколько (в том числе пустая или сильно недоопределённая сетка) —
    возвращает "multiple". Если решений нет вовсе — "no solution".

    Если перебор не уложился в MAX_STEPS шагов — «тоо complex» (TOO_COMPLEX).
    Схема (core/schemas.py) отсекает сетки с повторами, но сетку без повторов
    и без решения заранее не распознать — её можно только остановить по пределу.
    """
    if len(grid) != GRID_SIZE * GRID_SIZE:
        raise ValueError("Сетка должна содержать ровно 81 символ")

    try:
        solutions = _find_solutions(list(grid), limit=2)
    except StepLimitExceeded:
        return TOO_COMPLEX

    if len(solutions) == 1:
        return solutions[0]
    if len(solutions) == 0:
        return "no solution"
    return "multiple"
