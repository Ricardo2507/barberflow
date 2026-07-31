"""Rotas de gerenciamento de serviços."""

from django.urls import path

from . import views

app_name = "servicos"

urlpatterns = [
    path("", views.ServicoListView.as_view(), name="lista"),
    path("novo/", views.ServicoCreateView.as_view(), name="criar"),
    path("<int:pk>/editar/", views.ServicoUpdateView.as_view(), name="editar"),
    path(
        "<int:pk>/excluir/",
        views.ServicoDeleteView.as_view(),
        name="excluir",
    ),
]