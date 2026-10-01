"""Máquina de estados para transições do ciclo de vida das mensagens."""

from app.domain.intents import StatusMensagemEnum


class StateTransitionError(Exception):
    """Exceção levantada quando uma transição de estado inválida é requisitada."""

    def __init__(self, status_atual: StatusMensagemEnum, novo_status: StatusMensagemEnum):
        self.status_atual = status_atual
        self.novo_status = novo_status
        super().__init__(
            f"Transição inválida de estado: '{status_atual.value}' -> '{novo_status.value}'."
        )


# Mapa de transições válidas permitidas
TRANSICOES_VALIDAS: dict[StatusMensagemEnum, set[StatusMensagemEnum]] = {
    StatusMensagemEnum.RECEBIDA: {
        StatusMensagemEnum.AGUARDANDO_APROVACAO,
        StatusMensagemEnum.REQUER_ATENCAO_HUMANA,
    },
    StatusMensagemEnum.AGUARDANDO_APROVACAO: {
        StatusMensagemEnum.APROVADA,
        StatusMensagemEnum.REJEITADA,
    },
    StatusMensagemEnum.REQUER_ATENCAO_HUMANA: {
        StatusMensagemEnum.APROVADA,
        StatusMensagemEnum.REJEITADA,
    },
    # Estados terminais: nenhuma transição adicional é permitida
    StatusMensagemEnum.APROVADA: set(),
    StatusMensagemEnum.REJEITADA: set(),
}


def validar_transicao(status_atual: StatusMensagemEnum, novo_status: StatusMensagemEnum) -> None:
    """Valida se a transição entre estados é permitida pela máquina de estados.

    Levanta StateTransitionError se a transição for proibida.
    """
    destinos_permitidos = TRANSICOES_VALIDAS.get(status_atual, set())
    if novo_status not in destinos_permitidos:
        raise StateTransitionError(status_atual=status_atual, novo_status=novo_status)
