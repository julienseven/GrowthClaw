"""
Test suite for the transaction agent infrastructure.

Tests:
- Memo parsing and validation
- Project metadata extraction
- Marketing post generation
- Result storage and retrieval
"""
import pytest
from datetime import datetime

from agents.transaction_agent import ProjectMetadata, ProcessedTransaction
from processors.memo_processor import MemoProcessor, ParsedMemo
from services.result_manager import ResultManager, Result
from utils.validators import (
    is_valid_solana_address,
    is_valid_transaction_hash,
    validate_memo_string,
    validate_project_metadata,
)


class TestMemoProcessing:
    """Test memo extraction and parsing."""

    def test_valid_memo_format(self):
        """Test parsing valid memo format."""
        memo = "SolanaAI | AI-powered trading bot for Solana blockchain"
        result = ProjectMetadata.from_memo(memo)

        assert result is not None
        assert result.name == "SolanaAI"
        assert result.description == "AI-powered trading bot for Solana blockchain"

    def test_memo_with_extra_spaces(self):
        """Test memo parsing with extra whitespace."""
        memo = "  MyProject  |  A great project  "
        result = ProjectMetadata.from_memo(memo)

        assert result is not None
        assert result.name == "MyProject"
        assert result.description == "A great project"

    def test_memo_missing_delimiter(self):
        """Test parsing memo without delimiter."""
        memo = "ProjectWithoutDelimiter"
        result = ProjectMetadata.from_memo(memo)

        assert result is None

    def test_memo_empty_name(self):
        """Test memo with empty project name."""
        memo = " | Description only"
        result = ProjectMetadata.from_memo(memo)

        assert result is None

    def test_memo_empty_description(self):
        """Test memo with empty description."""
        memo = "ProjectName | "
        result = ProjectMetadata.from_memo(memo)

        assert result is None

    def test_memo_name_too_long(self):
        """Test memo with excessively long name."""
        memo = "A" * 101 + " | Description"
        result = ProjectMetadata.from_memo(memo)

        assert result is None

    def test_memo_description_too_long(self):
        """Test memo with excessively long description."""
        memo = "ProjectName | " + "A" * 1001
        result = ProjectMetadata.from_memo(memo)

        assert result is None


class TestMemoProcessorValidation:
    """Test MemoProcessor validation functions."""

    def test_parse_valid_memo(self):
        """Test ParsedMemo with valid input."""
        memo = "TestProject | This is a test"
        result = MemoProcessor.parse_memo(memo)

        assert result.is_valid
        assert result.project_name == "TestProject"
        assert result.project_description == "This is a test"
        assert result.error_message is None

    def test_parse_memo_empty_text(self):
        """Test parsing empty memo."""
        result = MemoProcessor.parse_memo("")

        assert not result.is_valid
        assert result.error_message == "Memo text is empty"

    def test_parse_memo_invalid_type(self):
        """Test parsing non-string memo."""
        result = MemoProcessor.parse_memo(12345)

        assert not result.is_valid
        assert "must be string" in result.error_message

    def test_parse_memo_missing_delimiter(self):
        """Test parsing memo without delimiter."""
        result = MemoProcessor.parse_memo("NoDelimiterHere")

        assert not result.is_valid
        assert "missing delimiter" in result.error_message

    def test_parse_memo_too_large(self):
        """Test parsing memo exceeding size limit."""
        large_memo = "A" * 567 + " | B"
        result = MemoProcessor.parse_memo(large_memo)

        assert not result.is_valid
        assert "exceeds max size" in result.error_message

    def test_parse_memo_with_null_bytes(self):
        """Test parsing memo with null bytes."""
        memo = "Project\x00 | Description"
        result = MemoProcessor.parse_memo(memo)

        assert not result.is_valid
        assert "null bytes" in result.error_message

    def test_validate_project_data_valid(self):
        """Test project data validation with valid input."""
        is_valid, error = MemoProcessor.validate_project_data(
            "TestProject", "A valid test project description"
        )

        assert is_valid
        assert error is None

    def test_validate_project_data_short_name(self):
        """Test validation with too-short name."""
        is_valid, error = MemoProcessor.validate_project_data("A", "Description")

        assert not is_valid

    def test_validate_project_data_short_description(self):
        """Test validation with too-short description."""
        is_valid, error = MemoProcessor.validate_project_data("Project", "Bad")

        assert not is_valid


