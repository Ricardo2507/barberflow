"""Views principais do sistema."""

from django.shortcuts import render


def home(request):
    """Exibe a página inicial do BarberFlow."""

    return render(
        request,
        "home.html",
    )