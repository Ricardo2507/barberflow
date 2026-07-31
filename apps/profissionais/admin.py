
"""Registro dos modelos Barbeiro e HorarioTrabalho no Django Admin."""

from django.contrib import admin

from .models import Barbeiro, HorarioTrabalho


class HorarioTrabalhoInline(admin.TabularInline):
    """Permite editar os horários de trabalho junto com o barbeiro."""

    model = HorarioTrabalho
    extra = 1


@admin.register(Barbeiro)
class BarbeiroAdmin(admin.ModelAdmin):
    """Configura a exibição do modelo Barbeiro no admin."""

    list_display = ["usuario", "ativo"]
    list_filter = ["ativo"]
    filter_horizontal = ["especialidades"]
    inlines = [HorarioTrabalhoInline]