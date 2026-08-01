# apps/agendamentos/forms.py

from datetime import datetime # Necessário para datetime.combine
from django.utils import timezone # Necessário para timezone.localtime e timezone.make_aware

from django import forms

from apps.profissionais.models import Barbeiro
from apps.servicos.models import Servico

from .models import Agendamento
from .services import calcular_horarios_livres # Importa a função de serviço

class AgendamentoForm(forms.ModelForm):
    """Formulário utilizado pelo cliente para criar ou alterar um agendamento."""

    class Meta:
        model = Agendamento
        fields = ["servico", "barbeiro", "data", "hora_inicio"]
        widgets = {
            "data": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                    "class": "form-control",
                },
            ),
            "hora_inicio": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "type": "time",
                    "class": "form-control",
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data"].input_formats = ["%Y-%m-%d"]
        self.fields["hora_inicio"].input_formats = ["%H:%M"]

        # Garante que apenas serviços e barbeiros ativos sejam exibidos
        self.fields["servico"].queryset = Servico.objects.filter(
            ativo=True
        )
        self.fields["barbeiro"].queryset = Barbeiro.objects.filter(
            ativo=True
        )

        # Adiciona classes de estilização
        self.fields["servico"].widget.attrs.update(
            {"class": "form-select"}
        )
        self.fields["barbeiro"].widget.attrs.update(
            {"class": "form-select"}
        )

    def clean(self):
        cleaned_data = super().clean()

        data = cleaned_data.get("data")
        hora_inicio = cleaned_data.get("hora_inicio")
        barbeiro = cleaned_data.get("barbeiro")
        servico = cleaned_data.get("servico")

        # Só prossegue com validações complexas se todos os campos essenciais
        # estiverem presentes e não tiverem falhado em validações básicas de campo.
        if data and hora_inicio and barbeiro and servico:
            # 1. Validação: Não permitir agendamentos no passado (data ou hora)
            # Converte o datetime do agendamento para ser timezone-aware para comparação
            agendamento_datetime = timezone.make_aware(datetime.combine(data, hora_inicio))
            now = timezone.localtime() # Pega o datetime local atual (timezone-aware)

            if agendamento_datetime < now:
                self.add_error("data", "Não é possível agendar para o passado.")
                self.add_error("hora_inicio", "Não é possível agendar para o passado.")
                # Se a data/hora está no passado, não há necessidade de verificar disponibilidade
                return cleaned_data

            # 2. Validação: Usar calcular_horarios_livres para verificar disponibilidade
            # Esta verificação implicitamente também lida com horários passados no dia atual,
            # pois a função `calcular_horarios_livres` os filtra.
            horarios_disponiveis = calcular_horarios_livres(
                barbeiro=barbeiro,
                servico=servico,
                data_agendamento=data
            )

            if hora_inicio not in horarios_disponiveis:
                self.add_error(
                    "hora_inicio",
                    "O horário selecionado não está disponível para este barbeiro e serviço."
                )
                # Opcionalmente, você poderia adicionar um erro também a 'barbeiro' ou 'servico'
                # self.add_error("barbeiro", "Barbeiro não disponível neste horário.")

        return cleaned_data


class AgendamentoAdminForm(forms.ModelForm):
    """Formulário utilizado pela equipe para editar um agendamento."""

    class Meta:
        model = Agendamento
        fields = [
            "cliente",
            "servico",
            "barbeiro",
            "data",
            "hora_inicio",
            "hora_fim",
            "status",
        ]

        widgets = {
            "data": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                    "class": "form-control",
                },
            ),
            "hora_inicio": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "type": "time",
                    "class": "form-control",
                },
            ),
            "hora_fim": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "type": "time",
                    "class": "form-control",
                },
            ),
            "cliente": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "servico": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "barbeiro": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data"].input_formats = ["%Y-%m-%d"]
        self.fields["hora_inicio"].input_formats = ["%H:%M"]
        self.fields["hora_fim"].input_formats = ["%H:%M"]

        # Se o AgendamentoAdminForm também precisar filtrar serviços/barbeiros ativos,
        # adicione os querysets aqui, similar ao AgendamentoForm.
        # self.fields["servico"].queryset = Servico.objects.filter(ativo=True)
        # self.fields["barbeiro"].queryset = Barbeiro.objects.filter(ativo=True)