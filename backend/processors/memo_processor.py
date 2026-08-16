"""
Memo Processor - Specialized handler for Solana Memo Program instruction parsing.

This module provides robust parsing and validation for memo instructions,
with comprehensive error handling for edge cases.
"""
import logging
import base64
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Constants for memo parsing
MEMO_PROGRAM_ID = "MemoSq4gDiRynqzStXoESKyXKpy4xjqJMmLeQMwr08"
MEMO_DELIMITER = "|"
MAX_MEMO_SIZE = 566  # Solana memo instruction data limit
MAX_MEMO_DISPLAY = 500
MIN_MEMO_SIZE = 3  # "a|b" minimum


@dataclass
class ParsedMemo:
    """Result of memo parsing."""
    raw_text: str
    is_valid: bool
    project_name: Optional[str] = None
    project_description: Optional[str] = None
    error_message: Optional[str] = None
    encoding_type: str = "utf-8"


class MemoProcessor:
    """
    Specialized processor for Solana Memo Program instructions.

    Handles:
    - Base64 decoding
    - UTF-8 validation
    - Format validation (ProjectName | ProjectDescription)
    - Size constraints
    - Edge case handling
    """

    @staticmethod
    def extract_memo_from_instructions(
        instructions: list[Dict[str, Any]],
    ) -> Optional[str]:
        """
        Extract memo text from transaction instructions.

        Args:
            instructions: List of transaction instructions

        Returns:
            Memo text or None if not found
        """
        if not instructions or not isinstance(instructions, list):
            logger.warning("Invalid instructions format")
            return None

        for instruction in instructions:
            try:
                # Check if this is a Memo Program instruction
                program_id = instruction.get("programId", "")

                if program_id != MEMO_PROGRAM_ID:
                    continue

                # Extract data field
                data = instruction.get("data", "")

                if not data:
                    logger.debug("Empty memo data")
                    continue

                # Try to decode and return
                decoded = MemoProcessor._decode_memo_data(data)
                if decoded:
                    return decoded

            except Exception as e:
                logger.debug(f"Error processing instruction: {e}")
                continue

        return None

    @staticmethod
    def _decode_memo_data(data: Any) -> Optional[str]:
        """
        Decode memo data from various formats.

        Args:
            data: Data field from instruction (could be string, base64, etc.)

        Returns:
            Decoded memo text or None
        """
        if isinstance(data, str):
            # Try base64 decode first
            try:
                decoded = base64.b64decode(data).decode("utf-8", errors="strict")
                return decoded.strip()
            except Exception:
                pass

            # Try direct string
            try:
                return data.strip()
            except Exception:
                pass

        elif isinstance(data, bytes):
            # Try UTF-8 decode
            try:
                return data.decode("utf-8", errors="strict").strip()
            except Exception:
                logger.warning("Failed to decode bytes as UTF-8")
                return None

        return None

    @staticmethod
    def parse_memo(memo_text: str) -> ParsedMemo:
        """
        Parse memo in format: "ProjectName | ProjectDescription"

        Comprehensive error handling for:
        - Missing delimiter
        - Empty fields
        - Size constraints
        - Invalid characters
        - Encoding issues

        Args:
            memo_text: Raw memo text

        Returns:
            ParsedMemo object with validation results
        """
        # Validate input
        if not memo_text:
            return ParsedMemo(
                raw_text="",
                is_valid=False,
                error_message="Memo text is empty",
            )

        if not isinstance(memo_text, str):
            return ParsedMemo(
                raw_text=str(memo_text),
                is_valid=False,
                error_message="Memo must be string",
            )

        memo_text = memo_text.strip()

        # Check size constraints
        if len(memo_text) > MAX_MEMO_SIZE:
            return ParsedMemo(
                raw_text=memo_text,
                is_valid=False,
                error_message=f"Memo exceeds max size: {len(memo_text)} > {MAX_MEMO_SIZE}",
            )

        if len(memo_text) < MIN_MEMO_SIZE:
            return ParsedMemo(
                raw_text=memo_text,
                is_valid=False,
                error_message=f"Memo too short: {len(memo_text)} < {MIN_MEMO_SIZE}",
            )

        # Check for delimiter
        if MEMO_DELIMITER not in memo_text:
            return ParsedMemo(
                raw_text=memo_text,
                is_valid=False,
                error_message=f"Memo missing delimiter '{MEMO_DELIMITER}'",
            )

        # Split on first delimiter only
        try:
            parts = memo_text.split(MEMO_DELIMITER, 1)

            if len(parts) != 2:
                return ParsedMemo(
                    raw_text=memo_text,
                    is_valid=False,
                    error_message="Failed to split memo",
                )

            project_name = parts[0].strip()
            project_description = parts[1].strip()

            # Validate extracted fields
            if not project_name:
                return ParsedMemo(
                    raw_text=memo_text,
                    is_valid=False,
                    error_message="Project name is empty",
                )

            if not project_description:
                return ParsedMemo(
                    raw_text=memo_text,
                    is_valid=False,
                    error_message="Project description is empty",
                )

            # Check project name constraints
            if len(project_name) > 100:
                return ParsedMemo(
                    raw_text=memo_text,
                    is_valid=False,
                    error_message=f"Project name too long: {len(project_name)} > 100",
                )

            # Check description constraints
            if len(project_description) > MAX_MEMO_DISPLAY:
                return ParsedMemo(
                    raw_text=memo_text,
                    is_valid=False,
                    error_message=f"Description too long: {len(project_description)} > {MAX_MEMO_DISPLAY}",
                )

            # Validate characters (no null bytes, etc.)
            if "\0" in project_name or "\0" in project_description:
                return ParsedMemo(
                    raw_text=memo_text,
                    is_valid=False,
                    error_message="Memo contains null bytes",
                )

            # All validations passed
            return ParsedMemo(
                raw_text=memo_text,
                is_valid=True,
                project_name=project_name,
                project_description=project_description,
            )

        except Exception as e:
            return ParsedMemo(
                raw_text=memo_text,
                is_valid=False,
                error_message=f"Error parsing memo: {str(e)}",
            )

    @staticmethod
    def validate_project_data(
        project_name: str, project_description: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validate project data for AI processing.

        Args:
            project_name: Project name
            project_description: Project description

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not project_name or not isinstance(project_name, str):
            return False, "Invalid project name"

        if not project_description or not isinstance(project_description, str):
            return False, "Invalid project description"

        # Check lengths for AI processing
        if len(project_name) < 2:
            return False, "Project name too short"

        if len(project_description) < 5:
            return False, "Project description too short"

        # Check for suspicious patterns
        suspicious_patterns = [
            "\\x00",  # Null byte
            "\x00",
            "...",  # Too many dots
            "|||",  # Too many delimiters
        ]

        combined = f"{project_name} {project_description}"
        for pattern in suspicious_patterns:
            if pattern in combined:
                return False, f"Suspicious pattern detected: {pattern}"

        return True, None
