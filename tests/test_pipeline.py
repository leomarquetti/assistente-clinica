"""Testes de integração do PipelineService."""

import pytest

from app.api.deps import get_pipeline_service
from app.domain.intents import IntentEnum, StatusMensagemEnum
from app.domain.schemas import AprovacaoRequest, MensagemCriar


@pytest.mark.asyncio
async def test_pipeline_processar_mensagem_agendamento_com_sucesso() -> None:
    pipeline = get_pipeline_service()
    entrada = MensagemCriar(
        texto="Olá, gostaria de agendar uma consulta para meu filho. Contato: (11) 98765-4321.",
        paciente_identificador="João da Silva",
    )

    resposta = await pipeline.processar_mensagem(entrada)

    assert resposta.id is not None
    assert "(11) 98765-4321" not in resposta.texto_mascarado
    assert "[TELEFONE MASCARADO]" in resposta.texto_mascarado
    assert resposta.intencao == IntentEnum.AGENDAMENTO
    assert resposta.status == StatusMensagemEnum.AGUARDANDO_APROVACAO
    assert resposta.requer_atencao_humana is False
    assert resposta.rascunho_resposta is not None
    assert "agendamento" in resposta.rascunho_resposta.lower()


@pytest.mark.asyncio
async def test_pipeline_processar_mensagem_urgente_bloqueia_rascunho() -> None:
    pipeline = get_pipeline_service()
    entrada = MensagemCriar(
        texto="Socorro, estou com muita dor no peito e formigamento!",
        paciente_identificador="Paciente Emergência",
    )

    resposta = await pipeline.processar_mensagem(entrada)

    assert resposta.intencao == IntentEnum.URGENCIA_CLINICA
    assert resposta.status == StatusMensagemEnum.REQUER_ATENCAO_HUMANA
    assert resposta.requer_atencao_humana is True
    # REGRA FUNDAMENTAL: Sem rascunho de IA para urgências clínicas
    assert resposta.rascunho_resposta is None
    assert "Atenção humana imediata" in (resposta.motivo_escalonamento or "")


@pytest.mark.asyncio
async def test_pipeline_aprovar_e_rejeitar_mensagem() -> None:
    pipeline = get_pipeline_service()

    # 1. Processa mensagem
    msg = await pipeline.processar_mensagem(MensagemCriar(texto="Gostaria de agendar retorno."))
    assert msg.status == StatusMensagemEnum.AGUARDANDO_APROVACAO

    # 2. Aprova mensagem com texto ajustado
    aprovada = await pipeline.aprovar_mensagem(
        mensagem_id=msg.id,
        requisicao=AprovacaoRequest(
            texto_aprovado="Olá! Confirmamos sua consulta para quinta-feira às 15h.",
            aprovado_por="atendente_lucia",
            observacoes="Paciente preferiu o turno da tarde.",
        ),
        operador_autenticado="atendente:atendente_lucia",
    )
    assert aprovada.status == StatusMensagemEnum.APROVADA
    assert aprovada.texto_aprovado == "Olá! Confirmamos sua consulta para quinta-feira às 15h."
    assert aprovada.aprovado_por == "atendente_lucia"
