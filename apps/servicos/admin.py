"""Registro do modelo Servico no Django Admin."""

from django.contrib import admin

from .models import Servico


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    """Configura a exibição do modelo Servico no admin."""

    list_display = ["nome", "preco", "duracao_minutos", "ativo"]
    list_filter = ["ativo"]
    search_fields = ["nome"]