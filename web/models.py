"""Django ORM живёт только здесь и в migrations/ — core/ про БД не знает,
как того требует AGENTS.md. Структура соответствует docs/ER.png."""

from django.db import models


class Task(models.Model):
    """Заявка на вычисление. Лёгкая, часто опрашивается (status)."""

    class Kind(models.TextChoices):
        GENERATE = "generate", "Генерация"
        SOLVE = "solve", "Решение"
        VALIDATE = "validate", "Проверка"

    class Status(models.TextChoices):
        QUEUED = "queued", "В очереди"
        RUNNING = "running", "Выполняется"
        DONE = "done", "Готово"
        ERROR = "error", "Ошибка"

    name = models.CharField(max_length=100, default="")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.QUEUED
    )
    params = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Task#{self.id} {self.name} ({self.kind}/{self.status})"


class PuzzleResult(models.Model):
    """Результат задачи. Создаётся один раз, когда Task.status == done.

    81 int — это не «большие данные» (см. docs/ER.png), поэтому puzzle
    и solution хранятся прямо в таблице, в JSONField, без отдельного файла.
    """

    task = models.OneToOneField(
        Task, on_delete=models.CASCADE, related_name="result"
    )
    puzzle = models.JSONField()
    solution = models.JSONField()
    clues = models.PositiveSmallIntegerField()
    elapsed_ms = models.FloatField()

    def __str__(self) -> str:
        return f"Result for Task#{self.task_id}"
