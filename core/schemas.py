"""pydantic-схемы параметров задачи (core/schemas.py).

Вход валидируется здесь ДО расчёта — никакого eval, никакой проверки
корректности сетки внутри core/solver.py. Поля и структура — mode/grid/difficulty/seed; проверка на дубли в
строках/столбцах/блоках — наше дополнение поверх
"""

from pydantic import BaseModel, Field, field_validator

GRID_LENGTH = 81
GRID_SIZE = 9
BOX_SIZE = 3
VALID_CHARS = set("123456789.")


class SudokuParams(BaseModel):
    """Параметры задачи: решить готовую сетку или сгенерировать новую.

    mode решает, что делает ядро — два режима в одном контракте, а не
    два разных адреса (так проще: /api/tasks один на всё).
    """

    mode: str = Field(pattern=r"^(solve|generate)$")
    grid: str | None = Field(default=None, min_length=GRID_LENGTH, max_length=GRID_LENGTH)
    difficulty: str = Field(default="medium", pattern=r"^(easy|medium|hard)$")
    seed: int | None = None  # та же сетка при том же seed

    @field_validator("grid")
    @classmethod
    def validate_grid_contents(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not set(value) <= VALID_CHARS:
            raise ValueError("Сетка может содержать только цифры 1-9 и символ '.'")
        for kind, group in _all_groups():
            seen: set[str] = set()
            for idx in group:
                digit = value[idx]
                if digit == ".":
                    continue
                if digit in seen:
                    raise ValueError(
                        f"Повтор цифры {digit} в {kind} — сетка некорректна"
                    )
                seen.add(digit)
        return value


def _all_groups() -> list[tuple[str, list[int]]]:
    groups: list[tuple[str, list[int]]] = []
    for row in range(GRID_SIZE):
        groups.append((f"row {row}", [row * GRID_SIZE + c for c in range(GRID_SIZE)]))
    for col in range(GRID_SIZE):
        groups.append((f"column {col}", [r * GRID_SIZE + col for r in range(GRID_SIZE)]))
    for box_row in range(0, GRID_SIZE, BOX_SIZE):
        for box_col in range(0, GRID_SIZE, BOX_SIZE):
            indices = [
                (box_row + r) * GRID_SIZE + (box_col + c)
                for r in range(BOX_SIZE)
                for c in range(BOX_SIZE)
            ]
            groups.append((f"box ({box_row},{box_col})", indices))
    return groups
