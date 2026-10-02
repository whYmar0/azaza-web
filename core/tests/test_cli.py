"""Ядро из консоли — python -m core сетка.txt (core/__main__.py).

Эталон тот же, что у сайта и API: головоломка Википедии с опубликованным
решением (ответ известен заранее, не из нашего кода)."""

import subprocess
import sys
from pathlib import Path

from core.__main__ import main

ROOT = Path(__file__).resolve().parents[2]
WIKI_PUZZLE = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
WIKI_SOLUTION = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"


def _file(tmp_path, text: str) -> str:
    path = tmp_path / "grid.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_prints_published_solution(tmp_path, capsys):
    assert main([_file(tmp_path, WIKI_PUZZLE + "\n")]) == 0
    assert capsys.readouterr().out.strip() == WIKI_SOLUTION


def test_grid_in_nine_lines_is_accepted(tmp_path, capsys):
    """Сетку удобнее писать девятью строками — переводы строк не считаются."""
    nine_lines = "\n".join(WIKI_PUZZLE[i:i + 9] for i in range(0, 81, 9))
    assert main([_file(tmp_path, nine_lines)]) == 0
    assert capsys.readouterr().out.strip() == WIKI_SOLUTION


def test_bad_grid_prints_reason_not_traceback(tmp_path, capsys):
    """80 символов: причина словами и код 1, а не падение с ValueError."""
    assert main([_file(tmp_path, WIKI_PUZZLE[:-1])]) == 1
    assert "Ошибка во входе" in capsys.readouterr().out


def test_repeated_digit_is_caught_by_schema(tmp_path, capsys):
    """Две пятёрки в первой строке: ловит схема, до перебора не доходит."""
    assert main([_file(tmp_path, "55" + WIKI_PUZZLE[2:])]) == 1
    assert "Повтор цифры 5" in capsys.readouterr().out


def test_empty_grid_has_many_solutions(tmp_path, capsys):
    assert main([_file(tmp_path, "." * 81)]) == 1
    assert "решений больше одного" in capsys.readouterr().out


def test_wrong_call_prints_usage(capsys):
    assert main([]) == 2
    assert "python -m core" in capsys.readouterr().out


def test_missing_file_is_code_2(tmp_path, capsys):
    assert main([str(tmp_path / "нет-такого.txt")]) == 2
    assert "Не удалось прочитать файл" in capsys.readouterr().out


def test_runs_as_module_without_django():
    """Настоящий запуск, как в README: отдельный процесс, файл из репозитория.
    Заодно проверяем главное правило ядра: Django при этом не загружается."""
    run = subprocess.run(
        [sys.executable, "-m", "core", "сетка.txt"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
    )
    assert run.returncode == 0, run.stderr
    assert run.stdout.strip() == WIKI_SOLUTION

    probe = subprocess.run(
        [sys.executable, "-c",
         "import sys, core.__main__; print('django' in sys.modules)"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert probe.stdout.strip() == "False", probe.stderr
