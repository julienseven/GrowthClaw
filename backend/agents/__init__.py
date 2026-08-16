"""
Agents module for $GROWTH backend.

This module contains autonomous agents that:
- Monitor Solana transactions in real-time
- Process and analyze transaction data
- Generate marketing content
- Manage autonomous workflows

Main agents:
- TransactionAgent: Monitors wallet for incoming transactions
- MarketMonitor: Analyzes market conditions
- GrowthAgent: Generates growth strategies
"""

from .transaction_agent import TransactionAgent, ProjectMetadata, ProcessedTransaction

__all__ = [
    "TransactionAgent",
    "ProjectMetadata",
    "ProcessedTransaction",
]
