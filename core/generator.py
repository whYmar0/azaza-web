"""Генератор судоку с гарантией единственного решения.

core/ — чистая логика, без Django/БД/HTTP (как и solver.py).

Алгоритм:
1. Построить полную (без пустых клеток) валидную сетку — backtracking
   с перемешанным порядком кандидатов, детерминированным при фиксированном
   seed.
2. Удалять клетки по одной, в порядке, зависящем от seed. После каждого
   удаления проверять единственность решения через `solve()` (limit=2);
   если решений стало больше одного — клетку возвращать на место.
3. Останавливаться, когда достигнуто целевое число подсказок для выбранной
   сложности или когда весь порядок ячеек пройден.

Один и тот же seed всегда даёт одну и ту же пару (puzzle, solution).
"""

import random

from core.solver import DIGITS, EMPTY, GRID_SIZE, TOO_COMPLEX, solve

TARGET_CLUES = {"easy": 40, "medium": 32, "hard": 26}


def _candidates_for_full_grid(grid: list[str], idx: int) -> set[str]:
    """Те же правила, что в core/solver.py::_candidates, но локально —
    не считаем нужным делить приватную функцию между двумя модулями
    ради одной строки правил "цифры 1-9 без повторов в ряду/столбце/блоке"."""
    row, col = divmod(idx, GRID_SIZE)
    used: set[str] = set()
    for c in range(GRID_SIZE):
        used.add(grid[row * GRID_SIZE + c])
    for r in range(GRID_SIZE):
        used.add(grid[r * GRID_SIZE + col])
    box_row, box_col = (row // 3) * 3, (col // 3) * 3
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            used.add(grid[r * GRID_SIZE + c])
    return DIGITS - used


def _build_full_grid(rng: random.Random) -> str:
    """Построить случайную (для данного rng) полностью заполненную и
    валидную по правилам судоку сетку backtracking-ом."""
    grid: list[str] = [EMPTY] * (GRID_SIZE * GRID_SIZE)

    def backtrack(idx: int) -> bool:
        if idx == len(grid):
            return True
        # sorted() обязателен: порядок обхода set строк зависит от
        # PYTHONHASHSEED и меняется между запусками процесса. Без сортировки
        # один и тот же seed давал бы разные сетки при каждом рестарте сервера.
        candidates = sorted(_candidates_for_full_grid(grid, idx))
        rng.shuffle(candidates)
        for value in candidates:
            grid[idx] = value
            if backtrack(idx + 1):
                return True
            grid[idx] = EMPTY
        return False

    backtrack(0)
    return "".join(grid)


def generate(difficulty: str = "medium", seed: int | None = None) -> tuple[str, str]:
    """Сгенерировать головоломку с гарантированно единственным решением.

    Возвращает (puzzle, solution) — обе строки по 81 символу. `puzzle`
    содержит "." на месте убранных клеток, `solution` — полностью
    заполненная сетка, из которой puzzle получена.
    """
    rng = random.Random(seed)
    solution = _build_full_grid(rng)
    grid = list(solution)

    target_clues = TARGET_CLUES.get(difficulty, TARGET_CLUES["medium"])
    order = list(range(GRID_SIZE * GRID_SIZE))
    rng.shuffle(order)

    clues = GRID_SIZE * GRID_SIZE
    for idx in order:
        if clues <= target_clues:
            break
        removed_value = grid[idx]
        grid[idx] = EMPTY
        # Проверка единственности после удаления: solve() с ранним выходом.
        # TOO_COMPLEX — тоже «не доказано единственности»: клетку возвращаем.
        # По замеру при генерации худший вызов solve() — 1 275 шагов из 50 000,
        # так что на практике TOO_COMPLEX не срабатывает.
        if solve("".join(grid)) in ("multiple", "no solution", TOO_COMPLEX):
            grid[idx] = removed_value  # не единственно — клетку возвращаем
        else:
            clues -= 1

    return "".join(grid), solution
