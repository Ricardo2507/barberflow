"""Modelo de Serviços oferecidos pela barbearia."""

from django.db import models


class Servico(models.Model):
    """Representa um serviço oferecido (Cabelo, Barba, Combo etc.)."""

    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    duracao_minutos = models.PositiveIntegerField(
        help_text="Tempo estimado de execução do serviço, em minutos."
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"

    def __str__(self) -> str:
        return f"{self.nome} ({self.duracao_minutos} min)"
