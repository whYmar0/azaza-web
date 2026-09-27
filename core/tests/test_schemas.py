"""Проверка: некорректная сетка отклоняется схемой ДО расчёта (не внутри
core/solver.py). Пример с двумя пятёрками в одной строке ; пример с длиной 80 символов"""

import pytest
from pydantic import ValidationError

from core.schemas import SudokuParams


def test_duplicate_in_row_is_rejected_before_calculation():
    grid = "55......." + "." * 72  # две пятёрки в первой строке
    with pytest.raises(ValidationError):
        SudokuParams(mode="solve", grid=grid)


def test_duplicate_in_column_is_rejected():
    grid = list("." * 81)
    grid[0] = "7"
    grid[9] = "7"  # тот же столбец, следующая строка
    with pytest.raises(ValidationError):
        SudokuParams(mode="solve", grid="".join(grid))


def test_wrong_length_grid_is_rejected():
    """80 символов вместо 81"""
    with pytest.raises(ValidationError):
        SudokuParams(mode="solve", grid="." * 80)


def test_valid_empty_grid_is_accepted():
    SudokuParams(mode="solve", grid="." * 81)  # не должно бросать исключение


def test_generate_mode_without_grid_is_accepted():
    SudokuParams(mode="generate", difficulty="hard", seed=1)


def test_invalid_mode_is_rejected():
    with pytest.raises(ValidationError):
        SudokuParams(mode="wrong-mode")
