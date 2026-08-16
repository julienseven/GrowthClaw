"""
Configuration validation CLI.

Run `python -m app.infra.config` from the backend directory to verify that
every required environment variable is present and well-formed before
starting the FastAPI server or the asyncio workers.

Handy for CI gates and local smoke-testing:

    cd backend
    python -m app.infra.config
"""

from __future__ import annotations

import sys

BASIC_VALID = set("123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")  # base58


def _is_base58(value: str) -> bool:
    return bool(value) and all(c in BASIC_VALID for c in value)


def run_checks() -> int:
    from app.core.config import get_settings

    settings = get_settings()
    errors: list[str] = []
    notes: list[str] = []

    # --- OpenAI --------------------------------------------------
    if not settings.openai.api_key:
        if settings.is_production:
            errors.append("OPENAI_API_KEY is required in production")
        else:
            notes.append("OPENAI_API_KEY is unset (AI engine disabled in dev)")

    # --- Solana --------------------------------------------------
    if not settings.solana.rpc_url.startswith(("https://", "http://")):
        errors.append("SOLANA_RPC_URL must be an http(s) URL")

    for token in settings.solana.target_tokens:
        if not _is_base58(token):
            errors.append(f"SOLANA_TARGET_TOKENS contains invalid base58: {token!r}")

    # --- Report --------------------------------------------------
    print("== $GROWTH backend configuration check ==")
    print(f"  app_env            = {settings.app_env}")
    print(f"  solana.rpc_url     = {settings.solana.rpc_url}")
    print(f"  solana.targets     = {len(settings.solana.target_tokens)} token(s)")
    print(f"  openai.model       = {settings.openai.model}")
    print(f"  openai.api_key     = {'***' if settings.openai.api_key else '<unset>'}")
    print(f"  worker.concurrency = {settings.worker.max_concurrent_tasks}")
    for note in notes:
        print(f"  [note] {note}")
    for err in errors:
        print(f"  [ERROR] {err}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(run_checks())
