"""
Input validation utilities for Solana addresses and transactions.

Production-ready validators with comprehensive error handling.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Solana address constraints
SOLANA_ADDRESS_PATTERN = re.compile(r"^[1-9A-HJ-NP-Z]{32,34}$")  # Base58
TRANSACTION_SIGNATURE_PATTERN = re.compile(r"^[1-9A-HJ-NP-Z]{87,88}$")  # Base58


def is_valid_solana_address(address: str) -> bool:
    """
    Validate Solana base58 address format.

    Solana addresses are base58-encoded 32-byte public keys.
    Valid addresses:
    - 32-34 characters in length
    - Use base58 alphabet (no 0, O, I, l)

    Args:
        address: Address string to validate

    Returns:
        True if valid Solana address, False otherwise
    """
    if not address or not isinstance(address, str):
        logger.debug(f"Invalid address type: {type(address)}")
        return False

    address = address.strip()

    # Check length
    if len(address) < 32 or len(address) > 34:
        logger.debug(f"Address length invalid: {len(address)}")
        return False

    # Check base58 pattern
    if not SOLANA_ADDRESS_PATTERN.match(address):
        logger.debug(f"Address does not match base58 pattern: {address[:10]}...")
        return False

    # Additional validation: try with solana-py if available
    try:
        from solana.publickey import PublicKey

        PublicKey(address)
        return True
    except Exception as e:
        logger.debug(f"Solana PublicKey validation failed: {e}")
        return False


def is_valid_token_address(address: str) -> bool:
    """
    Validate SPL token mint address.

    Token addresses are also base58-encoded 32-byte keys,
    so validation is identical to Solana addresses.

    Args:
        address: Token address to validate

    Returns:
        True if valid token address, False otherwise
    """
    return is_valid_solana_address(address)


def is_valid_transaction_hash(tx_hash: str) -> bool:
    """
    Validate Solana transaction signature format.

    Transaction signatures are base58-encoded and typically 87-88 characters.

    Args:
        tx_hash: Transaction signature to validate

    Returns:
        True if valid transaction hash, False otherwise
    """
    if not tx_hash or not isinstance(tx_hash, str):
        logger.debug(f"Invalid transaction hash type: {type(tx_hash)}")
        return False

    tx_hash = tx_hash.strip()

    # Check length (transaction signatures are typically 87-88 chars)
    if len(tx_hash) < 87 or len(tx_hash) > 88:
        logger.debug(f"Transaction hash length invalid: {len(tx_hash)}")
        return False

    # Check base58 pattern
    if not TRANSACTION_SIGNATURE_PATTERN.match(tx_hash):
        logger.debug(f"Transaction hash does not match pattern: {tx_hash[:10]}...")
        return False

    return True


def validate_memo_string(memo: str, max_length: int = 566) -> tuple[bool, Optional[str]]:
    """
    Validate memo string for Solana Memo Program.

    Args:
        memo: Memo string to validate
        max_length: Maximum memo length (Solana limit is 566 bytes)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not memo:
        return False, "Memo cannot be empty"

    if not isinstance(memo, str):
        return False, f"Memo must be string, got {type(memo)}"

    if len(memo) > max_length:
        return False, f"Memo exceeds max length: {len(memo)} > {max_length}"

    # Check for null bytes
    if "\0" in memo:
        return False, "Memo contains null bytes"

    return True, None


def validate_project_metadata(
    project_name: str, project_description: str
) -> tuple[bool, Optional[str]]:
    """
    Validate project metadata for AI processing.

    Args:
        project_name: Project name
        project_description: Project description

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not project_name or not isinstance(project_name, str):
        return False, "Project name must be non-empty string"

    if not project_description or not isinstance(project_description, str):
        return False, "Project description must be non-empty string"

    # Check name length
    if len(project_name) < 2:
        return False, "Project name too short (minimum 2 characters)"

    if len(project_name) > 100:
        return False, "Project name too long (maximum 100 characters)"

    # Check description length
    if len(project_description) < 5:
        return False, "Project description too short (minimum 5 characters)"

    if len(project_description) > 1000:
        return False, "Project description too long (maximum 1000 characters)"

    # Check for suspicious patterns
    if project_name.count("|") > 1 or project_description.count("|") > 1:
        return False, "Metadata contains suspicious delimiter patterns"

    return True, None
