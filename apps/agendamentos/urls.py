"""Rotas do modulo de agendamentos."""

from django.urls import path

from . import views

app_name = "agendamentos"

urlpatterns = [
    # Fluxo publico / do cliente
    path("", views.agendar, name="agendar"),
    path(
        "horarios-disponiveis/",
        views.horarios_disponiveis,
        name="horarios_disponiveis",
    ),
    path("criar/", views.criar_agendamento, name="criar"),
    path(
        "<int:pk>/confirmacao/",
        views.confirmacao,
        name="confirmacao",
    ),

    # Area "meus agendamentos" (cliente logado)
    path(
        "meus-agendamentos/",
        views.meus_agendamentos,
        name="meus_agendamentos",
    ),
    path(
        "meus-agendamentos/<int:pk>/alterar/",
        views.alterar_meu_agendamento,
        name="alterar_meu_agendamento",
    ),
    path(
        "meus-agendamentos/<int:pk>/cancelar/",
        views.cancelar_meu_agendamento,
        name="cancelar_meu_agendamento",
    ),

    # Area "meus atendimentos" (barbeiro logado)
    path(
        "meus-atendimentos/",
        views.meus_atendimentos,
        name="meus_atendimentos",
    ),

    # Painel administrativo (equipe)
    path("painel/", views.painel_agendamentos, name="painel"),
    path(
        "painel/<int:pk>/confirmar/",
        views.confirmar_agendamento,
        name="confirmar",
    ),
    path(
        "painel/<int:pk>/cancelar/",
        views.cancelar_agendamento,
        name="cancelar",
    ),
    path(
        "painel/<int:pk>/editar/",
        views.editar_agendamento,
        name="editar",
    ),
]