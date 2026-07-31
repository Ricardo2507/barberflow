"""Regras de negócio para cálculo de horários disponíveis."""

from datetime import date, datetime, time, timedelta

from django.utils import timezone

from apps.profissionais.models import Barbeiro, HorarioTrabalho
from apps.servicos.models import Servico

from .models import Agendamento


def calcular_horarios_livres(
    barbeiro: Barbeiro,
    servico: Servico,
    data_agendamento: date,
) -> list[time]:
    """Retorna os horários disponíveis, futuros e sem conflito."""

    hoje = timezone.localdate()
    agora = timezone.localtime()
    hora_atual = agora.time()

    # Datas anteriores não possuem horários disponíveis
    if data_agendamento < hoje:
        return []

    dia_semana = data_agendamento.weekday()

    janelas_trabalho = HorarioTrabalho.objects.filter(
        barbeiro=barbeiro,
        dia_semana=dia_semana,
    ).order_by("hora_inicio")

    if not janelas_trabalho.exists():
        return []

    duracao = timedelta(minutes=servico.duracao_minutos)

    agendamentos_existentes = Agendamento.objects.filter(
        barbeiro=barbeiro,
        data=data_agendamento,
        status__in=[
            Agendamento.Status.PENDENTE,
            Agendamento.Status.CONFIRMADO,
        ],
    ).values_list("hora_inicio", "hora_fim")

    horarios_livres = []

    for janela in janelas_trabalho:
        cursor = datetime.combine(data_agendamento, janela.hora_inicio)
        fim_janela = datetime.combine(data_agendamento, janela.hora_fim)

        while cursor + duracao <= fim_janela:
            slot_inicio = cursor.time()
            slot_fim = (cursor + duracao).time()

            # Para hoje, só entram horários com início após o momento atual
            if data_agendamento == hoje:
                horario_futuro = slot_inicio > hora_atual
            else:
                horario_futuro = True

            conflita = any(
                existente_inicio is not None
                and existente_fim is not None
                and slot_inicio < existente_fim
                and slot_fim > existente_inicio
                for existente_inicio, existente_fim
                in agendamentos_existentes
            )

            if horario_futuro and not conflita:
                horarios_livres.append(slot_inicio)

            cursor += duracao

    return horarios_livres