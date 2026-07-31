"""Modelos do app de agendamentos."""

from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.profissionais.models import Barbeiro
from apps.servicos.models import Servico


class Agendamento(models.Model):
    """Representa a reserva de um horário para um serviço com um barbeiro."""

    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        CONFIRMADO = "CONFIRMADO", "Confirmado"
        CANCELADO = "CANCELADO", "Cancelado"
        CONCLUIDO = "CONCLUIDO", "Concluído"

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agendamentos",
    )
    barbeiro = models.ForeignKey(
        Barbeiro,
        on_delete=models.CASCADE,
        related_name="agendamentos",
    )
    servico = models.ForeignKey(
        Servico,
        on_delete=models.PROTECT,
        related_name="agendamentos",
    )
    data = models.DateField()
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField(
        blank=True,
        help_text="Calculado automaticamente a partir da duração do serviço.",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDENTE,
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ["data", "hora_inicio"]
        unique_together = ("barbeiro", "data", "hora_inicio")

    def clean(self) -> None:
        """Calcula hora_fim e valida data, horário e sobreposição."""

        if not self.data or not self.hora_inicio or not self.servico_id:
            return

        # Calcula hora_fim aqui, pois neste ponto do ciclo
        # (form.is_valid() chama full_clean antes do save) o
        # valor ainda pode estar vazio.
        inicio_dt = datetime.combine(self.data, self.hora_inicio)
        fim_dt = inicio_dt + timedelta(
            minutes=self.servico.duracao_minutos
        )
        self.hora_fim = fim_dt.time()

        hoje = timezone.localdate()
        agora = timezone.localtime()

        # Impede agendamento em data que já passou
        if self.data < hoje:
            raise ValidationError(
                {"data": "Não é possível agendar para uma data passada."}
            )

        # Impede agendamento em horário que já passou, se for hoje
        if self.data == hoje and self.hora_inicio <= agora.time():
            raise ValidationError(
                {
                    "hora_inicio": (
                        "Não é possível agendar para um horário "
                        "que já passou."
                    )
                }
            )

        # Valida sobreposição de horários para o mesmo barbeiro
        conflitos = Agendamento.objects.filter(
            barbeiro=self.barbeiro,
            data=self.data,
            status__in=[self.Status.PENDENTE, self.Status.CONFIRMADO],
        ).exclude(pk=self.pk)

        for agendamento in conflitos:
            if not agendamento.hora_fim:
                continue

            if (
                self.hora_inicio < agendamento.hora_fim
                and self.hora_fim > agendamento.hora_inicio
            ):
                raise ValidationError(
                    "Este barbeiro já possui um agendamento nesse horário."
                )

    def save(self, *args, **kwargs) -> None:
        """Executa a validação completa (incluindo clean) antes de salvar."""

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"{self.cliente} com {self.barbeiro} em {self.data} "
            f"às {self.hora_inicio}"
        )