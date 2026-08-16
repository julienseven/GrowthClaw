"""
Solana adapter — async polling + transaction inspection.

Responsibilities:
  1. Poll ``get_signatures_for_address`` for an agent wallet.
  2. Inspect each valid transaction for a native SOL transfer meeting a
     baseline amount (default 0.05 SOL).
  3. Parse the attached Memo Program instruction payload

         "ProjectName | Project Description"

     and surface it to the caller (which routes it to the OpenAI engine).

Design notes:
  * Uses ``solders``/``solana-py`` with ``encoding="jsonParsed"`` so the
    RPC returns structured ``parsed`` instructions when it can, falling back
    to base64 ``data`` decoding when it cannot.
  * Determines the SOL amount actually delivered to the agent wallet using
    ``meta.preBalances``/``meta.postBalances`` deltas (authoritative) and, if
    those are absent, parses System Program transfer instructions.
  * Only transactions whose ``meta.err`` is null are inspected.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.signature import Signature

from app.core.solana_utils import (
    MEMO_PROGRAM_ID,
    MemoPayloadError,
    lamports_to_sol,
    parse_memo_payload,
)

# Default baseline: an incoming transfer must deliver at least this many SOL.
DEFAULT_MIN_SOL = 0.05

# Bounded limits so one poll can never spin out of control.
DEFAULT_SIGNATURE_LIMIT = 20


class TransactionInspectionError(RuntimeError):
    """Base class for all inspection failures."""


class TransactionFetchError(TransactionInspectionError):
    """get_transaction returned an empty/None value (skipped/forks/pruned)."""


class TransactionSkipError(TransactionInspectionError):
    """Transaction is valid but does not meet the growth criteria.

    Expected/benign during normal operation — it means "not our customer".
    """


@dataclass(frozen=True)
class GrowthSubmission:
    """A validated inbound submission (SOL + memo) ready for the AI engine."""

    signature: str
    from_wallet: str
    sol_amount: float
    memo_payload: str
    project_name: str
    description: str


class SolanaAdapter:
    """Async wrapper around ``AsyncClient`` dedicated to growth-submission polling."""

    def __init__(
        self,
        wallet_address: str,
        rpc_url: str,
        *,
        min_sol: float = DEFAULT_MIN_SOL,
        signature_limit: int = DEFAULT_SIGNATURE_LIMIT,
        commitment: str = "confirmed",
    ) -> None:
        if min_sol <= 0:
            raise ValueError("min_sol must be > 0")
        if not 1 <= signature_limit <= 1000:
            raise ValueError("signature_limit must be within [1, 1000]")

        try:
            self._wallet_pubkey: Pubkey = Pubkey.from_string(wallet_address)
        except Exception as exc:  # solders raises various decode errors
            raise ValueError(f"Invalid wallet address: {wallet_address!r}") from exc

        self._wallet_str = str(self._wallet_pubkey)
        self._rpc_url = rpc_url
        self._min_sol = float(min_sol)
        self._signature_limit = signature_limit
        self._commitment = commitment
        self._client: AsyncClient | None = None

    async def __aenter__(self) -> SolanaAdapter:
        await self.connect()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

    async def connect(self) -> None:
        if self._client is None:
            self._client = AsyncClient(self._rpc_url, commitment=self._commitment)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected()

    @property
    def wallet_address(self) -> str:
        return self._wallet_str

    async def poll_signatures(self, *, until_signature: str | None = None) -> list[str]:
        """Return recent transaction signatures for the agent wallet.

        ``until_signature`` acts as an "after this" cursor: only signatures
        strictly newer than it are returned, so the caller can resume where
        it left off without re-processing old transactions.
        """
        if self._client is None:
            raise RuntimeError("SolanaAdapter is not connected")

        response = await self._client.get_signatures_for_address(
            self._wallet_pubkey,
            limit=self._signature_limit,
        )
        if response.value is None:
            return []

        signatures: list[str] = []
        for info in response.value:
            sig = str(info.signature)
            # Cursor reached -> stop (list is newest-first).
            if until_signature is not None and sig == until_signature:
                break
            signatures.append(sig)
        return signatures

    async def inspect_transaction(self, signature: str) -> GrowthSubmission | None:
        """Inspect a single transaction.

        Returns a ``GrowthSubmission`` when the transaction is a valid
        qualifying submission, otherwise ``None``. Raises
        ``TransactionInspectionError`` subclasses only for hard failures
        (the poll loop catches benign skips separately).
        """
        if self._client is None:
            raise RuntimeError("SolanaAdapter is not connected")

        try:
            sig = Signature.from_string(signature)
        except Exception as exc:
            raise TransactionFetchError(f"Invalid signature {signature!r}") from exc

        resp = await self._client.get_transaction(
            sig,
            encoding="jsonParsed",
            max_supported_transaction_version=0,
        )
        if resp.value is None:
            raise TransactionFetchError(
                f"Transaction {signature!r} has no detail (skipped/pruned/forked)"
            )

        # solana-py decodes the JSON RPC response into a solders dataclass
        # (EncodedConfirmedTransactionWithStatusMeta). Normalise it into a
        # plain dict so the rest of the parser is encoding-agnostic.
        tx = _normalize_tx(resp.value)
        meta = tx.get("meta") or {}
        if meta.get("err") is not None:
            raise TransactionSkipError(f"Transaction {signature!r} failed on-chain")

        sol_amount, from_wallet, account_index = self._extract_sol_transfer(tx, signature)

        if from_wallet == self._wallet_str:
            raise TransactionSkipError(
                f"Transaction {signature!r}: SOL originated from the agent wallet (outbound)"
            )

        if sol_amount < self._min_sol:
            raise TransactionSkipError(
                f"Transaction {signature!r}: {sol_amount:.6f} SOL below "
                f"{self._min_sol} SOL baseline"
            )

        memo_payload = self._extract_memo_payload(tx, signature)
        try:
            parsed = parse_memo_payload(memo_payload)
        except MemoPayloadError as exc:
            raise TransactionSkipError(
                f"Transaction {signature!r}: invalid memo layout ({exc})"
            ) from exc

        return GrowthSubmission(
            signature=signature,
            from_wallet=from_wallet,
            sol_amount=round(sol_amount, 9),
            memo_payload=memo_payload,
            project_name=parsed.project_name,
            description=parsed.description,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_sol_transfer(
        self, tx: dict[str, Any], signature: str
    ) -> tuple[float, str, int]:
        """Return (sol_amount, from_wallet, account_index).

        Primary method: balance deltas from ``meta.preBalances`` /
        ``meta.postBalances`` (authoritative for the *net* SOL received).
        Fallback: parse System Program transfer instructions.
        """
        message = tx.get("transaction", {}).get("message", {})
        account_keys = self._resolve_account_keys(message)
        agent_index = self._find_agent_index(account_keys)

        if agent_index is None:
            raise TransactionSkipError(
                f"Transaction {signature!r}: agent wallet not an account in tx"
            )

        meta = tx.get("meta") or {}
        pre = meta.get("preBalances")
        post = meta.get("postBalances")

        if _is_list_of_int(pre) and _is_list_of_int(post) and agent_index < len(pre) and agent_index < len(post):
            delta = post[agent_index] - pre[agent_index]
            if delta > 0:
                from_wallet = self._find_sender_from_balances(
                    account_keys, pre, post, exclude=agent_index
                )
                return lamports_to_sol(delta), from_wallet or "unknown", agent_index

        # Fallback: inspect parsed transfer instructions.
        instructions = message.get("instructions", [])
        for ix in instructions:
            parsed = ix.get("parsed")
            if not parsed or parsed.get("type") != "transfer":
                continue
            info = parsed.get("info") or {}
            destination = info.get("destination")
            if destination == self._wallet_str:
                lamports = int(info.get("lamports", 0))
                source = info.get("source") or "unknown"
                return lamports_to_sol(lamports), source, agent_index

        raise TransactionSkipError(
            f"Transaction {signature!r}: no incoming SOL transfer to agent wallet"
        )

    def _extract_memo_payload(self, tx: dict[str, Any], signature: str) -> str:
        """Extract the raw memo text from the Memo Program instruction."""
        message = tx.get("transaction", {}).get("message", {})
        instructions = message.get("instructions", [])
        account_keys = self._resolve_account_keys(message)

        # Prefer top-level instructions.
        for ix in instructions:
            program = self._resolve_program_id(ix, account_keys)
            if program == MEMO_PROGRAM_ID:
                raw = self._decode_memo_data(ix)
                if raw is not None:
                    return raw

        # Some wallets nest the memo under inner instructions (Meta).
        meta = tx.get("meta") or {}
        for group in meta.get("innerInstructions", []) or []:
            for ix in group.get("instructions", []) or []:
                program = self._resolve_program_id(ix, account_keys)
                if program == MEMO_PROGRAM_ID:
                    raw = self._decode_memo_data(ix)
                    if raw is not None:
                        return raw

        raise TransactionSkipError(
            f"Transaction {signature!r}: no Memo Program instruction found"
        )

    @staticmethod
    def _decode_memo_data(ix: dict[str, Any]) -> str | None:
        """Decode memo instruction data from jsonParsed form.

        The Memo Program never "parses" its data, so it arrives as base64
        under either ``data`` (a str) or ``data[0]`` (a list, when the
        instruction's accounts were resolvable).
        """
        parsed = ix.get("parsed")
        if isinstance(parsed, str):
            return parsed
        if isinstance(parsed, dict) and isinstance(parsed.get("memo"), str):
            return parsed["memo"]

        data = ix.get("data")
        encoded = None
        if isinstance(data, str):
            encoded = data
        elif isinstance(data, list | tuple) and data:
            encoded = data[0]

        if not encoded:
            return None
        try:
            return base64.b64decode(encoded).decode("utf-8")
        except Exception:
            return None

    @staticmethod
    def _resolve_account_keys(message: dict[str, Any]) -> list[str]:
        """Return a list of account pubkeys (strings) for the transaction."""
        keys = message.get("accountKeys") or message.get("accounts") or []
        resolved: list[str] = []
        for k in keys:
            if isinstance(k, str):
                resolved.append(k)
            elif isinstance(k, dict):
                resolved.append(k.get("pubkey") or k.get("publicKey") or "")
            else:
                resolved.append(str(k))
        return resolved

    @staticmethod
    def _resolve_program_id(
        ix: dict[str, Any], account_keys: list[str]
    ) -> str | None:
        """Return the string program id for a parsed instruction."""
        pid = ix.get("programId") or ix.get("program_id")
        if isinstance(pid, str):
            return pid
        # programIdIndex case (older encoding) references account list.
        idx = ix.get("programIdIndex")
        if isinstance(idx, int) and 0 <= idx < len(account_keys):
            return account_keys[idx]
        return None

    def _find_agent_index(self, account_keys: list[str]) -> int | None:
        try:
            return account_keys.index(self._wallet_str)
        except ValueError:
            return None

    @staticmethod
    def _find_sender_from_balances(
        account_keys: list[str],
        pre: list[int],
        post: list[int],
        *,
        exclude: int,
    ) -> str | None:
        """Heuristically identify the sender as the account whose balance
        decreased the most (excluding the agent/recipient)."""
        best_idx = -1
        best_decrease = 0
        for i in range(min(len(account_keys), len(pre), len(post))):
            if i == exclude:
                continue
            decrease = pre[i] - post[i]
            if decrease > best_decrease:
                best_decrease = decrease
                best_idx = i
        return account_keys[best_idx] if best_idx >= 0 else None


def _is_list_of_int(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(v, int) for v in value)


def _normalize_tx(value: Any) -> dict[str, Any]:
    """Normalize a ``get_transaction`` value into a plain dict.

    With ``solana-py`` 0.36.x and ``encoding="jsonParsed"`` the RPC value is
    eagerly decoded into a solders dataclass (``EncodedConfirmedTransaction
    WithStatusMeta``), which exposes ``to_json()``. We round-trip that to a
    dict so the rest of the inspection logic is agnostic to the underlying
    serialization. If the caller already handed us a mapping, return it as-is.
    """
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_json"):
        jsoned = value.to_json()
        if isinstance(jsoned, str):
            return json.loads(jsoned)
    # Last resort: implicit object<->dict via json serialization.
    try:
        return json.loads(json.dumps(value))
    except (TypeError, ValueError):
        raise TransactionInspectionError(
            f"Unable to normalize transaction value of type {type(value)!r}"
        ) from None
