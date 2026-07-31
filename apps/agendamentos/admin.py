"""Registro do modelo Agendamento no Django Admin."""

from django.contrib import admin

from .models import Agendamento


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    """Configura a exibição do modelo Agendamento no admin."""

    list_display = [
        "cliente",
        "barbeiro",
        "servico",
        "data",
        "hora_inicio",
        "status",
    ]
    list_filter = ["status", "data", "barbeiro"]
    search_fields = ["cliente__username", "barbeiro__usuario__username"]