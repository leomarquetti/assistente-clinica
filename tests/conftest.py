"""Configurações e fixtures para a suite de testes pytest."""

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_storage
from app.config import settings
from app.main import app
from app.storage.memory import MemoryStorage


@pytest.fixture(autouse=True)
def limpar_armazenamento() -> None:
    """Garante que o armazenamento em memória seja resetado antes de cada teste."""
    storage = get_storage()
    if isinstance(storage, MemoryStorage):
        storage._mensagens.clear()
        storage._auditoria.clear()


@pytest.fixture
def client() -> TestClient:
    """Cliente HTTP de teste para invocar endpoints da aplicação."""
    return TestClient(app)


@pytest.fixture
def headers_atendente() -> dict[str, str]:
    """Headers com chave de API de Atendente."""
    return {"X-API-Key": settings.API_KEY_ATENDENTE}


@pytest.fixture
def headers_gestor() -> dict[str, str]:
    """Headers com chave de API de Gestor."""
    return {"X-API-Key": settings.API_KEY_GESTOR}
