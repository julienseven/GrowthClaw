"""
Services module for business logic and data management.

Provides:
- Result management and storage
- Transaction processing pipelines
- Analytics and reporting
"""

from .result_manager import ResultManager, Result

__all__ = [
    "ResultManager",
    "Result",
]
