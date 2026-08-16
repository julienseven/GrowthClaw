"""
Result Manager - Handles storage and retrieval of processed transactions.

This service provides:
- In-memory result caching
- Result filtering and querying
- Persistence layer integration (ready for Redis/DB)
- Result statistics and analytics
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Result:
    """Stored transaction processing result."""
    signature: str
    timestamp: str
    project_name: str
    project_description: str
    marketing_post: str
    post_length: int
    sentiment: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    payer: Optional[str] = None
    lamports_transferred: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ResultManager:
    """
    Manages storage and retrieval of transaction processing results.

    Features:
    - In-memory caching
    - Result filtering
    - Statistics collection
    - Ready for Redis/Database integration
    """

    def __init__(self, max_results: int = 10000):
        """
        Initialize result manager.

        Args:
            max_results: Maximum results to keep in memory
        """
        self.max_results = max_results
        self.results: List[Result] = []
        self.metadata = {
            "total_processed": 0,
            "total_successful": 0,
            "total_errors": 0,
            "avg_post_length": 0,
            "last_processed_time": None,
        }

    def add_result(self, result: Result) -> None:
        """
        Add a processed transaction result.

        Args:
            result: Result object to store
        """
        self.results.append(result)

        # Trim if exceeds max
        if len(self.results) > self.max_results:
            self.results = self.results[-self.max_results:]

        # Update metadata
        self.metadata["total_processed"] += 1
        if result.error is None:
            self.metadata["total_successful"] += 1
        else:
            self.metadata["total_errors"] += 1

        self.metadata["last_processed_time"] = datetime.now().isoformat()

        # Update average post length
        successful_posts = [
            r.post_length for r in self.results if r.error is None and r.post_length > 0
        ]
        if successful_posts:
            self.metadata["avg_post_length"] = sum(successful_posts) / len(
                successful_posts
            )

        logger.debug(f"Result stored: {result.signature[:16]}...")

    def get_results(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get stored results with pagination.

        Args:
            limit: Number of results to return
            offset: Starting offset

        Returns:
            List of result dictionaries
        """
        start = max(0, len(self.results) - offset - limit)
        end = max(0, len(self.results) - offset)
        return [r.to_dict() for r in self.results[start:end]]

    def get_recent_results(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get results from the last N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of recent result dictionaries
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent = [
            r
            for r in self.results
            if datetime.fromisoformat(r.timestamp) > cutoff_time
        ]

        return [r.to_dict() for r in recent]

    def get_successful_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get only successful (non-error) results.

        Args:
            limit: Maximum results to return

        Returns:
            List of successful result dictionaries
        """
        successful = [r for r in self.results if r.error is None]
        return [r.to_dict() for r in successful[-limit:]]

    def get_results_by_project(self, project_name: str) -> List[Dict[str, Any]]:
        """
        Get all results for a specific project.

        Args:
            project_name: Project name to filter

        Returns:
            List of results for that project
        """
        filtered = [r for r in self.results if r.project_name == project_name]
        return [r.to_dict() for r in filtered]

    def get_marketing_posts(self, limit: int = 100) -> List[str]:
        """
        Get generated marketing posts.

        Args:
            limit: Maximum posts to return

        Returns:
            List of marketing post strings
        """
        posts = [
            r.marketing_post
            for r in self.results
            if r.marketing_post and r.error is None
        ]
        return posts[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get result statistics.

        Returns:
            Dictionary with statistics
        """
        stats = self.metadata.copy()

        # Calculate success rate
        total = stats["total_processed"]
        successful = stats["total_successful"]
        stats["success_rate"] = (
            (successful / total * 100) if total > 0 else 0
        )

        # Get most recent
        if self.results:
            stats["most_recent"] = self.results[-1].to_dict()

        return stats

    def clear_results(self) -> int:
        """
        Clear all results.

        Returns:
            Number of results cleared
        """
        count = len(self.results)
        self.results = []
        logger.info(f"Cleared {count} results")
        return count

    async def persist_to_storage(self) -> bool:
        """
        Persist results to external storage (Redis/DB).

        This is a placeholder for future integration.

        Returns:
            True if persistence successful
        """
        # TODO: Implement Redis/Database storage
        logger.info(f"Persisting {len(self.results)} results to storage")
        return True

    async def load_from_storage(self) -> bool:
        """
        Load results from external storage (Redis/DB).

        This is a placeholder for future integration.

        Returns:
            True if load successful
        """
        # TODO: Implement Redis/Database loading
        logger.info("Loading results from storage")
        return True
