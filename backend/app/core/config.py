from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Configuración leída del entorno (y de `.env` en la raíz del repo durante desarrollo)."""

    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_version: str = "0.1.0"
    database_url: str = Field(min_length=1)
    redis_url: str = Field(min_length=1)
    log_level: str = "INFO"
    cors_origins: list[str] = []
    dependency_timeout_s: float = 2.0

    # Autenticación (ADR-006). El secreto firma los access tokens: mínimo 32 caracteres aleatorios.
    jwt_secret: str = Field(min_length=32)
    jwt_issuer: str = "aicc-api"
    access_token_ttl_s: int = 15 * 60
    refresh_token_ttl_days: int = 30

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def docs_enabled(self) -> bool:
        return self.app_env in ("development", "test")


@lru_cache
def get_settings() -> Settings:
    return Settings()
