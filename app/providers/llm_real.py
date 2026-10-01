"""Provedor real de LLM (stub para integração com OpenAI, Anthropic, Gemini, etc.)."""

from app.config import settings
from app.domain.intents import IntentEnum
from app.providers.llm_base import LLMProvider


class RealLLMProvider(LLMProvider):
    """Stub de integração para provedor real de LLM.

    Ativado somente quando LLM_PROVIDER="real" e a chave de API for informada no ambiente.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.LLM_API_KEY
        if not self.api_key:
            # Não expõe que tipo de chave ou detalhes sensíveis no erro
            raise ValueError(
                "Provedor real configurado, mas nenhuma chave de API foi fornecida no servidor."
            )

    async def gerar_rascunho(self, texto_mascarado: str, intencao: IntentEnum) -> str:
        """Gera rascunho através de chamada a provedor externo de LLM."""
        if intencao == IntentEnum.URGENCIA_CLINICA:
            raise ValueError(
                "Segurança clínica: Proibida a geração de rascunho de IA para urgências médicas."
            )

        # Stub indicando a integração futura com teto de gastos e prompt de sistema seguro
        raise NotImplementedError(
            "Integração com LLM real é um stub para a Fase 3 da arquitetura. "
            "Use LLM_PROVIDER=mock para testes e demonstração."
        )
