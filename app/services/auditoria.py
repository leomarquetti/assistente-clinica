"""Serviço de registro de auditoria append-only.

Garante que nenhuma informação pessoal em texto claro seja registrada nos logs
e que toda ação do pipeline ou intervenção humana seja rastreável.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from app.domain.schemas import AuditoriaLogResponse
from app.storage.base import Storage


class AuditoriaService:
    """Gerencia a criação de registros de auditoria append-only."""

    def __init__(self, storage: Storage):
        self.storage = storage

    async def registrar_evento(
        self,
        acao: str,
        operador: str,
        mensagem_id: str | None = None,
        detalhes: dict[str, Any] | None = None,
    ) -> AuditoriaLogResponse:
        """Cria e persiste um novo registro no log de auditoria append-only."""
        registro = AuditoriaLogResponse(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            mensagem_id=mensagem_id,
            acao=acao,
            operador=operador,
            detalhes=detalhes or {},
        )
        await self.storage.registrar_auditoria(registro)
        return registro
