"""
The $GROWTH agent — the background asyncio loop.

Periodically polls the agent wallet for new signatures, inspects each
qualifying transaction (baseline SOL + Memo Program payload), and routes the
project description to the OpenAI engine for a viral marketing post.

Graceful shutdown is wired to ``SIGINT``/``SIGTERM`` via ``asyncio``. The
loop is resilient: RPC hiccups and bad transactions are logged and skipped
without killing the process.
"""

from __future__ import annotations

import asyncio
import signal

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.domain.ai_engine import AIEngineError, OpenAIEngine
from app.domain.solana import (
    SolanaAdapter,
    TransactionFetchError,
    TransactionSkipError,
)

MIN_POLL_SECONDS = 2.0


class GrowthAgent:
    def __init__(self, *, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._log = get_logger("growth.agent")

        s = self._settings
        self._adapter = SolanaAdapter(
            wallet_address=s.solana.wallet_address,
            rpc_url=s.solana.rpc_url,
            min_sol=s.solana.min_sol_amount,
            signature_limit=s.solana.signature_limit,
        )

        if not s.openai.api_key:
            self._engine: OpenAIEngine | None = None
            self._log.warning("OPENAI_API_KEY unset — AI engine disabled (dry-run)")
        else:
            self._engine = OpenAIEngine(
                api_key=s.openai.api_key,
                model=s.openai.model,
                temperature=s.openai.temperature,
                max_tokens=s.openai.max_tokens,
                timeout_seconds=s.openai.timeout_seconds,
            )

        self._poll_interval = max(MIN_POLL_SECONDS, s.worker.poll_interval_seconds)
        self._shutdown_requested = False

    async def run(self) -> None:
        """Run the poll loop until a shutdown signal is received."""
        self._log.info(
            "growth_agent.starting",
            wallet=self._adapter.wallet_address,
            poll_interval=self._poll_interval,
            baseline_sol=self._settings.solana.min_sol_amount,
        )
        async with self._adapter:
            last_seen: str | None = None
            while not self._shutdown_requested:
                try:
                    last_seen = await self._poll_once(last_seen)
                except Exception as exc:  # keep the loop alive at all costs
                    self._log.exception(
                        "growth_agent.poll_error", error=str(exc)
                    )
                await asyncio.sleep(self._poll_interval)

        if self._engine is not None:
            await self._engine.close()
        self._log.info("growth_agent.stopped")

    async def _poll_once(self, until_signature: str | None) -> str | None:
        """One iteration: fetch signatures and process new ones.

        Returns the newest signature seen (used as the next cursor), or the
        previous cursor if nothing new arrived.
        """
        signatures = await self._adapter.poll_signatures(
            until_signature=until_signature
        )
        if not signatures:
            return until_signature

        newest = signatures[0]
        # Poll returns newest-first; process oldest-first for determinism.
        for signature in reversed(signatures):
            await self._process_signature(signature)

        self._log.info("growth_agent.polled", processed=len(signatures))
        return newest

    async def _process_signature(self, signature: str) -> None:
        try:
            submission = await self._adapter.inspect_transaction(signature)
        except TransactionSkipError as exc:
            self._log.debug("growth_agent.skip", signature=signature, reason=str(exc))
            return
        except TransactionFetchError as exc:
            self._log.warning(
                "growth_agent.inspect_failed", signature=signature, reason=str(exc)
            )
            return

        if submission is None:
            return

        self._log.info(
            "growth_agent.submission_found",
            signature=submission.signature,
            from_wallet=submission.from_wallet,
            sol_amount=submission.sol_amount,
            project_name=submission.project_name,
        )

        if self._engine is None:
            self._log.info(
                "growth_agent.dry_run",
                project_name=submission.project_name,
                description=submission.description,
            )
            return

        try:
            post = await self._engine.generate_marketing_post(
                submission.project_name, submission.description
            )
        except AIEngineError as exc:
            self._log.error(
                "growth_agent.ai_error",
                signature=submission.signature,
                reason=str(exc),
            )
            return

        self._log.info(
            "growth_agent.post_generated",
            signature=submission.signature,
            project_name=submission.project_name,
            post=post,
            post_length=len(post),
        )

    def request_shutdown(self) -> None:
        self._shutdown_requested = True


async def _main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    agent = GrowthAgent(settings=settings)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, agent.request_shutdown)
        except (NotImplementedError, RuntimeError):
            # Non-Unix / non-main-thread: fall back to no signal handler.
            pass

    await agent.run()


def main() -> None:
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
