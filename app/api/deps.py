"""Injeção de dependências compartilhadas da API."""

from functools import lru_cache

from app.config import settings
from app.providers.llm_base import LLMProvider
from app.providers.llm_mock import MockLLMProvider
from app.providers.llm_real import RealLLMProvider
from app.services.auditoria import AuditoriaService
from app.services.pipeline import PipelineService
from app.services.rascunho import RascunhoService
from app.storage.base import Storage
from app.storage.memory import MemoryStorage

# Singleton para o storage em memória no ciclo de vida da aplicação
_memory_storage_instance = MemoryStorage()


def get_storage() -> Storage:
    """Retorna o driver de armazenamento ativo conforme configuração."""
    if settings.STORAGE == "sqlite":
        # SQLiteStorage será integrado plenamente na Fase 2
        from app.storage.sqlite import SqliteStorage

        return SqliteStorage(settings.SQLITE_DB_PATH)
    return _memory_storage_instance


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Instancia o provedor de LLM configurado (mock ou real)."""
    if settings.LLM_PROVIDER == "real":
        return RealLLMProvider()
    return MockLLMProvider()


def get_auditoria_service() -> AuditoriaService:
    """Instancia o serviço de auditoria append-only."""
    return AuditoriaService(storage=get_storage())


def get_rascunho_service() -> RascunhoService:
    """Instancia o serviço de rascunhos com o LLMProvider configurado."""
    return RascunhoService(provider=get_llm_provider())


def get_pipeline_service() -> PipelineService:
    """Instancia o serviço do pipeline completo de atendimento."""
    return PipelineService(
        storage=get_storage(),
        auditoria_service=get_auditoria_service(),
        rascunho_service=get_rascunho_service(),
        limiar_confianca=settings.CONFIDENCE_THRESHOLD,
    )
