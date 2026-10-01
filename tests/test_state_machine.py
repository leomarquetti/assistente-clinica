"""Testes unitários da máquina de estados do ciclo de vida das mensagens."""

import pytest

from app.domain.intents import StatusMensagemEnum
from app.domain.state_machine import StateTransitionError, validar_transicao


def test_transicoes_validas() -> None:
    # A partir de RECEBIDA
    validar_transicao(StatusMensagemEnum.RECEBIDA, StatusMensagemEnum.AGUARDANDO_APROVACAO)
    validar_transicao(StatusMensagemEnum.RECEBIDA, StatusMensagemEnum.REQUER_ATENCAO_HUMANA)

    # A partir de AGUARDANDO_APROVACAO
    validar_transicao(StatusMensagemEnum.AGUARDANDO_APROVACAO, StatusMensagemEnum.APROVADA)
    validar_transicao(StatusMensagemEnum.AGUARDANDO_APROVACAO, StatusMensagemEnum.REJEITADA)

    # A partir de REQUER_ATENCAO_HUMANA
    validar_transicao(StatusMensagemEnum.REQUER_ATENCAO_HUMANA, StatusMensagemEnum.APROVADA)
    validar_transicao(StatusMensagemEnum.REQUER_ATENCAO_HUMANA, StatusMensagemEnum.REJEITADA)


def test_transicoes_invalidas_a_partir_de_aprovada() -> None:
    # APROVADA é estado terminal: qualquer transição subsequente deve falhar
    destinos_invalidos = [
        StatusMensagemEnum.RECEBIDA,
        StatusMensagemEnum.AGUARDANDO_APROVACAO,
        StatusMensagemEnum.REQUER_ATENCAO_HUMANA,
        StatusMensagemEnum.APROVADA,
        StatusMensagemEnum.REJEITADA,
    ]
    for destino in destinos_invalidos:
        with pytest.raises(StateTransitionError) as exc_info:
            validar_transicao(StatusMensagemEnum.APROVADA, destino)
        assert exc_info.value.status_atual == StatusMensagemEnum.APROVADA
        assert exc_info.value.novo_status == destino


def test_transicoes_invalidas_a_partir_de_rejeitada() -> None:
    # REJEITADA é estado terminal
    destinos_invalidos = [
        StatusMensagemEnum.RECEBIDA,
        StatusMensagemEnum.AGUARDANDO_APROVACAO,
        StatusMensagemEnum.REQUER_ATENCAO_HUMANA,
        StatusMensagemEnum.APROVADA,
        StatusMensagemEnum.REJEITADA,
    ]
    for destino in destinos_invalidos:
        with pytest.raises(StateTransitionError):
            validar_transicao(StatusMensagemEnum.REJEITADA, destino)


def test_transicao_direta_invalida_de_recebida_para_aprovada() -> None:
    # Não pode aprovar direto sem antes passar pela triagem
    with pytest.raises(StateTransitionError):
        validar_transicao(StatusMensagemEnum.RECEBIDA, StatusMensagemEnum.APROVADA)
