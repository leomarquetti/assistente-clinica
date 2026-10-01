"""Módulo de autenticação simples por API Key e autorização baseada em papéis."""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings
from app.domain.intents import RoleEnum

API_KEY_HEADER = APIKeyHeader(
    name="X-API-Key",
    description="Chave de API para autenticação por papel ('demo-atendente-key' para atendentes ou 'demo-gestor-key' para gestores).",
    auto_error=False,
)


async def get_current_role(api_key: str | None = Security(API_KEY_HEADER)) -> RoleEnum:
    """Valida a chave de API fornecida no cabeçalho X-API-Key e retorna o papel correspondente."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação requerida: cabeçalho 'X-API-Key' ausente.",
        )

    if api_key == settings.API_KEY_GESTOR:
        return RoleEnum.GESTOR
    elif api_key == settings.API_KEY_ATENDENTE:
        return RoleEnum.ATENDENTE
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API inválida ou não autorizada.",
        )


async def require_atendente(
    role: RoleEnum = Security(get_current_role),
) -> RoleEnum:
    """Permite acesso a atendentes e gestores."""
    if role not in (RoleEnum.ATENDENTE, RoleEnum.GESTOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: requer papel de 'atendente' ou 'gestor'.",
        )
    return role


async def require_gestor(
    role: RoleEnum = Security(get_current_role),
) -> RoleEnum:
    """Permite acesso estritamente a gestores."""
    if role != RoleEnum.GESTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: recurso restrito ao papel de 'gestor'.",
        )
    return role
