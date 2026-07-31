
"""Views de autenticação e cadastro de usuários."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CadastroClienteForm


class CadastroClienteView(CreateView):
    """Permite que um novo cliente crie sua própria conta."""

    form_class = CadastroClienteForm
    template_name = "usuarios/cadastro.html"
    success_url = reverse_lazy("agendamentos:agendar")

    def form_valid(self, form):
        """Autentica o usuário automaticamente após o cadastro."""
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Cadastro realizado com sucesso!")
        return response


class EntrarView(LoginView):
    """Tela de login do sistema."""

    template_name = "usuarios/login.html"
    redirect_authenticated_user = True


class SairView(LogoutView):
    """Efetua logout e redireciona para a tela de login."""

    next_page = reverse_lazy("usuarios:login")
