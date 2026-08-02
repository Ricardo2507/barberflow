"""Views do app de agendamentos."""

from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.profissionais.models import Barbeiro
from apps.servicos.models import Servico

# Removendo a importação do módulo 'emails' para substituí-lo
# from . import emails

from .forms import AgendamentoAdminForm, AgendamentoForm
from .models import Agendamento
from .services import calcular_horarios_livres

# Importe a função utilitária que acabamos de criar
from apps.core.utils import enviar_email_async


# ============================================================================
# Funções auxiliares
# ============================================================================


def _inicio_do_agendamento(agendamento):
    """
    Combina a data e o horário de início do agendamento
    em um datetime com timezone.
    """

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


def _status_agendamento():
    """
    Centraliza os status utilizados nas views.
    """

    return {
        "pendente": Agendamento.Status.PENDENTE,
        "confirmado": Agendamento.Status.CONFIRMADO,
        "cancelado": Agendamento.Status.CANCELADO,
        "concluido": Agendamento.Status.CONCLUIDO,
    }


def _usuario_e_administrador(user):
    """
    Define quem pode acessar o painel geral.

    O usuário precisa ser superusuário ou pertencer ao grupo
    'Administradores'.

    Um barbeiro com is_staff=True não terá acesso ao painel,
    a menos que também esteja no grupo Administradores.
    """

    if not user.is_authenticated:
        return False

    return (
        user.is_superuser
        or user.groups.filter(name="Administradores").exists()
    )


def _usuario_e_barbeiro(user):
    """
    Verifica se o usuário possui um cadastro de barbeiro.
    """

    if not user.is_authenticated:
        return False

    return Barbeiro.objects.filter(
        usuario_id=user.pk,
    ).exists()


def _usuario_pode_operar_agendamento(user, agendamento):
    """
    Verifica se o usuário pode confirmar ou finalizar o agendamento.

    Administradores podem operar qualquer agendamento.

    Barbeiros podem operar somente os agendamentos vinculados
    ao próprio perfil.
    """

    if _usuario_e_administrador(user):
        return True

    return (
        agendamento.barbeiro_id is not None
        and agendamento.barbeiro.usuario_id == user.pk
    )


def _adicionar_erros_de_validacao(request, erro):
    """
    Envia os erros de ValidationError para o sistema de mensagens.
    """

    if hasattr(erro, "message_dict"):
        for mensagens in erro.message_dict.values():
            for mensagem in mensagens:
                messages.error(request, mensagem)
    else:
        messages.error(request, str(erro))


# ============================================================================
# Área pública de agendamento
# ============================================================================


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
    """Retorna os horários disponíveis para o formulário HTMX."""

    servico_id = request.GET.get("servico")
    barbeiro_id = request.GET.get("barbeiro")
    data_texto = request.GET.get("data")

    if not servico_id or not barbeiro_id or not data_texto:
        return HttpResponse(
            '<div class="alert alert-info">'
            "Selecione o serviço, o barbeiro e a data."
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
            "Data inválida."
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
        {
            "horarios": horarios,
        },
    )


@login_required
@require_POST
def criar_agendamento(request):
    """Processa o envio do formulário e cria um agendamento."""

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
        _adicionar_erros_de_validacao(request, erro)
        return redirect("agendamentos:agendar")

    # --- Substituição das chamadas de e-mail síncronas por assíncronas ---
    # Notificação para o cliente
    enviar_email_async(
        subject="Seu agendamento no BarberFlow foi confirmado!",
        message=(
            f"Olá, {agendamento.cliente.get_full_name() or agendamento.cliente.username}!\n\n"
            "Seu agendamento foi confirmado com sucesso.\n\n"
            f"Detalhes do Agendamento:\n"
            f"Serviço: {agendamento.servico.nome}\n"
            f"Barbeiro: {agendamento.barbeiro.usuario.get_full_name() or agendamento.barbeiro.usuario.username}\n"
            f"Data: {agendamento.data.strftime('%d/%m/%Y')}\n"
            f"Horário: {agendamento.hora_inicio.strftime('%H:%M')}\n\n"
            "Aguardamos você!"
        ),
        recipient_list=[agendamento.cliente.email],
    )

    # Notificação para o barbeiro
    enviar_email_async(
        subject=f"Novo agendamento para você: {agendamento.servico.nome}",
        message=(
            f"Olá, {agendamento.barbeiro.usuario.get_full_name() or agendamento.barbeiro.usuario.username}!\n\n"
            "Você tem um novo agendamento:\n\n"
            f"Cliente: {agendamento.cliente.get_full_name() or agendamento.cliente.username}\n"
            f"Serviço: {agendamento.servico.nome}\n"
            f"Data: {agendamento.data.strftime('%d/%m/%Y')}\n"
            f"Horário: {agendamento.hora_inicio.strftime('%H:%M')}\n\n"
            "Verifique seus agendamentos no painel."
        ),
        recipient_list=[agendamento.barbeiro.usuario.email],
    )
    # --- Fim da substituição ---

    messages.success(
        request,
        "Agendamento realizado com sucesso. Um e-mail de confirmação foi enviado.",
    )

    # return redirect(
    #     "agendamentos:confirmacao",
    #     pk=agendamento.pk,
    # )
    return redirect("agendamentos:meus_agendamentos") 

