#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sudoku_service.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Не удалось импортировать Django. Убедитесь, что виртуальное "
            "окружение активировано и pip install -r requirements.txt выполнен."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
