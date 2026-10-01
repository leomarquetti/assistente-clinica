"""Provedor de LLM simulado (mock baseado em regras determinísticas)."""

from app.domain.intents import IntentEnum
from app.providers.llm_base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Provedor mock baseado em regras de negócio para geração de rascunhos de demonstração.

    Gera rascunhos cordiais e puramente administrativos, sem jamais emitir conselhos médicos.
    """

    RESPOSTAS_TEMPLATES: dict[IntentEnum, str] = {
        IntentEnum.AGENDAMENTO: (
            "Olá! Agradecemos o contato com nossa clínica. Para prosseguirmos com seu agendamento, "
            "por favor nos informe a especialidade desejada e sua preferência de dia e turno "
            "(manhã ou tarde). Retornaremos com as opções disponíveis."
        ),
        IntentEnum.REMARCACAO: (
            "Olá! Compreendemos a solicitação. Para reorganizarmos seu atendimento ou cancelamento, "
            "por gentileza informe para qual período você gostaria de transferir sua consulta."
        ),
        IntentEnum.DUVIDA_ADMINISTRATIVA: (
            "Olá! Nosso horário de funcionamento é de segunda a sexta, das 07h às 19h, e aos sábados "
            "das 08h às 12h. Trabalhamos com diversos convênios e oferecemos estacionamento no local. "
            "Como podemos ajudar com mais informações?"
        ),
        IntentEnum.FINANCEIRO: (
            "Olá! Para questões financeiras, comprovantes de pagamento, emissão de recibos e notas "
            "fiscais para reembolso, nossa equipe administrativa pode orientá-lo. Aceitamos PIX, "
            "cartões de crédito e débito. Poderia nos informar o procedimento correspondente?"
        ),
        IntentEnum.OUTRO: (
            "Olá! Recebemos sua mensagem em nossa clínica. Para que possamos direcionar o atendimento "
            "correto, poderia nos fornecer mais detalhes sobre sua solicitação?"
        ),
    }

    async def gerar_rascunho(self, texto_mascarado: str, intencao: IntentEnum) -> str:
        """Retorna uma sugestão determinística de resposta para revisão humana."""
        if intencao == IntentEnum.URGENCIA_CLINICA:
            raise ValueError(
                "Segurança clínica: Proibida a geração de rascunho automatizado para urgências médicas."
            )

        return self.RESPOSTAS_TEMPLATES.get(
            intencao,
            self.RESPOSTAS_TEMPLATES[IntentEnum.OUTRO],
        )
