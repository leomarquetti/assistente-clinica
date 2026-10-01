"""Interface abstrata base para provedores de IA (simulada ou real)."""

from abc import ABC, abstractmethod

from app.domain.intents import IntentEnum


class LLMProvider(ABC):
    """Interface padronizada para provedores de LLM plugáveis."""

    @abstractmethod
    async def gerar_rascunho(self, texto_mascarado: str, intencao: IntentEnum) -> str:
        """Gera um rascunho de resposta administrativa para a intenção detectada.

        IMPORTANTE: Nunca deve ser invocado com intenção URGENCIA_CLINICA ou texto não mascarado.
        """
        pass
