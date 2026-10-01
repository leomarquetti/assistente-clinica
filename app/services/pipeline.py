"""Orquestrador do pipeline de atendimento, privacidade, triagem e aprovação."""

import uuid
from datetime import UTC, datetime

from app.domain.intents import StatusMensagemEnum
from app.domain.schemas import (
    AprovacaoRequest,
    MensagemCriar,
    MensagemResponse,
    RejeicaoRequest,
)
from app.domain.state_machine import validar_transicao
from app.services.auditoria import AuditoriaService
from app.services.privacidade import mascarar_dados_pessoais
from app.services.rascunho import RascunhoService
from app.services.triagem import executar_triagem_deterministica
from app.storage.base import Storage


class PipelineService:
    """Coordena o fluxo de processamento de ponta a ponta com segurança e auditoria."""

    def __init__(
        self,
        storage: Storage,
        auditoria_service: AuditoriaService,
        rascunho_service: RascunhoService,
        limiar_confianca: float = 0.6,
    ):
        self.storage = storage
        self.auditoria = auditoria_service
        self.rascunho = rascunho_service
        self.limiar_confianca = limiar_confianca

    async def processar_mensagem(self, entrada: MensagemCriar) -> MensagemResponse:
        """Processa uma mensagem de paciente fictício:

        1. Mascara dados pessoais (entrada e identificador).
        2. Registra recebimento na auditoria append-only.
        3. Realiza triagem determinística de urgência e intenção.
        4. Decide escalonamento para atenção humana ou geração de rascunho.
        5. Persiste a mensagem e audita a conclusão da triagem.
        """
        mensagem_id = str(uuid.uuid4())
        agora = datetime.now(UTC)

        # 1. Mascaramento rigoroso de PII antes de qualquer processamento
        texto_mascarado = mascarar_dados_pessoais(entrada.texto)
        id_paciente_mascarado = (
            mascarar_dados_pessoais(entrada.paciente_identificador)
            if entrada.paciente_identificador
            else None
        )

        # 2. Auditoria append-only inicial
        await self.auditoria.registrar_evento(
            acao="MENSAGEM_RECEBIDA",
            operador="sistema",
            mensagem_id=mensagem_id,
            detalhes={
                "texto_mascarado": texto_mascarado,
                "paciente_identificador_mascarado": id_paciente_mascarado,
            },
        )

        # 3. Triagem determinística com detecção de urgência e negação
        resultado_triagem = executar_triagem_deterministica(
            texto=texto_mascarado,
            limiar_confianca=self.limiar_confianca,
        )

        # 4. Decisão de estado e rascunho
        rascunho_sugerido: str | None = None
        if resultado_triagem.requer_atencao_humana:
            status = StatusMensagemEnum.REQUER_ATENCAO_HUMANA
        else:
            status = StatusMensagemEnum.AGUARDANDO_APROVACAO
            rascunho_sugerido = await self.rascunho.gerar_sugestao(
                texto_mascarado=texto_mascarado,
                intencao=resultado_triagem.intencao,
            )

        # 5. Montagem da entidade de resposta
        mensagem = MensagemResponse(
            id=mensagem_id,
            texto_mascarado=texto_mascarado,
            paciente_identificador_mascarado=id_paciente_mascarado,
            intencao=resultado_triagem.intencao,
            confianca=resultado_triagem.confianca,
            requer_atencao_humana=resultado_triagem.requer_atencao_humana,
            motivo_escalonamento=resultado_triagem.motivo_escalonamento,
            rascunho_resposta=rascunho_sugerido,
            status=status,
            criado_em=agora,
            atualizado_em=agora,
        )

        # Persistência
        await self.storage.salvar_mensagem(mensagem)

        # Auditoria da conclusão da triagem
        await self.auditoria.registrar_evento(
            acao="TRIAGEM_CONCLUIDA",
            operador="sistema",
            mensagem_id=mensagem_id,
            detalhes={
                "intencao": resultado_triagem.intencao.value,
                "confianca": resultado_triagem.confianca,
                "requer_atencao_humana": resultado_triagem.requer_atencao_humana,
                "status": status.value,
            },
        )

        return mensagem

    async def aprovar_mensagem(
        self,
        mensagem_id: str,
        requisicao: AprovacaoRequest,
        operador_autenticado: str,
    ) -> MensagemResponse:
        """Aprova uma mensagem pelo operador humano após revisão, aplicando máquina de estados."""
        mensagem = await self.storage.obter_mensagem(mensagem_id)
        if not mensagem:
            raise KeyError(f"Mensagem {mensagem_id} não encontrada.")

        # Validação estrita da máquina de estados (levanta StateTransitionError se inválida)
        validar_transicao(mensagem.status, StatusMensagemEnum.APROVADA)

        # Mascaramento também do texto aprovado e observações para proteção adicional
        texto_final = requisicao.texto_aprovado or mensagem.rascunho_resposta
        if not texto_final:
            raise ValueError(
                "A mensagem requer um texto aprovado explicitamente redigido pelo operador."
            )

        texto_final_mascarado = mascarar_dados_pessoais(texto_final)
        obs_mascaradas = (
            mascarar_dados_pessoais(requisicao.observacoes) if requisicao.observacoes else None
        )

        mensagem.status = StatusMensagemEnum.APROVADA
        mensagem.texto_aprovado = texto_final_mascarado
        mensagem.aprovado_por = requisicao.aprovado_por
        mensagem.observacoes = obs_mascaradas
        mensagem.atualizado_em = datetime.now(UTC)

        await self.storage.atualizar_mensagem(mensagem)

        await self.auditoria.registrar_evento(
            acao="MENSAGEM_APROVADA",
            operador=operador_autenticado,
            mensagem_id=mensagem_id,
            detalhes={
                "aprovado_por": requisicao.aprovado_por,
                "texto_aprovado_mascarado": texto_final_mascarado,
                "observacoes_mascaradas": obs_mascaradas,
            },
        )

        return mensagem

    async def rejeitar_mensagem(
        self,
        mensagem_id: str,
        requisicao: RejeicaoRequest,
        operador_autenticado: str,
    ) -> MensagemResponse:
        """Rejeita uma mensagem pelo operador humano, aplicando máquina de estados."""
        mensagem = await self.storage.obter_mensagem(mensagem_id)
        if not mensagem:
            raise KeyError(f"Mensagem {mensagem_id} não encontrada.")

        # Validação estrita da máquina de estados
        validar_transicao(mensagem.status, StatusMensagemEnum.REJEITADA)

        motivo_mascarado = mascarar_dados_pessoais(requisicao.motivo)

        mensagem.status = StatusMensagemEnum.REJEITADA
        mensagem.observacoes = f"Rejeitado: {motivo_mascarado}"
        mensagem.atualizado_em = datetime.now(UTC)

        await self.storage.atualizar_mensagem(mensagem)

        await self.auditoria.registrar_evento(
            acao="MENSAGEM_REJEITADA",
            operador=operador_autenticado,
            mensagem_id=mensagem_id,
            detalhes={
                "rejeitado_por": requisicao.rejeitado_por,
                "motivo_mascarado": motivo_mascarado,
            },
        )

        return mensagem
