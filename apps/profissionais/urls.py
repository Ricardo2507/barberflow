"""Rotas de listagem e painel de barbeiros."""

from django.urls import path

from . import views

app_name = "profissionais"

urlpatterns = [
    path("", views.BarbeiroListView.as_view(), name="lista"),
    path("<int:pk>/agenda/", views.BarbeiroDetailView.as_view(), name="agenda"),
]