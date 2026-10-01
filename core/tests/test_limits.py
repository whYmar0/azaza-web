"""Тесты границ входа на уровне ядра и схемы (без Django).

Сетка без решения — сетка Питера Норвига («norvig.com/sudoku.html»):
в ней нет повторов, поэтому схема её пропускает, но решения у неё нет."""

import time

import pytest
from pydantic import ValidationError

from core.schemas import SudokuParams
from core.solver import (
    MAX_STEPS,
    TOO_COMPLEX,
    StepLimitExceeded,
    _find_solutions,
    solve,
)

NORVIG_NO_SOLUTION = (
    ".....5.8." "...6.1.43" "........." ".1.5....." "...1.6..."
    "3.......5" "53.....61" "........4" "........."
)
INKALA = (
    "8........" "..36....." ".7..9.2.." ".5...7..." "....457.."
    "...1...3." "..1....68" "..85...1." ".9....4.."
)


def test_grid_without_solution_passes_schema():
    """Почему предел нужен именно в ядре: схема такую сетку не отсечёт."""
    SudokuParams(mode="solve", grid=NORVIG_NO_SOLUTION)


def test_grid_without_solution_stops_at_step_limit():
    start = time.perf_counter()
    assert solve(NORVIG_NO_SOLUTION) == TOO_COMPLEX
    # ~3 с на ноутбуке; 30 с — с запасом для медленной машины, но не 150+.
    assert time.perf_counter() - start < 30


def test_limit_counts_steps_not_solutions():
    """limit=2 — число решений; max_steps — число шагов. Инкале нужно
    ~19 000 шагов: с пределом 100 перебор обязан остановиться."""
    with pytest.raises(StepLimitExceeded):
        _find_solutions(list(INKALA), limit=2, max_steps=100)


def test_hardest_known_puzzle_still_fits_the_limit():
    """Предел не режет корректные сетки: Инкала решается в пределах
    MAX_STEPS (ответ сверен в core/tests/test_reference_puzzle.py)."""
    assert len(_find_solutions(list(INKALA), limit=2, max_steps=MAX_STEPS)) == 1


def test_solve_without_grid_is_rejected_by_schema():
    with pytest.raises(ValidationError, match="grid"):
        SudokuParams(mode="solve")


def test_seed_has_bounds():
    with pytest.raises(ValidationError):
        SudokuParams(mode="generate", seed=-1)
    with pytest.raises(ValidationError):
        SudokuParams(mode="generate", seed=2**32)
    SudokuParams(mode="generate", seed=2**32 - 1)
