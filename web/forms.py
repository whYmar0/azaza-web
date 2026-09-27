"""Форма для человека — те же поля и те же имена, что в core/schemas.py."""

from django import forms

MODE_CHOICES = [("solve", "Решить"), ("generate", "Сгенерировать")]
DIFFICULTY_CHOICES = [("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")]


class SudokuTaskForm(forms.Form):
    mode = forms.ChoiceField(choices=MODE_CHOICES, label="Режим")
    grid = forms.CharField(
        required=False, min_length=81, max_length=81, label="Сетка (81 символ)"
    )
    difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES, initial="medium", label="Сложность"
    )
    seed = forms.IntegerField(required=False, label="Seed")