# ============================================================================
# Visualização de agendamento
# ============================================================================


@login_required
def confirmacao(request, pk):
    """Exibe os detalhes de um agendamento autorizado."""

    agendamento = get_object_or_404(
        Agendamento.objects.select_related(
            "cliente",
            "servico",
            "barbeiro__usuario",
        ),
        pk=pk,
    )

    usuario = request.user

    e_cliente = agendamento.cliente_id == usuario.pk
    e_administrador = _usuario_e_administrador(usuario)

    e_barbeiro = (
        agendamento.barbeiro_id is not None
        and agendamento.barbeiro.usuario_id == usuario.pk
    )

    if not (e_cliente or e_administrador or e_barbeiro):
        raise PermissionDenied(
            "Você não tem permissão para visualizar este agendamento."
        )

    return render(
        request,
        "agendamentos/confirmacao.html",
        {
            "agendamento": agendamento,
        },
    )


# ============================================================================
# Área do cliente — Meus Agendamentos
# ============================================================================


@login_required
def meus_agendamentos(request):
    """
    Exibe somente os agendamentos em que o usuário logado
    é o cliente.
    """

    agendamentos_qs = (
        Agendamento.objects
        .filter(cliente_id=request.user.pk)
        .select_related(
            "cliente",
            "servico",
            "barbeiro__usuario",
        )
        .order_by("-data", "-hora_inicio")
    )

    status = _status_agendamento()
    agora = timezone.localtime()
    antecedencia_minima = timedelta(hours=1)

    agendamentos = []

    for agendamento in agendamentos_qs:
        pode_gerenciar = True
        motivo_nao_gerenciavel = ""

        if agendamento.status in {
            status["cancelado"],
            status["concluido"],
        }:
            pode_gerenciar = False
            motivo_nao_gerenciavel = (
                "Este agendamento não pode mais ser alterado ou cancelado."
            )
        else:
            inicio = _inicio_do_agendamento(agendamento)

            if inicio <= agora:
                pode_gerenciar = False
                motivo_nao_gerenciavel = (
                    "O agendamento já começou ou já passou."
                )
            elif inicio - agora < antecedencia_minima:
                pode_gerenciar = False
                motivo_nao_gerenciavel = (
                    "É necessário ter pelo menos 1 hora de antecedência."
                )

        agendamentos.append(
            {
                "agendamento": agendamento,
                "pode_gerenciar": pode_gerenciar,
                "motivo_nao_gerenciavel": motivo_nao_gerenciavel,
            }
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
@require_POST
def cancelar_meu_agendamento(request, pk):
    """
    Permite que o cliente cancele somente o próprio agendamento.

    Regras:
    - O cliente deve ser o proprietário.
    - O status não pode ser CANCELADO ou CONCLUIDO.
    - O agendamento ainda não pode ter começado.
    - Deve haver pelo menos 1 hora de antecedência.
    """

    agendamento = get_object_or_404(
        Agendamento.objects.select_related(
            "cliente",
            "servico",
            "barbeiro__usuario",
        ),
        pk=pk,
        cliente_id=request.user.pk,
    )

    status = _status_agendamento()

    if agendamento.status in {
        status["cancelado"],
        status["concluido"],
    }:
        messages.error(
            request,
            "Este agendamento não pode mais ser cancelado.",
        )
        return redirect("agendamentos:meus_agendamentos")

    inicio = _inicio_do_agendamento(agendamento)
    agora = timezone.localtime()

    if inicio <= agora:
        messages.error(
            request,
            "Não é possível cancelar um agendamento que já começou ou passou.",
        )
        return redirect("agendamentos:meus_agendamentos")

    if inicio - agora < timedelta(hours=1):
        messages.error(
            request,
            "Não é possível cancelar com menos de 1 hora de antecedência.",
        )
        return redirect("agendamentos:meus_agendamentos")

    with transaction.atomic():
        atualizado = (
            Agendamento.objects
            .select_for_update()
            .filter(
                pk=agendamento.pk,
                cliente_id=request.user.pk,
                status__in=[
                    status["pendente"],
                    status["confirmado"],
                ],
            )
            .update(
                status=status["cancelado"],
            )
        )

    if not atualizado:
        messages.error(
            request,
            "O agendamento não pôde ser cancelado porque foi alterado.",
        )
        return redirect("agendamentos:meus_agendamentos")

    # --- Substituição das chamadas de e-mail síncronas por assíncronas ---
    # Notificação para o cliente
    enviar_email_async(
        subject="Seu agendamento no BarberFlow foi cancelado.",
        message=(
            f"Olá, {agendamento.cliente.get_full_name() or agendamento.cliente.username}!\n\n"
            "Seu agendamento foi cancelado com sucesso.\n\n"
            f"Detalhes do Agendamento:\n"
            f"Serviço: {agendamento.servico.nome}\n"
            f"Barbeiro: {agendamento.barbeiro.usuario.get_full_name() or agendamento.barbeiro.usuario.username}\n"
            f"Data: {agendamento.data.strftime('%d/%m/%Y')}\n"
            f"Horário: {agendamento.hora_inicio.strftime('%H:%M')}\n\n"
            "Esperamos vê-lo em breve!"
        ),
        recipient_list=[agendamento.cliente.email],
    )

    # Notificação para o barbeiro
    enviar_email_async(
        subject=f"Agendamento cancelado: {agendamento.servico.nome}",
        message=(
            f"Olá, {agendamento.barbeiro.usuario.get_full_name() or agendamento.barbeiro.usuario.username}!\n\n"
            "Um agendamento foi cancelado:\n\n"
            f"Cliente: {agendamento.cliente.get_full_name() or agendamento.cliente.username}\n"
            f"Serviço: {agendamento.servico.nome}\n"
            f"Data: {agendamento.data.strftime('%d/%m/%Y')}\n"
            f"Horário: {agendamento.hora_inicio.strftime('%H:%M')}\n\n"
            "Verifique seus agendamentos no painel."
        ),
        recipient_list=[agendamento.barbeiro.usuario.email],
    )
    # --- Fim da substituição ---

    messages.success(
        request,
        "Agendamento cancelado com sucesso.",
    )

    return redirect("agendamentos:meus_agendamentos")


@login_required
def alterar_meu_agendamento(request, pk):
    """
    Permite que o cliente altere somente o próprio agendamento.
    """

    agendamento = get_object_or_404(
        Agendamento.objects.select_related(
            "cliente",
            "servico",
            "barbeiro__usuario",
        ),
        pk=pk,
        cliente_id=request.user.pk,
    )

    status = _status_agendamento()

    if agendamento.status in {
        status["cancelado"],
        status["concluido"],
    }:
        messages.error(
            request,
            "Este agendamento não pode mais ser alterado.",
        )
        return redirect("agendamentos:meus_agendamentos")

    inicio = _inicio_do_agendamento(agendamento)
    agora = timezone.localtime()

    if inicio <= agora:
        messages.error(
            request,
            "Não é possível alterar um agendamento que já começou ou passou.",
        )
        return redirect("agendamentos:meus_agendamentos")

    if inicio - agora < timedelta(hours=1):
        messages.error(
            request,
            "Não é possível alterar com menos de 1 hora de antecedência.",
        )
        return redirect("agendamentos:meus_agendamentos")

    if request.method == "POST":
        form = AgendamentoForm(
            request.POST,
            instance=agendamento,
        )

        if form.is_valid():
            try:
                form.save()
            except ValidationError as erro:
                _adicionar_erros_de_validacao(request, erro)
            else:
                # --- Notificação de alteração para o cliente e barbeiro ---
                enviar_email_async(
                    subject="Seu agendamento no BarberFlow foi alterado!",
                    message=(
                        f"Olá, {agendamento.cliente.get_full_name() or agendamento.cliente.username}!\n\n"
                        "Seu agendamento foi alterado com sucesso.\n\n"
                        f"Novos Detalhes do Agendamento:\n"
                        f"Serviço: {agendamento.servico.nome}\n"
                        f"Barbeiro: {agendamento.barbeiro.usuario.get_full_name() or agendamento.barbeiro.usuario.username}\n"
                        f"Data: {agendamento.data.strftime('%d/%m/%Y')}\n"
                        f"Horário: {agendamento.hora_inicio.strftime('%H:%M')}\n\n"
                        "Aguardamos você!"
                    ),
                    recipient_list=[agendamento.cliente.email],
                )

                enviar_email_async(
                    subject=f"Agendamento alterado: {agendamento.servico.nome}",
                    message=(
                        f"Olá, {agendamento.barbeiro.usuario.get_full_name() or agendamento.barbeiro.usuario.username}!\n\n"
                        "Um agendamento foi alterado:\n\n"
                        f"Cliente: {agendamento.cliente.get_full_name() or agendamento.cliente.username}\n"
                        f"Serviço: {agendamento.servico.nome}\n"
                        f"Nova Data: {agendamento.data.strftime('%d/%m/%Y')}\n"
                        f"Novo Horário: {agendamento.hora_inicio.strftime('%H:%M')}\n\n"
                        "Verifique seus agendamentos no painel."
                    ),
                    recipient_list=[agendamento.barbeiro.usuario.email],
                )
                # --- Fim da notificação ---

                messages.success(
                    request,
                    "Agendamento alterado com sucesso.",
                )
                return redirect("agendamentos:meus_agendamentos")
    else:
        form = AgendamentoForm(
            instance=agendamento,
        )

    return render(
        request,
        "agendamentos/editar_meu_agendamento.html",
        {
            "form": form,
            "agendamento": agendamento,
        },
    )


# ============================================================================
# Área do barbeiro — Meus Atendimentos
# ============================================================================


@login_required
@user_passes_test(
    _usuario_e_barbeiro,
    login_url="core:home",  # Redireciona para a home se não for barbeiro
)
def meus_atendimentos(request):
    """
    Exibe somente os atendimentos atribuídos ao barbeiro logado.
    """

    barbeiro = (
        Barbeiro.objects
        .filter(usuario_id=request.user.pk)
        .first()
    )

    # Este if é redundante devido ao user_passes_test, mas mantém a clareza
    if barbeiro is None:
        raise PermissionDenied(
            "O usuário logado não possui um perfil de barbeiro."
        )

    agendamentos_qs = (
        Agendamento.objects
        .filter(barbeiro_id=barbeiro.pk)
        .select_related(
            "cliente",
            "servico",
            "barbeiro__usuario",
        )
        .order_by("-data", "-hora_inicio")
    )

    status = _status_agendamento()
    agora = timezone.localtime()
    agendamentos = []

    for agendamento in agendamentos_qs:
        inicio = _inicio_do_agendamento(agendamento)

        pode_confirmar = (
            agendamento.status == status["pendente"]
            and inicio > agora
        )

        pode_finalizar = (
            agendamento.status in {
                status["pendente"],
                status["confirmado"],
            }
            and inicio <= agora
        )

        agendamentos.append(
            {
                "agendamento": agendamento,
                "pode_confirmar": pode_confirmar,
                "pode_finalizar": pode_finalizar,
            }
        )

    return render(
        request,
        "agendamentos/meus_atendimentos.html",
        {
            "agendamentos": agendamentos,
            "hoje": timezone.localdate(),
        },
    )


# ============================================================================
# Painel administrativo
# ============================================================================


@user_passes_test(
    _usuario_e_administrador,
    login_url="agendamentos:meus_atendimentos",
)
def painel_agendamentos(request):
    """
    Exibe todos os agendamentos somente para administradores.

    Barbeiros comuns não possuem acesso a esta página.
    """

    # Esta queryset já busca TODOS os agendamentos, sem filtros por usuário.
    agendamentos_qs = (
        Agendamento.objects
        .select_related(
            "cliente",
            "servico",
            "barbeiro__usuario",
        )
        .order_by("-data", "-hora_inicio")
    )

    status = _status_agendamento()
    agora = timezone.localtime()

    agendamentos = []

    for agendamento in agendamentos_qs:
        inicio = _inicio_do_agendamento(agendamento)

        pode_confirmar = (
            agendamento.status == status["pendente"]
            and inicio > agora
        )

        pode_finalizar = (
            agendamento.status in {
                status["pendente"],
                status["confirmado"],
            }
            and inicio <= agora
        )

        pode_cancelar_admin = agendamento.status not in {
            status["cancelado"],
            status["concluido"],
        }

        agendamentos.append(
            {
                "agendamento": agendamento,
                "pode_confirmar": pode_confirmar,
                "pode_finalizar": pode_finalizar,
                "pode_cancelar_admin": pode_cancelar_admin,
            }
        )

    return render(
        request,
        "agendamentos/painel.html",
        {
            "agendamentos": agendamentos,
        },
    )

# ============================================================================
# Ações do barbeiro e do administrador
# ============================================================================


@login_required
@require_POST
def confirmar_agendamento(request, pk):
    """
    Confirma um agendamento pendente e futuro.

    Pode ser executado por:
    - administrador;
    - barbeiro responsável pelo atendimento.
    """

    with transaction.atomic():
        agendamento = get_object_or_404(
            Agendamento.objects
            .select_for_update()
            .select_related(
                "cliente",
                "servico",
                "barbeiro__usuario",
            ),
            pk=pk,
        )

        if not _usuario_pode_operar_agendamento(
            request.user,
            agendamento,
        ):
            raise PermissionDenied(
                "Você não pode confirmar este agendamento."
            )

        status = _status_agendamento()

        if agendamento.status != status["pendente"]:
            messages.error(
                request,
                "Somente agendamentos pendentes podem ser confirmados.",
            )
            # Redireciona para o painel se for admin, senão para meus_atendimentos
            if _usuario_e_administrador(request.user):
                return redirect("agendamentos:painel")
            return redirect("agendamentos:meus_atendimentos")

        inicio = _inicio_do_agendamento(agendamento)

        if inicio <= timezone.localtime():
            messages.error(
                request,
                "Não é possível confirmar um agendamento que já começou ou passou.",
            )
            # Redireciona para o painel se for admin, senão para meus_atendimentos
            if _usuario_e_administrador(request.user):
                return redirect("agendamentos:painel")
            return redirect("agendamentos:meus_atendimentos")

        agendamento.status = status["confirmado"]
        agendamento.save(update_fields=["status"])

    # --- Notificação de confirmação para o cliente e barbeiro ---
    enviar_email_async(
        subject="Seu agendamento no BarberFlow foi confirmado!",
        message=(
            f"Olá, {agendamento.cliente.get_full_name() or agendamento.cliente.username}!\n\n"
            "Seu agendamento foi confirmado pela equipe.\n\n"
            f"Detalhes do Agendamento:\n"
            f"Serviço: {agendamento.servico.nome}\n"
            f"Barbeiro: {agendamento.barbeiro.usuario.get_full_name() or agendamento.barbeiro.usuario.username}\n"
            f"Data: {agendamento.data.strftime('%d/%m/%Y')}\n"
            f"Horário: {agendamento.hora_inicio.strftime('%H:%M')}\n\n"
            "Aguardamos você!"
        ),
        recipient_list=[agendamento.cliente.email],
    )

    enviar_email_async(
        subject=f"Agendamento confirmado: {agendamento.servico.nome}",
        message=(
            f"Olá, {agendamento.barbeiro.usuario.get_full_name() or agendamento.barbeiro.usuario.username}!\n\n"
            "Um agendamento foi confirmado:\n\n"
            f"Cliente: {agendamento.cliente.get_full_name() or agendamento.cliente.username}\n"
            f"Serviço: {agendamento.servico.nome}\n"
            f"Data: {agendamento.data.strftime('%d/%m/%Y')}\n"
            f"Horário: {agendamento.hora_inicio.strftime('%H:%M')}\n\n"
            "Verifique seus agendamentos no painel."
        ),
        recipient_list=[agendamento.barbeiro.usuario.email],
    )
    # --- Fim da notificação ---

    messages.success(
        request,
        "Agendamento confirmado com sucesso.",
    )

    if _usuario_e_administrador(request.user):
        return redirect("agendamentos:painel")

    return redirect("agendamentos:meus_atendimentos")


@login_required
@require_POST
def finalizar_agendamento(request, pk):
    """
    Finaliza um agendamento que já começou.

    Pode ser executado pelo administrador ou pelo barbeiro responsável.
    """

    with transaction.atomic():
        agendamento = get_object_or_404(
            Agendamento.objects
            .select_for_update()
            .select_related(
                "cliente",
                "servico",
                "barbeiro__usuario",
            ),
            pk=pk,
        )

        if not _usuario_pode_operar_agendamento(
            request.user,
            agendamento,
        ):
            raise PermissionDenied(
                "Você não pode finalizar este agendamento."
            )

        status = _status_agendamento()

        if agendamento.status not in {
            status["pendente"],
            status["confirmado"],
        }:
            messages.error(
                request,
                "Somente agendamentos pendentes ou confirmados podem ser finalizados.",
            )
            # Redireciona para o painel se for admin, senão para meus_atendimentos
            if _usuario_e_administrador(request.user):
                return redirect("agendamentos:painel")
            return redirect("agendamentos:meus_atendimentos")

        inicio = _inicio_do_agendamento(agendamento)

        if inicio > timezone.localtime():
            messages.error(
                request,
                "O agendamento ainda não começou.",
            )
            # Redireciona para o painel se for admin, senão para meus_atendimentos
            if _usuario_e_administrador(request.user):
                return redirect("agendamentos:painel")
            return redirect("agendamentos:meus_atendimentos")

        agendamento.status = status["concluido"]
        agendamento.save(update_fields=["status"])

    # --- Notificação de finalização para o cliente ---
    enviar_email_async(
        subject="Seu agendamento no BarberFlow foi concluído!",
        message=(
            f"Olá, {agendamento.cliente.get_full_name() or agendamento.cliente.username}!\n\n"
            "Seu agendamento foi concluído com sucesso. Esperamos que tenha gostado!\n\n"
            f"Detalhes do Agendamento:\n"
            f"Serviço: {agendamento.servico.nome}\n"
            f"Barbeiro: {agendamento.barbeiro.usuario.get_full_name() or agendamento.barbeiro.usuario.username}\n"
            f"Data: {agendamento.data.strftime('%d/%m/%Y')}\n"
            f"Horário: {agendamento.hora_inicio.strftime('%H:%M')}\n\n"
            "Volte sempre!"
        ),
        recipient_list=[agendamento.cliente.email],
    )
    # --- Fim da notificação ---

    messages.success(
        request,
        "Agendamento finalizado com sucesso.",
    )

    if _usuario_e_administrador(request.user):
        return redirect("agendamentos:painel")

    return redirect("agendamentos:meus_atendimentos")


@login_required
@require_POST
def cancelar_agendamento(request, pk):
    """
    Cancelamento administrativo.

    Somente administradores podem cancelar pela área administrativa.
    Barbeiros não podem cancelar pela tela Meus Atendimentos.
    """

    if not _usuario_e_administrador(request.user):
        raise PermissionDenied(
            "Somente administradores podem cancelar agendamentos por esta área."
        )

    with transaction.atomic():
        agendamento = get_object_or_404(
            Agendamento.objects
            .select_for_update()
            .select_related(
                "cliente",
                "servico",
                "barbeiro__usuario",
            ),
            pk=pk,
        )

        status = _status_agendamento()

        if agendamento.status == status["cancelado"]:
            messages.warning(
                request,
                "Este agendamento já está cancelado.",
            )
            return redirect("agendamentos:painel")

        if agendamento.status == status["concluido"]:
            messages.error(
                request,
                "Um agendamento concluído não pode ser cancelado.",
            )
            return redirect("agendamentos:painel")

        agendamento.status = status["cancelado"]
        agendamento.save(update_fields=["status"])

    # --- Notificação de cancelamento administrativo para o cliente e barbeiro ---
    enviar_email_async(
        subject="Seu agendamento no BarberFlow foi cancelado pela equipe.",
        message=(
            f"Olá, {agendamento.cliente.get_full_name() or agendamento.cliente.username}!\n\n"
            "Informamos que seu agendamento foi cancelado pela equipe do BarberFlow.\n\n"
            f"Detalhes do Agendamento:\n"
            f"Serviço: {agendamento.servico.nome}\n"
            f"Barbeiro: {agendamento.barbeiro.usuario.get_full_name() or agendamento.barbeiro.usuario.username}\n"
            f"Data: {agendamento.data.strftime('%d/%m/%Y')}\n"
            f"Horário: {agendamento.hora_inicio.strftime('%H:%M')}\n\n"
            "Por favor, entre em contato se tiver alguma dúvida."
        ),
        recipient_list=[agendamento.cliente.email],
    )

    enviar_email_async(
        subject=f"Agendamento cancelado administrativamente: {agendamento.servico.nome}",
        message=(
            f"Olá, {agendamento.barbeiro.usuario.get_full_name() or agendamento.barbeiro.usuario.username}!\n\n"
            "Um agendamento foi cancelado administrativamente:\n\n"
            f"Cliente: {agendamento.cliente.get_full_name() or agendamento.cliente.username}\n"
            f"Serviço: {agendamento.servico.nome}\n"
            f"Data: {agendamento.data.strftime('%d/%m/%Y')}\n"
            f"Horário: {agendamento.hora_inicio.strftime('%H:%M')}\n\n"
            "Verifique seus agendamentos no painel."
        ),
        recipient_list=[agendamento.barbeiro.usuario.email],
    )
    # --- Fim da notificação ---

    messages.warning(
        request,
        "Agendamento cancelado pela equipe.",
    )

    return redirect("agendamentos:painel")


# ============================================================================
# Edição administrativa
# ============================================================================


@user_passes_test(
    _usuario_e_administrador,
    login_url="agendamentos:meus_atendimentos",
)
def editar_agendamento(request, pk):
    """Permite que administradores editem agendamentos ativos."""

    agendamento = get_object_or_404(
        Agendamento.objects.select_related(
            "cliente",
            "servico",
            "barbeiro__usuario",
        ),
        pk=pk,
    )

    status = _status_agendamento()

    if agendamento.status in {
        status["cancelado"],
        status["concluido"],
    }:
        messages.error(
            request,
            "Agendamentos cancelados ou concluídos não podem ser alterados.",
        )
        return redirect("agendamentos:painel")

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
                # --- Notificação de alteração administrativa para o cliente e barbeiro ---
                enviar_email_async(
                    subject="Seu agendamento no BarberFlow foi alterado pela equipe.",
                    message=(
                        f"Olá, {agendamento.cliente.get_full_name() or agendamento.cliente.username}!\n\n"
                        "Informamos que seu agendamento foi alterado pela equipe do BarberFlow.\n\n"
                        f"Novos Detalhes do Agendamento:\n"
                        f"Serviço: {agendamento.servico.nome}\n"
                        f"Barbeiro: {agendamento.barbeiro.usuario.get_full_name() or agendamento.barbeiro.usuario.username}\n"
                        f"Data: {agendamento.data.strftime('%d/%m/%Y')}\n"
                        f"Horário: {agendamento.hora_inicio.strftime('%H:%M')}\n\n"
                        "Por favor, verifique os novos detalhes."
                    ),
                    recipient_list=[agendamento.cliente.email],
                )

                enviar_email_async(
                    subject=f"Agendamento alterado administrativamente: {agendamento.servico.nome}",
                    message=(
                        f"Olá, {agendamento.barbeiro.usuario.get_full_name() or agendamento.barbeiro.usuario.username}!\n\n"
                        "Um agendamento foi alterado administrativamente:\n\n"
                        f"Cliente: {agendamento.cliente.get_full_name() or agendamento.cliente.username}\n"
                        f"Serviço: {agendamento.servico.nome}\n"
                        f"Nova Data: {agendamento.data.strftime('%d/%m/%Y')}\n"
                        f"Novo Horário: {agendamento.hora_inicio.strftime('%H:%M')}\n\n"
                        "Verifique seus agendamentos no painel."
                    ),
                    recipient_list=[agendamento.barbeiro.usuario.email],
                )
                # --- Fim da notificação ---

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