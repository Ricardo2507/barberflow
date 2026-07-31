"""Formulários de cadastro e autenticação de usuários."""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Usuario


class CadastroClienteForm(UserCreationForm):
    """Formulário de cadastro público, restrito ao tipo Cliente."""

    email = forms.EmailField(required=True)
    telefone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = Usuario
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "telefone",
            "password1",
            "password2",
        ]

    def save(self, commit: bool = True) -> Usuario:
        """Força o tipo do usuário como Cliente ao salvar o formulário."""
        usuario = super().save(commit=False)
        usuario.tipo = Usuario.Tipo.CLIENTE
        usuario.email = self.cleaned_data["email"]
        usuario.telefone = self.cleaned_data.get("telefone", "")

        if commit:
            usuario.save()

        return usuario