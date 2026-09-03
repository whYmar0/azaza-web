from django.shortcuts import render

PROJECT_NAME = "Sudoku Service"


def index(request):
    return render(request, "web/index.html", {"project_name": PROJECT_NAME})
