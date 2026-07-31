"""Formulário de criação de agendamento."""

from django import forms

from apps.profissionais.models import Barbeiro
from apps.servicos.models import Servico

from .models import Agendamento


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

        self.fields["servico"].queryset = Servico.objects.filter(
            ativo=True
        )
        self.fields["barbeiro"].queryset = Barbeiro.objects.filter(
            ativo=True
        )

        self.fields["servico"].widget.attrs.update(
            {"class": "form-select"}
        )
        self.fields["barbeiro"].widget.attrs.update(
            {"class": "form-select"}
        )


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