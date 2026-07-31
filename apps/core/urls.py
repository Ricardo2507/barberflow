"""URLs principais do projeto."""

from django.contrib import admin
from django.urls import include, path

from apps.core import views as core_views

urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "",
        core_views.home,
        name="home",
    ),
    path(
        "agendamentos/",
        include("apps.agendamentos.urls"),
    ),
    path(
        "usuarios/",
        include("apps.usuarios.urls"),
    ),
    path(
        "servicos/",
        include("apps.servicos.urls"),
    ),
    path(
        "barbeiros/",
        include("apps.profissionais.urls"),
    ),
]