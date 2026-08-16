"""Core utilities: memo payload parsing + SOL amount helpers (pure logic)."""

from __future__ import annotations

from dataclasses import dataclass

# The Solana Memo Program account id. All Memo Program instructions invoke it.
MEMO_PROGRAM_ID = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"

# The client contract: memo payloads must be "<ProjectName> | <Description>".
MEMO_SEPARATOR = "|"

# 1 SOL = 1_000_000_000 lamports.
LAMPORTS_PER_SOL = 1_000_000_000


@dataclass(frozen=True)
class MemoPayload:
    """A parsed Memo Program payload conforming to the client layout."""

    project_name: str
    description: str


class MemoPayloadError(ValueError):
    """Raised when a memo payload does not conform to the client layout."""


def _clean_segment(value: str) -> str:
    return value.strip()


def parse_memo_payload(raw_memo: str | None) -> MemoPayload:
    """Parse a Memo Program payload into a ``MemoPayload``.

    The strict client layout is::

        "<ProjectName> | <Description>"

    Edge-case handling:
      * ``None`` / empty string                -> ``MemoPayloadError``
      * missing separator                      -> ``MemoPayloadError``
      * multiple separators                    -> split on the *first* only
      * leading/trailing whitespace on fields  -> stripped
      * blank ``ProjectName`` or description   -> ``MemoPayloadError``
    """
    if not raw_memo:
        raise MemoPayloadError("memo payload is empty")

    if MEMO_SEPARATOR not in raw_memo:
        raise MemoPayloadError(
            f"memo payload missing separator {MEMO_SEPARATOR!r}: {raw_memo!r}"
        )

    name_part, desc_part = raw_memo.split(MEMO_SEPARATOR, 1)

    project_name = _clean_segment(name_part)
    description = _clean_segment(desc_part)

    if not project_name:
        raise MemoPayloadError("ProjectName is empty after parsing")
    if not description:
        raise MemoPayloadError("Description is empty after parsing")

    return MemoPayload(project_name=project_name, description=description)


def lamports_to_sol(lamports: int | float) -> float:
    """Convert lamports to SOL."""
    return float(lamports) / LAMPORTS_PER_SOL
