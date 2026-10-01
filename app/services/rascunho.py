"""Serviço de geração de rascunhos de resposta administrativa."""

from app.domain.intents import IntentEnum
from app.providers.llm_base import LLMProvider


class RascunhoService:
    """Orquestra a geração de rascunhos via provedor plugável de IA."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    async def gerar_sugestao(self, texto_mascarado: str, intencao: IntentEnum) -> str:
        """Gera sugestão de resposta para revisão humana.

        Segurança clínica: bloqueia categoricamente qualquer tentativa de gerar
        rascunho para urgências médicas ou diagnósticos clínicos.
        """
        if intencao == IntentEnum.URGENCIA_CLINICA:
            raise ValueError(
                "Segurança clínica: Rascunhos automatizados são proibidos para urgências médicas."
            )

        return await self.provider.gerar_rascunho(
            texto_mascarado=texto_mascarado, intencao=intencao
        )
