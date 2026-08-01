"""Utilitários compartilhados do sistema."""

import logging
import threading
from collections.abc import Iterable

from django.conf import settings
from django.core.mail import send_mail


logger = logging.getLogger(__name__)


def _enviar_email_em_background(
    subject: str,
    message: str,
    from_email: str,
    recipient_list: list[str],
    fail_silently: bool,
) -> None:
    """Executa o envio do e-mail em segundo plano."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=fail_silently,
        )

        logger.info(
            "E-mail enviado com sucesso. Assunto: %s. Destinatários: %s",
            subject,
            recipient_list,
        )

    except Exception:
        logger.exception(
            "Erro ao enviar e-mail. Assunto: %s. Destinatários: %s",
            subject,
            recipient_list,
        )


def enviar_email_async(
    subject: str,
    message: str,
    recipient_list: Iterable[str],
    from_email: str | None = None,
    fail_silently: bool = True,
) -> None:
    """
    Dispara o envio do e-mail em uma thread separada.

    A função inicia a thread e retorna imediatamente para a View.
    """
    destinatarios = [
        email.strip()
        for email in recipient_list
        if email and email.strip()
    ]

    if not destinatarios:
        logger.warning(
            "E-mail não enviado: lista de destinatários vazia. Assunto: %s",
            subject,
        )
        return

    remetente = from_email or settings.DEFAULT_FROM_EMAIL

    email_thread = threading.Thread(
        target=_enviar_email_em_background,
        kwargs={
            "subject": subject,
            "message": message,
            "from_email": remetente,
            "recipient_list": destinatarios,
            "fail_silently": fail_silently,
        },
        daemon=True,
        name="barberflow-email",
    )

    email_thread.start()

    logger.info(
        "Envio assíncrono de e-mail disparado. Assunto: %s",
        subject,
    )