class TestValidators:
    """Test input validators."""

    def test_valid_solana_address(self):
        """Test valid Solana address validation."""
        # Real example addresses from Solana
        assert is_valid_solana_address("11111111111111111111111111111111")
        assert is_valid_solana_address("So11111111111111111111111111111111111112")

    def test_invalid_solana_address_empty(self):
        """Test invalid address (empty)."""
        assert not is_valid_solana_address("")

    def test_invalid_solana_address_too_short(self):
        """Test invalid address (too short)."""
        assert not is_valid_solana_address("11111111111111111111111111")

    def test_invalid_solana_address_bad_characters(self):
        """Test invalid address (contains invalid base58 chars)."""
        assert not is_valid_solana_address("0OIl11111111111111111111111111111111111")

    def test_valid_transaction_hash(self):
        """Test valid transaction signature."""
        # Valid 88-character base58 signature
        sig = "5" * 88
        assert is_valid_transaction_hash(sig)

    def test_invalid_transaction_hash_too_short(self):
        """Test invalid transaction hash (too short)."""
        assert not is_valid_transaction_hash("5" * 50)

    def test_invalid_transaction_hash_too_long(self):
        """Test invalid transaction hash (too long)."""
        assert not is_valid_transaction_hash("5" * 100)

    def test_validate_memo_string_valid(self):
        """Test valid memo string."""
        is_valid, error = validate_memo_string("Test memo")

        assert is_valid
        assert error is None

    def test_validate_memo_string_empty(self):
        """Test empty memo string."""
        is_valid, error = validate_memo_string("")

        assert not is_valid

    def test_validate_memo_string_with_null_bytes(self):
        """Test memo with null bytes."""
        is_valid, error = validate_memo_string("Test\x00memo")

        assert not is_valid

    def test_validate_project_metadata_valid(self):
        """Test valid project metadata."""
        is_valid, error = validate_project_metadata(
            "SolanaAI", "AI-powered trading bot for Solana"
        )

        assert is_valid
        assert error is None

    def test_validate_project_metadata_invalid_name_length(self):
        """Test invalid name length."""
        is_valid, error = validate_project_metadata("A", "Valid description")

        assert not is_valid

    def test_validate_project_metadata_invalid_description_length(self):
        """Test invalid description length."""
        is_valid, error = validate_project_metadata("ValidName", "Bad")

        assert not is_valid


class TestResultStorage:
    """Test result storage and retrieval."""

    def test_add_and_retrieve_results(self):
        """Test adding and retrieving results."""
        manager = ResultManager()

        result = Result(
            signature="5" * 88,
            timestamp="2024-01-15T10:00:00",
            project_name="TestProject",
            project_description="A test project",
            marketing_post="Test post",
            post_length=9,
        )

        manager.add_result(result)

        results = manager.get_results(limit=10)
        assert len(results) == 1
        assert results[0]["project_name"] == "TestProject"

    def test_get_successful_results(self):
        """Test filtering successful results."""
        manager = ResultManager()

        # Add successful result
        result1 = Result(
            signature="5" * 88,
            timestamp="2024-01-15T10:00:00",
            project_name="Project1",
            project_description="Description",
            marketing_post="Post",
            post_length=4,
        )

        # Add failed result
        result2 = Result(
            signature="6" * 88,
            timestamp="2024-01-15T10:01:00",
            project_name="Project2",
            project_description="Description",
            marketing_post="",
            post_length=0,
            error="Parse error",
        )

        manager.add_result(result1)
        manager.add_result(result2)

        successful = manager.get_successful_results(limit=10)
        assert len(successful) == 1
        assert successful[0]["project_name"] == "Project1"

    def test_get_statistics(self):
        """Test statistics generation."""
        manager = ResultManager()

        # Add results
        for i in range(5):
            result = Result(
                signature=str(i) * 88,
                timestamp="2024-01-15T10:00:00",
                project_name=f"Project{i}",
                project_description="Description",
                marketing_post=f"Post {i}",
                post_length=6,
            )
            manager.add_result(result)

        stats = manager.get_statistics()

        assert stats["total_processed"] == 5
        assert stats["total_successful"] == 5
        assert stats["success_rate"] == 100.0

    def test_get_results_by_project(self):
        """Test filtering results by project."""
        manager = ResultManager()

        # Add results for different projects
        for project_name in ["Project1", "Project2", "Project1"]:
            result = Result(
                signature="5" * 88,
                timestamp="2024-01-15T10:00:00",
                project_name=project_name,
                project_description="Description",
                marketing_post="Post",
                post_length=4,
            )
            manager.add_result(result)

        project_results = manager.get_results_by_project("Project1")
        assert len(project_results) == 2

    def test_get_marketing_posts(self):
        """Test retrieving marketing posts."""
        manager = ResultManager()

        posts = ["Post 1", "Post 2", "Post 3"]
        for i, post in enumerate(posts):
            result = Result(
                signature=str(i) * 88,
                timestamp="2024-01-15T10:00:00",
                project_name=f"Project{i}",
                project_description="Description",
                marketing_post=post,
                post_length=len(post),
            )
            manager.add_result(result)

        retrieved_posts = manager.get_marketing_posts(limit=10)
        assert len(retrieved_posts) == 3
        assert retrieved_posts == posts

    def test_clear_results(self):
        """Test clearing results."""
        manager = ResultManager()

        # Add results
        for i in range(5):
            result = Result(
                signature=str(i) * 88,
                timestamp="2024-01-15T10:00:00",
                project_name=f"Project{i}",
                project_description="Description",
                marketing_post="Post",
                post_length=4,
            )
            manager.add_result(result)

        assert len(manager.results) == 5

        cleared = manager.clear_results()
        assert cleared == 5
        assert len(manager.results) == 0


# Integration test placeholder
class TestIntegration:
    """Integration tests (require real Solana/OpenAI access)."""

    @pytest.mark.skip(reason="Requires live Solana/OpenAI connections")
    async def test_full_transaction_pipeline(self):
        """Test complete transaction processing pipeline."""
        # This would require:
        # 1. Real Solana wallet with transactions
        # 2. Valid OpenAI API key
        # 3. Test transaction with memo in correct format
        pass
