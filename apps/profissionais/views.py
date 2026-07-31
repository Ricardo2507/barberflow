"""Views de gerenciamento de barbeiros e visualização pública da equipe."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView

from .models import Barbeiro


class BarbeiroListView(ListView):
    """Lista pública dos barbeiros ativos, usada na tela de agendamento."""

    model = Barbeiro
    template_name = "profissionais/lista.html"
    context_object_name = "barbeiros"

    def get_queryset(self):
        """Retorna apenas barbeiros ativos."""
        return Barbeiro.objects.filter(ativo=True).select_related("usuario")


class BarbeiroDetailView(LoginRequiredMixin, DetailView):
    """Exibe o painel de agenda de um barbeiro específico."""

    model = Barbeiro
    template_name = "profissionais/painel_agenda.html"
    context_object_name = "barbeiro"

    def get_context_data(self, **kwargs):
        """Adiciona os agendamentos do dia ao contexto."""
        from datetime import date

        context = super().get_context_data(**kwargs)
        context["agendamentos_hoje"] = self.object.agendamentos.filter(
            data=date.today()
        ).select_related("cliente", "servico")
        return context

# Create your views here.
