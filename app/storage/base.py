"""Interface base para os mecanismos de armazenamento e persistência."""

from abc import ABC, abstractmethod

from app.domain.schemas import AuditoriaLogResponse, MensagemResponse


class Storage(ABC):
    """Interface abstrata de armazenamento para mensagens e trilha de auditoria append-only."""

    @abstractmethod
    async def salvar_mensagem(self, mensagem: MensagemResponse) -> None:
        """Persiste uma nova mensagem já processada."""
        pass

    @abstractmethod
    async def obter_mensagem(self, mensagem_id: str) -> MensagemResponse | None:
        """Busca uma mensagem por seu identificador único."""
        pass

    @abstractmethod
    async def atualizar_mensagem(self, mensagem: MensagemResponse) -> None:
        """Atualiza o registro de uma mensagem existente (ex.: aprovação ou rejeição)."""
        pass

    @abstractmethod
    async def registrar_auditoria(self, registro: AuditoriaLogResponse) -> None:
        """Registra um evento de auditoria no log append-only."""
        pass

    @abstractmethod
    async def listar_auditoria(
        self, limite: int = 50, offset: int = 0
    ) -> list[AuditoriaLogResponse]:
        """Lista registros de auditoria em ordem cronológica reversa."""
        pass

    @abstractmethod
    async def limpar_dados(self) -> None:
        """Remove todos os dados (utilizado em testes e reinicialização demo)."""
        pass
