"""Modelos Pydantic v2 para validação de entrada e serialização de saída."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.intents import IntentEnum, StatusMensagemEnum


class MensagemCriar(BaseModel):
    """Payload de entrada para recebimento de mensagem de paciente fictício."""

    texto: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Conteúdo da mensagem enviada pelo paciente fictício (máx. 2000 caracteres)",
        examples=["Olá, gostaria de agendar uma consulta para amanhã à tarde."],
    )
    paciente_identificador: str | None = Field(
        default=None,
        max_length=100,
        description="Código opaco do paciente (ex.: P-1024). Não utilize nomes ou documentos reais.",
        examples=["P-1024"],
    )


class MensagemResponse(BaseModel):
    """Resposta com dados processados da mensagem e resultado da triagem."""

    id: str
    texto_mascarado: str
    paciente_identificador_mascarado: str | None = None
    intencao: IntentEnum
    confianca: float
    requer_atencao_humana: bool
    motivo_escalonamento: str | None = None
    rascunho_resposta: str | None = None
    status: StatusMensagemEnum
    criado_em: datetime
    atualizado_em: datetime
    texto_aprovado: str | None = None
    aprovado_por: str | None = None
    observacoes: str | None = None


class AprovacaoRequest(BaseModel):
    """Payload para aprovação ou ajuste do rascunho por atendente ou gestor."""

    texto_aprovado: str | None = Field(
        default=None,
        max_length=2000,
        description="Texto final aprovado. Se omitido, utiliza o rascunho sugerido.",
    )
    aprovado_por: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Identificação do operador responsável pela aprovação humana.",
        examples=["atendente_maria"],
    )
    observacoes: str | None = Field(
        default=None,
        max_length=500,
        description="Observações operacionais da equipe médica/administrativa.",
    )


class RejeicaoRequest(BaseModel):
    """Payload para descarte ou rejeição da mensagem pela equipe."""

    motivo: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Justificativa da rejeição da mensagem.",
        examples=["Mensagem duplicada ou spam."],
    )
    rejeitado_por: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Identificação do operador responsável pela rejeição.",
        examples=["atendente_joao"],
    )


class AuditoriaLogResponse(BaseModel):
    """Item do log de auditoria append-only."""

    id: str
    timestamp: datetime
    mensagem_id: str | None = None
    acao: str
    operador: str
    detalhes: dict[str, Any]


class HealthCheckResponse(BaseModel):
    """Resposta de verificação de integridade e metadados do ambiente de demonstração."""

    status: str
    app_mode: str
    llm_provider: str
    storage: str
    aviso: str
