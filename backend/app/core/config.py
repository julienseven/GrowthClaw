"""
Central, typed configuration for the $GROWTH backend.

Uses `pydantic-settings` to bind environment variables (plus an optional
`.env` file) into a single frozen `Settings` object. Every subsystem
(the Solana RPC client, the OpenAI engine, the asyncio workers) reads its
runtime parameters from here — there is never any hardcoded key, URL, or
token address scattered through the codebase.

Usage:

    from app.core.config import get_settings
    settings = get_settings()
    print(settings.solana.rpc_url)
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class SolanaSettings(BaseSettings):
    """Everything required to talk to the Solana blockchain."""

    model_config = SettingsConfigDict(env_prefix="SOLANA_", extra="ignore")

    rpc_url: str = Field(default="https://api.mainnet-beta.solana.com")
    rpc_ws_url: str | None = Field(default=None)
    rpc_url_backup: str | None = Field(default=None)

    max_concurrency: int = Field(default=16, gt=0)
    timeout_seconds: float = Field(default=30.0, gt=0)

    # Base58 address of the agent wallet the growth loop polls for inbound SOL.
    wallet_address: str = Field(default="")

    # Native SOL baseline: inbound transfers must deliver >= this amount.
    min_sol_amount: float = Field(default=0.05, gt=0)

    # Number of recent signatures to pull per poll (bounded 1..1000).
    signature_limit: int = Field(default=20, ge=1, le=1000)

    # Comma-separated base58 mint addresses the growth engine is targeting.
    target_tokens: list[str] = Field(default_factory=list)

    @field_validator("target_tokens", mode="before")
    @classmethod
    def _parse_token_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [t.strip() for t in value.split(",") if t.strip()]
        if isinstance(value, list | tuple):
            return [str(t).strip() for t in value if str(t).strip()]
        raise ValueError("SOLANA_TARGET_TOKENS must be a comma-separated string or list")


class OpenAISettings(BaseSettings):
    """Configuration for the AI engine (gpt-4o-mini by default)."""

    model_config = SettingsConfigDict(env_prefix="OPENAI_", extra="ignore")

    api_key: str | None = Field(default=None)
    model: str = Field(default="gpt-4o-mini")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, gt=0)
    timeout_seconds: float = Field(default=60.0, gt=0)


class WorkerSettings(BaseSettings):
    """Tuning for the asyncio background-worker runtime."""

    model_config = SettingsConfigDict(env_prefix="WORKER_", extra="ignore")

    max_concurrent_tasks: int = Field(default=8, gt=0)
    poll_interval_seconds: float = Field(default=5.0, gt=0)


class Settings(BaseSettings):
    """Top-level application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    debug: bool = False

    # Annotated with NoDecode so pydantic-settings reads the raw env string
    # (comma-separated) instead of trying to JSON-parse it; the validator
    # below splits on commas.
    cors_allowed_origins: Annotated[
        list[str], NoDecode
    ] = Field(default_factory=lambda: ["http://localhost:3000"])

    solana: SolanaSettings = SolanaSettings()
    openai: OpenAISettings = OpenAISettings()
    worker: WorkerSettings = WorkerSettings()

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _parse_origins(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [o.strip() for o in value.split(",") if o.strip()]
        return list(value) if value else []

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Return the singleton settings instance (parsed once, cached)."""
    return Settings()


def env_file_path() -> Path:
    """Absolute path to the .env file used by this project (for CLI tooling)."""
    return Path(__file__).resolve().parent.parent.parent / ".env"
