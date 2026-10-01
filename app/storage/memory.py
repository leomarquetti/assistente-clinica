"""Implementação de armazenamento em memória volátil para modo de demonstração."""

import asyncio
from copy import deepcopy

from app.domain.schemas import AuditoriaLogResponse, MensagemResponse
from app.storage.base import Storage


class MemoryStorage(Storage):
    """Storage volátil em memória, ideal para testes rápidos e demonstração efêmera."""

    def __init__(self) -> None:
        self._mensagens: dict[str, MensagemResponse] = {}
        self._auditoria: list[AuditoriaLogResponse] = []
        self._lock = asyncio.Lock()

    async def salvar_mensagem(self, mensagem: MensagemResponse) -> None:
        async with self._lock:
            self._mensagens[mensagem.id] = deepcopy(mensagem)

    async def obter_mensagem(self, mensagem_id: str) -> MensagemResponse | None:
        async with self._lock:
            item = self._mensagens.get(mensagem_id)
            return deepcopy(item) if item else None

    async def atualizar_mensagem(self, mensagem: MensagemResponse) -> None:
        async with self._lock:
            if mensagem.id not in self._mensagens:
                raise KeyError(f"Mensagem {mensagem.id} não encontrada.")
            self._mensagens[mensagem.id] = deepcopy(mensagem)

    async def registrar_auditoria(self, registro: AuditoriaLogResponse) -> None:
        async with self._lock:
            # append-only: insere no final
            self._auditoria.append(deepcopy(registro))

    async def listar_auditoria(
        self, limite: int = 50, offset: int = 0
    ) -> list[AuditoriaLogResponse]:
        async with self._lock:
            # Retorna os mais recentes primeiro
            invertido = list(reversed(self._auditoria))
            fatia = invertido[offset : offset + limite]
            return deepcopy(fatia)

    async def limpar_dados(self) -> None:
        async with self._lock:
            self._mensagens.clear()
            self._auditoria.clear()
