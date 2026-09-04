from django.contrib import admin

from web.models import PuzzleResult, Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "status", "created_at", "updated_at")
    list_filter = ("kind", "status")


@admin.register(PuzzleResult)
class PuzzleResultAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "clues", "elapsed_ms")
