from django.shortcuts import render

from web.forms import SudokuTaskForm

PROJECT_NAME = "Sudoku Service"


def index(request):
    form = SudokuTaskForm()
    return render(request, "web/index.html", {"project_name": PROJECT_NAME, "form": form})
