from django.urls import path

from . import views

app_name = "agendamentos"

urlpatterns = [
    path(
        "agendar/",
        views.agendar,
        name="agendar",
    ),
    path(
        "horarios-disponiveis/",
        views.horarios_disponiveis,
        name="horarios_disponiveis",
    ),
    path(
        "criar/",
        views.criar_agendamento,
        name="criar_agendamento",
    ),
    path(
        "confirmacao/<int:pk>/",
        views.confirmacao,
        name="confirmacao",
    ),
    path(
        "meus-agendamentos/",
        views.meus_agendamentos,
        name="meus_agendamentos",
    ),
    path(
        "meus-agendamentos/<int:pk>/cancelar/",
        views.cancelar_meu_agendamento,
        name="cancelar_meu_agendamento",
    ),
    path(
        "meus-agendamentos/<int:pk>/alterar/",
        views.alterar_meu_agendamento,
        name="alterar_meu_agendamento",
    ),
    path(
        "meus-atendimentos/",
        views.meus_atendimentos,
        name="meus_atendimentos",
    ),
    path(
        "painel/",
        views.painel_agendamentos,
        name="painel",
    ),
    path(
        "painel/<int:pk>/confirmar/",
        views.confirmar_agendamento,
        name="confirmar_agendamento",
    ),
    path(
        "painel/<int:pk>/finalizar/",
        views.finalizar_agendamento,
        name="finalizar_agendamento",
    ),
    path(
        "painel/<int:pk>/cancelar/",
        views.cancelar_agendamento,
        name="cancelar_agendamento",
    ),
    path(
        "painel/<int:pk>/editar/",
        views.editar_agendamento,
        name="editar_agendamento",
    ),
]
