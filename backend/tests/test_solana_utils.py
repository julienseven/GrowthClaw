"""Unit tests for memo payload parsing + SOL conversion (pure logic)."""

from __future__ import annotations

import pytest

from app.core.solana_utils import (
    LAMPORTS_PER_SOL,
    MemoPayload,
    MemoPayloadError,
    lamports_to_sol,
    parse_memo_payload,
)


def test_parse_valid_payload():
    parsed = parse_memo_payload("SolRocket | Breakthrough DeFi on Solana")
    assert parsed == MemoPayload(
        project_name="SolRocket", description="Breakthrough DeFi on Solana"
    )


def test_parse_trims_whitespace():
    parsed = parse_memo_payload("  SolRocket   |   Breakthrough DeFi   ")
    assert parsed.project_name == "SolRocket"
    assert parsed.description == "Breakthrough DeFi"


def test_parse_multiple_separators_uses_first():
    parsed = parse_memo_payload("SolRocket | a description | with pipes")
    assert parsed.project_name == "SolRocket"
    assert parsed.description == "a description | with pipes"


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "",
        "   ",
        "no separator here",
        " | missing name",
        "name | ",
        "| missing everything",
    ],
)
def test_parse_invalid_payload_raises(bad):
    with pytest.raises(MemoPayloadError):
        parse_memo_payload(bad)


def test_lamports_to_sol():
    assert lamports_to_sol(0) == 0.0
    assert lamports_to_sol(LAMPORTS_PER_SOL) == 1.0
    assert lamports_to_sol(50_000_000) == 0.05
