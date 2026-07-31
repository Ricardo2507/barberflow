"""Views do app de agendamentos."""

from datetime import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.profissionais.models import Barbeiro
from apps.servicos.models import Servico

from . import emails
from .forms import AgendamentoAdminForm, AgendamentoForm
from .models import Agendamento
from .services import calcular_horarios_livres


def agendar(request):
    """Renderiza a tela principal de agendamento."""

    contexto = {
        "servicos": Servico.objects.filter(ativo=True),
        "barbeiros": (
            Barbeiro.objects
            .filter(ativo=True)
            .select_related("usuario")
        ),
        "data_minima": timezone.localdate(),
    }

    return render(
        request,
        "agendamentos/agendar.html",
        contexto,
    )


def horarios_disponiveis(request):
    """Retorna os horarios disponiveis para o formulario HTMX."""

    servico_id = request.GET.get("servico")
    barbeiro_id = request.GET.get("barbeiro")
    data_texto = request.GET.get("data")

    if not servico_id or not barbeiro_id or not data_texto:
        return HttpResponse(
            '<div class="alert alert-info">'
            "Selecione o servico, o barbeiro e a data."
            "</div>"
        )

    servico = get_object_or_404(
        Servico,
        pk=servico_id,
        ativo=True,
    )

    barbeiro = get_object_or_404(
        Barbeiro,
        pk=barbeiro_id,
        ativo=True,
    )

    try:
        data_agendamento = datetime.strptime(
            data_texto,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        return HttpResponse(
            '<div class="alert alert-danger">'
            "Data invalida."
            "</div>"
        )

    horarios = calcular_horarios_livres(
        barbeiro=barbeiro,
        servico=servico,
        data_agendamento=data_agendamento,
    )

    return render(
        request,
        "agendamentos/_horarios_disponiveis.html",
        {"horarios": horarios},
    )


@login_required
def criar_agendamento(request):
    """Processa o envio do formulario e cria um agendamento."""

    if request.method != "POST":
        return redirect("agendamentos:agendar")

    form = AgendamentoForm(request.POST)

    if not form.is_valid():
        for erros in form.errors.values():
            for erro in erros:
                messages.error(request, erro)

        return redirect("agendamentos:agendar")

    agendamento = form.save(commit=False)
    agendamento.cliente = request.user

    try:
        agendamento.save()
    except ValidationError as erro:
        if hasattr(erro, "message_dict"):
            for mensagens in erro.message_dict.values():
                for mensagem in mensagens:
                    messages.error(request, mensagem)
        else:
            messages.error(request, erro.message)

        return redirect("agendamentos:agendar")

    emails.notificar_criacao_para_cliente(agendamento)
    emails.notificar_criacao_para_barbeiro(agendamento)

    messages.success(
        request,
        "Agendamento realizado com sucesso!",
    )

    return redirect(
        "agendamentos:confirmacao",
        pk=agendamento.pk,
    )


@login_required
def confirmacao(request, pk):
    """Exibe os detalhes do agendamento recem-criado."""

    agendamento = get_object_or_404(
        Agendamento.objects.select_related(
            "cliente",
            "servico",
            "barbeiro__usuario",
        ),
        pk=pk,
    )

    usuario = request.user

    e_dono = agendamento.cliente_id == usuario.id
    e_equipe = usuario.is_staff

    e_barbeiro_responsavel = (
        hasattr(usuario, "perfil_barbeiro")
        and agendamento.barbeiro_id == usuario.perfil_barbeiro.id
    )

    if not (e_dono or e_equipe or e_barbeiro_responsavel):
        raise PermissionDenied(
            "Voce nao tem permissao para ver este agendamento."
        )

    return render(
        request,
        "agendamentos/confirmacao.html",
        {"agendamento": agendamento},
    )


@login_required
def meus_agendamentos(request):
    """Exibe somente os agendamentos do cliente logado."""

    agendamentos = (
        Agendamento.objects
        .filter(cliente=request.user)
        .select_related(
            "barbeiro__usuario",
            "servico",
        )
        .order_by("-data", "-hora_inicio")
    )

    return render(
        request,
        "agendamentos/meus_agendamentos.html",
        {
            "agendamentos": agendamentos,
            "hoje": timezone.localdate(),
        },
    )


@login_required
def meus_atendimentos(request):
    """Exibe somente os atendimentos do barbeiro logado."""

    if not hasattr(request.user, "perfil_barbeiro"):
        raise PermissionDenied(
            "Apenas barbeiros podem acessar esta pagina."
        )

    agendamentos = (
        Agendamento.objects
        .filter(barbeiro=request.user.perfil_barbeiro)
        .select_related(
            "cliente",
            "servico",
        )
        .order_by("-data", "-hora_inicio")
    )

    return render(
        request,
        "agendamentos/meus_atendimentos.html",
        {
            "agendamentos": agendamentos,
            "hoje": timezone.localdate(),
        },
    )


def _inicio_do_agendamento(agendamento):
    """Monta uma data/hora com fuso para o inicio do agendamento."""

    inicio = datetime.combine(
        agendamento.data,
        agendamento.hora_inicio,
    )

    if timezone.is_naive(inicio):
        inicio = timezone.make_aware(
            inicio,
            timezone.get_current_timezone(),
        )

    return inicio


@login_required
@require_POST
def cancelar_meu_agendamento(request, pk):
    """Permite que o cliente cancele o proprio agendamento."""

    agendamento = get_object_or_404(
        Agendamento.objects.select_related(
            "cliente",
            "servico",
            "barbeiro__usuario",
        ),
        pk=pk,
        cliente=request.user,
    )

    status_cancelado = getattr(
        Agendamento.Status,
        "CANCELADO",
        "CANCELADO",
    )

    status_concluido = getattr(
        Agendamento.Status,
        "CONCLUIDO",
        "CONCLUIDO",
    )

    if agendamento.status in {
        status_cancelado,
        status_concluido,
    }:
        messages.error(
            request,
            "Este agendamento nao pode mais ser cancelado.",
        )
        return redirect("agendamentos:meus_agendamentos")

    inicio = _inicio_do_agendamento(agendamento)
    agora = timezone.now()

    if inicio <= agora:
        messages.error(
            request,
            "Nao e possivel cancelar um agendamento que ja comecou.",
        )
        return redirect("agendamentos:meus_agendamentos")

    Agendamento.objects.filter(
        pk=agendamento.pk,
        cliente=request.user,
    ).update(
        status=status_cancelado,
    )

    emails.notificar_cancelamento_para_cliente(agendamento)
    emails.notificar_cancelamento_para_barbeiro(agendamento)

    messages.success(
        request,
        "Agendamento cancelado com sucesso.",
    )

    return redirect("agendamentos:meus_agendamentos")


@login_required
def alterar_meu_agendamento(request, pk):
    """Permite que o cliente altere o proprio agendamento."""

    agendamento = get_object_or_404(
        Agendamento,
        pk=pk,
        cliente=request.user,
    )

    status_cancelado = getattr(
        Agendamento.Status,
        "CANCELADO",
        "CANCELADO",
    )

    status_concluido = getattr(
        Agendamento.Status,
        "CONCLUIDO",
        "CONCLUIDO",
    )

    if agendamento.status in {
        status_cancelado,
        status_concluido,
    }:
        messages.error(
            request,
            "Este agendamento nao pode mais ser alterado.",
        )
        return redirect("agendamentos:meus_agendamentos")

    inicio = _inicio_do_agendamento(agendamento)
    agora = timezone.now()

    if inicio <= agora:
        messages.error(
            request,
            "Nao e possivel alterar um agendamento que ja comecou.",
        )
        return redirect("agendamentos:meus_agendamentos")

    if request.method == "POST":
        form = AgendamentoForm(
            request.POST,
            instance=agendamento,
        )

        if form.is_valid():
            novo_agendamento = form.save(commit=False)
            novo_agendamento.cliente = request.user

            novo_agendamento.status = getattr(
                Agendamento.Status,
                "PENDENTE",
                "PENDENTE",
            )

            try:
                novo_agendamento.save()
            except ValidationError as erro:
                if hasattr(erro, "message_dict"):
                    for campo, mensagens in erro.message_dict.items():
                        for mensagem in mensagens:
                            if campo == "__all__":
                                form.add_error(None, mensagem)
                            else:
                                form.add_error(campo, mensagem)
                else:
                    form.add_error(None, str(erro))
            else:
                emails.notificar_alteracao_para_barbeiro(
                    novo_agendamento
                )

                messages.success(
                    request,
                    "Agendamento alterado. Aguarde a confirmacao da equipe.",
                )
                return redirect("agendamentos:meus_agendamentos")
    else:
        form = AgendamentoForm(instance=agendamento)

    return render(
        request,
        "agendamentos/alterar.html",
        {
            "form": form,
            "agendamento": agendamento,
        },
    )


@staff_member_required
def painel_agendamentos(request):
    """Exibe todos os agendamentos para usuarios da equipe."""

    agendamentos = (
        Agendamento.objects
        .select_related(
            "cliente",
            "servico",
            "barbeiro",
        )
        .all()
        .order_by("-data", "-hora_inicio")
    )

    return render(
        request,
        "agendamentos/painel.html",
        {"agendamentos": agendamentos},
    )


@staff_member_required
@require_POST
def confirmar_agendamento(request, pk):
    """Confirma um agendamento sem validar novamente data e horario."""

    agendamento = get_object_or_404(
        Agendamento.objects.select_related(
            "cliente",
            "servico",
            "barbeiro__usuario",
        ),
        pk=pk,
    )

    status_confirmado = getattr(
        Agendamento.Status,
        "CONFIRMADO",
        "CONFIRMADO",
    )

    Agendamento.objects.filter(
        pk=agendamento.pk,
    ).update(
        status=status_confirmado,
    )

    emails.notificar_confirmacao_para_cliente(agendamento)

    messages.success(
        request,
        "Agendamento confirmado com sucesso.",
    )

    return redirect("agendamentos:painel")


@staff_member_required
@require_POST
def cancelar_agendamento(request, pk):
    """Cancela um agendamento sem validar novamente data e horario."""

    agendamento = get_object_or_404(
        Agendamento.objects.select_related(
            "cliente",
            "servico",
            "barbeiro__usuario",
        ),
        pk=pk,
    )

    status_cancelado = getattr(
        Agendamento.Status,
        "CANCELADO",
        "CANCELADO",
    )

    Agendamento.objects.filter(
        pk=agendamento.pk,
    ).update(
        status=status_cancelado,
    )

    emails.notificar_cancelamento_para_cliente(agendamento)
    emails.notificar_cancelamento_para_barbeiro(agendamento)

    messages.warning(
        request,
        "Agendamento cancelado.",
    )

    return redirect("agendamentos:painel")


@staff_member_required
def editar_agendamento(request, pk):
    """Permite que a equipe edite um agendamento."""

    agendamento = get_object_or_404(
        Agendamento,
        pk=pk,
    )

    if request.method == "POST":
        form = AgendamentoAdminForm(
            request.POST,
            instance=agendamento,
        )

        if form.is_valid():
            try:
                form.save()
            except ValidationError as erro:
                if hasattr(erro, "message_dict"):
                    for campo, mensagens in erro.message_dict.items():
                        for mensagem in mensagens:
                            if campo == "__all__":
                                form.add_error(None, mensagem)
                            else:
                                form.add_error(campo, mensagem)
                else:
                    form.add_error(None, str(erro))
            else:
                messages.success(
                    request,
                    "Agendamento alterado com sucesso.",
                )
                return redirect("agendamentos:painel")
    else:
        form = AgendamentoAdminForm(
            instance=agendamento,
        )

    return render(
        request,
        "agendamentos/editar.html",
        {
            "form": form,
            "agendamento": agendamento,
        },
    )