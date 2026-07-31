

"""Modelos relacionados à autenticação e aos tipos de usuário do sistema."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """Usuário customizado que estende o modelo padrão do Django.

    Adiciona um campo de tipo para diferenciar Clientes de Barbeiros,
    permitindo controle de acesso e regras de negócio específicas
    em cada app (ex: apenas Barbeiros aparecem na tela de agendamento).
    """

    class Tipo(models.TextChoices):
        CLIENTE = "CLIENTE", "Cliente"
        BARBEIRO = "BARBEIRO", "Barbeiro"

    tipo = models.CharField(
        max_length=10,
        choices=Tipo.choices,
        default=Tipo.CLIENTE,
        verbose_name="Tipo de usuário",
    )
    telefone = models.CharField(max_length=20, blank=True)

    def is_barbeiro(self) -> bool:
        """Retorna True se o usuário for do tipo Barbeiro."""
        return self.tipo == self.Tipo.BARBEIRO

    def __str__(self) -> str:
        return self.get_full_name() or self.username
