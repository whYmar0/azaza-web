"""Эталонный тест для генератора (методичка, чекпоинт 21.09):
фиксированный seed + проверка единственности решения существующим solve().

Никакой не-seeded случайности в тестах — иначе тест мог бы изредка падать
без изменений в коде (тот самый анти-паттерн "плавающий тест")."""

import os
import subprocess
import sys
from pathlib import Path

from core.generator import generate
from core.solver import solve

SEED = 42


def test_generate_is_reproducible_with_fixed_seed():
    """Тот же seed -> тот же результат, каждый раз."""
    puzzle_a, solution_a = generate(difficulty="medium", seed=SEED)
    puzzle_b, solution_b = generate(difficulty="medium", seed=SEED)
    assert puzzle_a == puzzle_b
    assert solution_a == solution_b


def test_seed_is_reproducible_across_processes():
    """Один процесс не ловит зависимость от хеш-рандомизации Python:
    запускаем генератор в отдельных процессах с разным PYTHONHASHSEED —
    результат при одном seed обязан совпасть (как после рестарта сервера)."""
    code = "from core.generator import generate; print(generate('hard', 42)[0])"
    outputs = set()
    for hash_seed in ("1", "2", "3"):
        env = {**os.environ, "PYTHONHASHSEED": hash_seed}
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, env=env, check=True,
            cwd=Path(__file__).resolve().parents[2],
        )
        outputs.add(result.stdout.strip())
    assert len(outputs) == 1


def test_generated_puzzle_has_unique_solution():
    """Проверка единственности — тем же solve(), что решает чужие сетки,
    а не отдельной "доверительной" логикой внутри генератора."""
    puzzle, solution = generate(difficulty="medium", seed=SEED)
    assert solve(puzzle) == solution


def test_generated_solution_is_a_valid_full_grid():
    _, solution = generate(difficulty="easy", seed=SEED)
    assert len(solution) == 81
    assert "." not in solution


def test_different_seeds_give_different_puzzles():
    """Не гарантия качества генератора, но ловит грубую ошибку вида
    "seed вообще не используется, всегда одна и та же сетка"."""
    puzzle_a, _ = generate(difficulty="medium", seed=1)
    puzzle_b, _ = generate(difficulty="medium", seed=2)
    assert puzzle_a != puzzle_b


def test_hard_difficulty_has_fewer_clues_than_easy():
    puzzle_easy, _ = generate(difficulty="easy", seed=SEED)
    puzzle_hard, _ = generate(difficulty="hard", seed=SEED)
    clues_easy = sum(1 for c in puzzle_easy if c != ".")
    clues_hard = sum(1 for c in puzzle_hard if c != ".")
    assert clues_hard <= clues_easy
