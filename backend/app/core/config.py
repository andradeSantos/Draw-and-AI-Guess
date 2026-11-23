"""Configurações da aplicação carregadas via `.env` (sem segredos no código)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://museu_user:museu_pass_local@localhost:5432/draw_ia_db"
    model_artifacts_dir: str = "ml/artifacts"
    unknown_confidence_threshold: float | None = None
    unknown_margin_threshold: float | None = None
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
