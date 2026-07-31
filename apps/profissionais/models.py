"""Modelos de Barbeiros e seus horários de trabalho."""

from django.conf import settings
from django.db import models

from apps.servicos.models import Servico


class Barbeiro(models.Model):
    """Perfil profissional vinculado a um Usuario do tipo BARBEIRO."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_barbeiro",
    )
    especialidades = models.ManyToManyField(
        Servico,
        related_name="barbeiros",
        blank=True,
        help_text="Serviços que este barbeiro está apto a realizar.",
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Barbeiro"
        verbose_name_plural = "Barbeiros"

    def __str__(self) -> str:
        return self.usuario.get_full_name() or self.usuario.username


class HorarioTrabalho(models.Model):
    """Janela de trabalho recorrente de um barbeiro em um dia da semana."""

    class DiaSemana(models.IntegerChoices):
        SEGUNDA = 0, "Segunda-feira"
        TERCA = 1, "Terça-feira"
        QUARTA = 2, "Quarta-feira"
        QUINTA = 3, "Quinta-feira"
        SEXTA = 4, "Sexta-feira"
        SABADO = 5, "Sábado"
        DOMINGO = 6, "Domingo"

    barbeiro = models.ForeignKey(
        Barbeiro, on_delete=models.CASCADE, related_name="horarios_trabalho"
    )
    dia_semana = models.IntegerField(choices=DiaSemana.choices)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()

    class Meta:
        verbose_name = "Horário de Trabalho"
        verbose_name_plural = "Horários de Trabalho"
        unique_together = ("barbeiro", "dia_semana", "hora_inicio")
        ordering = ["dia_semana", "hora_inicio"]

    def __str__(self) -> str:
        return (
            f"{self.barbeiro} - {self.get_dia_semana_display()} "
            f"({self.hora_inicio} às {self.hora_fim})"
        )