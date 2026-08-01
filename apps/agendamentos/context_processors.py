
def permissoes_agendamentos(request):
    """
    Disponibiliza as permissões de agendamentos nos templates.
    """

    usuario = request.user

    if not usuario.is_authenticated:
        return {
            "is_administrador": False,
            "e_barbeiro": False,
        }

    is_administrador = (
        usuario.is_superuser
        or usuario.groups.filter(
            name="Administradores"
        ).exists()
    )

    e_barbeiro = hasattr(usuario, "perfil_barbeiro")

    return {
        "is_administrador": is_administrador,
        "e_barbeiro": e_barbeiro,
    }