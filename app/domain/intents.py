"""Definição de enumerações de domínio: intenções, status e papéis de acesso."""

from enum import StrEnum


class IntentEnum(StrEnum):
    """Intenções possíveis identificadas na triagem da mensagem."""

    AGENDAMENTO = "agendamento"
    REMARCACAO = "remarcacao"
    DUVIDA_ADMINISTRATIVA = "duvida_administrativa"
    FINANCEIRO = "financeiro"
    URGENCIA_CLINICA = "urgencia_clinica"
    OUTRO = "outro"


class StatusMensagemEnum(StrEnum):
    """Estados possíveis do ciclo de vida de uma mensagem no sistema."""

    RECEBIDA = "recebida"
    AGUARDANDO_APROVACAO = "aguardando_aprovacao"
    REQUER_ATENCAO_HUMANA = "requer_atencao_humana"
    APROVADA = "aprovada"
    REJEITADA = "rejeitada"


class RoleEnum(StrEnum):
    """Papéis de acesso autorizados via API Key."""

    ATENDENTE = "atendente"
    GESTOR = "gestor"
