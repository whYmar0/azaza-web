# Sudoku Service

Веб-сервис-генератор судоку с гарантией единственного решения. Формат сетки
— строка из 81 символа (`1`-`9` и `.` для пустой клетки). Один контракт на
два входа: страница (для человека) и `/api/tasks` (для программы).

## Идея

Подробно, с обоснованием архитектуры («рамка») — в `docs/idea.md`.

## API

`POST /api/tasks` — `{"name": "...", "params": {"mode": "solve"|"generate", "grid": "...", "difficulty": "...", "seed": ...}}` → `202` + `{"id": ...}`.
`GET /api/tasks/{id}` — статус (`queued`/`running`/`done`/`error`).
`GET /api/tasks/{id}/result` — результат, когда `status == done`.
Полная документация с примерами запросов — `docs/api.md`; интерактивно —
`/api/docs` (Swagger, автогенерация Django Ninja).

## Структура проекта

- `core/` — вычислительное ядро. Не импортирует Django, не ходит в БД и HTTP.
  - `core/solver.py` — решатель (backtracking + MRV).
  - `core/schemas.py` — `SudokuParams`: pydantic-валидация входа ДО расчёта
    (длина, допустимые символы, паттерны mode/difficulty, отсутствие дублей
    в строках/столбцах/блоках).
  - `core/tests/` — 8 тестов на чистую логику (эталоны + схема).
- `web/` — Django-слой:
  - `web/models.py` — `Task` (заявка, с полями `name`/`kind`/`status`/`params`/`error`), `PuzzleResult`.
  - `web/services.py` — единственная точка входа для views/API в `core/`; фон — поток, статус пишет прямо в `Task.status`.
  - `web/api.py` — тонкий Django Ninja роутер, почти не меняется.
  - `web/forms.py` — форма с теми же именами полей, что в `core/schemas.py`.
  - `web/views.py`, `web/templates/` — страница с формой.
- `tests/test_api.py` — тест уровня API (нужен Django, поэтому отдельно от `core/tests/`).
- `docs/` — идея (`idea.md`), API-контракт (`api.md`), ER-схема
  (`ER.png`), архитектурные решения (`ADR-001.md`, `ADR-002.md`),
  самопроверка архитектуры (`fat_review.md`).

## Запуск с чистой машины

```bash
git clone <url> sudoku-service && cd sudoku-service
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Тесты: `pytest`. Админка: `http://127.0.0.1:8000/admin/`. API-документация:
`http://127.0.0.1:8000/api/docs`.

## Архитектурные принципы

1. `core/` не зависит от Django, БД и HTTP.
2. Views и API не содержат бизнес-логики — только вызывают `web/services.py`.
3. Вход валидируется pydantic-схемой до расчёта. Никакого `eval`.
4. Секреты — только в `.env`.

## Вклад

| Участник | Что сделал |
|---|---|
| Ташлигов Ахмед | Стартер проекта, `sudoku_service/`, `requirements.txt`, `.env.example`, `web/api.py`, `tests/test_api.py	` |
| Умаров Зелим | `docs/fat_review.md`, `docs/ADR-001.md`, `web/forms.py` |
| Альсиев Идрис | `docs/ER.png`, `web/models.py`, `web/migrations/`, `web/services.py` |
| Байраев Магомед-Эми | `core/schemas.py` , `core/solver.py`, `core/tests/`, `docs/ADR-002.md` |
