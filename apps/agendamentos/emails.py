"""Funcoes de envio de e-mail relacionadas a agendamentos."""

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def _enviar(destinatario, assunto, template, contexto):
    """Renderiza um template de texto e envia por e-mail."""

    if not destinatario:
        print(f"E-mail ignorado: destinatario vazio para '{assunto}'.")
        return

    corpo = render_to_string(template, contexto)

    send_mail(
        subject=assunto,
        message=corpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[destinatario],
        fail_silently=False,
    )


def notificar_criacao_para_cliente(agendamento):
    _enviar(
        destinatario=agendamento.cliente.email,
        assunto="BarberFlow - Agendamento recebido",
        template="agendamentos/emails/criacao_cliente.txt",
        contexto={"agendamento": agendamento},
    )


def notificar_criacao_para_barbeiro(agendamento):
    _enviar(
        destinatario=agendamento.barbeiro.usuario.email,
        assunto="BarberFlow - Novo agendamento",
        template="agendamentos/emails/criacao_barbeiro.txt",
        contexto={"agendamento": agendamento},
    )


def notificar_confirmacao_para_cliente(agendamento):
    _enviar(
        destinatario=agendamento.cliente.email,
        assunto="BarberFlow - Agendamento confirmado",
        template="agendamentos/emails/confirmacao_cliente.txt",
        contexto={"agendamento": agendamento},
    )


def notificar_cancelamento_para_cliente(agendamento):
    _enviar(
        destinatario=agendamento.cliente.email,
        assunto="BarberFlow - Agendamento cancelado",
        template="agendamentos/emails/cancelamento_cliente.txt",
        contexto={"agendamento": agendamento},
    )


def notificar_cancelamento_para_barbeiro(agendamento):
    _enviar(
        destinatario=agendamento.barbeiro.usuario.email,
        assunto="BarberFlow - Atendimento cancelado",
        template="agendamentos/emails/cancelamento_barbeiro.txt",
        contexto={"agendamento": agendamento},
    )


def notificar_alteracao_para_barbeiro(agendamento):
    _enviar(
        destinatario=agendamento.barbeiro.usuario.email,
        assunto="BarberFlow - Agendamento alterado pelo cliente",
        template="agendamentos/emails/alteracao_barbeiro.txt",
        contexto={"agendamento": agendamento},
    )