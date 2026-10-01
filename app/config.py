"""Configurações da aplicação baseadas em Pydantic Settings."""

from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Modo da aplicação (apenas demo é suportado nesta fase de demonstração)
    APP_MODE: Literal["demo"] = "demo"

    # Provedor de LLM: "mock" (regras) ou "real" (stub ativável por chave)
    LLM_PROVIDER: Literal["mock", "real"] = "mock"

    # Tipo de armazenamento: "memory" ou "sqlite"
    STORAGE: Literal["memory", "sqlite"] = "memory"

    # Limiar mínimo de confiança para permitir geração automática de rascunho
    CONFIDENCE_THRESHOLD: float = 0.6

    # Caminho do banco SQLite caso STORAGE="sqlite"
    SQLITE_DB_PATH: str = "clinic_demo.db"

    # Chaves de demonstração estáticas (válidas unicamente em APP_MODE=demo)
    API_KEY_ATENDENTE: str = "demo-atendente-key"
    API_KEY_GESTOR: str = "demo-gestor-key"

    # Limite de taxa (Rate Limit) padrão
    RATE_LIMIT_DEFAULT: str = "60/minute"

    # Chave para LLM real (apenas se LLM_PROVIDER="real")
    LLM_API_KEY: str | None = None

    @model_validator(mode="after")
    def validar_seguranca_chaves(self) -> "Settings":
        """Garante formalmente que as chaves padrão 'demo-*' jamais sejam aceitas fora do modo demo."""
        chaves_padrao_demo = {"demo-atendente-key", "demo-gestor-key"}
        if self.APP_MODE != "demo":
            if (
                self.API_KEY_ATENDENTE in chaves_padrao_demo
                or self.API_KEY_GESTOR in chaves_padrao_demo
            ):
                raise ValueError(
                    "As chaves padrão de demonstração ('demo-*') são proibidas fora do modo demo."
                )
        return self


# Instância global de configurações
settings = Settings()
