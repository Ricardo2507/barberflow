"""Registro do modelo Usuario no Django Admin."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Configura a exibição do modelo Usuario no admin."""

    fieldsets = UserAdmin.fieldsets + (
        ("Informações adicionais", {"fields": ("tipo", "telefone")}),
    )
    list_display = ["username", "email", "tipo", "is_active"]
    list_filter = ["tipo", "is_active"]