"""Views de gerenciamento de serviços (área administrativa)."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .models import Servico


class BarbeiroRequiredMixin(UserPassesTestMixin):
    """Restringe o acesso apenas a usuários do tipo Barbeiro."""

    def test_func(self) -> bool:
        return self.request.user.is_authenticated and self.request.user.is_barbeiro()


class ServicoListView(LoginRequiredMixin, BarbeiroRequiredMixin, ListView):
    """Lista todos os serviços cadastrados."""

    model = Servico
    template_name = "servicos/lista.html"
    context_object_name = "servicos"


class ServicoCreateView(LoginRequiredMixin, BarbeiroRequiredMixin, CreateView):
    """Cria um novo serviço."""

    model = Servico
    fields = ["nome", "descricao", "preco", "duracao_minutos", "ativo"]
    template_name = "servicos/formulario.html"
    success_url = reverse_lazy("servicos:lista")


class ServicoUpdateView(LoginRequiredMixin, BarbeiroRequiredMixin, UpdateView):
    """Edita um serviço existente."""

    model = Servico
    fields = ["nome", "descricao", "preco", "duracao_minutos", "ativo"]
    template_name = "servicos/formulario.html"
    success_url = reverse_lazy("servicos:lista")


class ServicoDeleteView(LoginRequiredMixin, BarbeiroRequiredMixin, DeleteView):
    """Remove um serviço."""

    model = Servico
    template_name = "servicos/confirmar_exclusao.html"
    success_url = reverse_lazy("servicos:lista")

# Create your views here.
