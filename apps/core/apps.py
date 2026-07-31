"""Configuração do app core."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configurações principais do app core."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"