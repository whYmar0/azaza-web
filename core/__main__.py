"""python -m core сетка.txt  ->  решение или причина.

Запуск ядра без сайта (требование сдачи 28.09): ни Django, ни базы, ни
HTTP. Тот же путь, что у сайта и API: сначала схема (core/schemas.py),
потом solve() (core/solver.py) — только результат печатается в консоль.

Файл: сетка из 81 символа ('1'-'9' и '.'), одной строкой или девятью
строками по девять — пробелы и переводы строк не считаются.

Код выхода: 0 — решение найдено, 1 — решения нет (причина напечатана),
2 — программу вызвали неправильно (нет файла или лишние аргументы).
"""

import sys

from pydantic import ValidationError

from core.schemas import SudokuParams
from core.solver import MAX_STEPS, TOO_COMPLEX, solve

USAGE = "Использование: python -m core сетка.txt"

REASONS = {
    "multiple": "решений больше одного",
    "no solution": "решения нет",
    TOO_COMPLEX: f"превышен предел перебора ({MAX_STEPS} шагов): "
    "сетка слишком сложная или не имеет решения",
}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(USAGE)
        return 2
    try:
        with open(args[0], encoding="utf-8") as f:
            grid = "".join(f.read().split())  # 81 символ: цифры и точки
    except OSError as exc:
        print(f"Не удалось прочитать файл: {exc}")
        return 2

    try:
        SudokuParams(mode="solve", grid=grid)  # та же проверка, что у сайта и API
    except ValidationError as exc:
        for err in exc.errors():
            print("Ошибка во входе:", err["msg"].removeprefix("Value error, "))
        return 1

    result = solve(grid)
    if result in REASONS:
        print("Решение не найдено:", REASONS[result])
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
