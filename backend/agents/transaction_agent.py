"""
Transaction Agent - Main orchestrator for Solana transaction monitoring.

This agent:
1. Polls a wallet for new incoming transactions
2. Validates SOL transfers (minimum 0.05 SOL)
3. Parses Memo Program instructions (Format: "ProjectName | ProjectDescription")
4. Generates viral marketing posts via OpenAI
5. Stores results for downstream processing

Production-ready async implementation with comprehensive error handling.
"""
import asyncio
import logging
import base64
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any

from solana.rpc.core import RPCException

from config import settings
from core.solana_client import SolanaClient, TransactionData
from core.ai_engine import AIEngine
from utils.validators import is_valid_solana_address

logger = logging.getLogger(__name__)


# Constants
MIN_SOL_TRANSFER = 0.05  # Minimum SOL to trigger processing
LAMPORTS_PER_SOL = 1_000_000_000
MEMO_PROGRAM_ID = "MemoSq4gDiRynqzStXoESKyXKpy4xjqJMmLeQMwr08"
MEMO_DELIMITER = "|"
MAX_MEMO_LENGTH = 500


@dataclass
class ProjectMetadata:
    """Extracted project metadata from memo."""
    name: str
    description: str
    raw_memo: str

    @staticmethod
    def from_memo(memo: str) -> Optional["ProjectMetadata"]:
        """
        Parse memo in format: "ProjectName | ProjectDescription"

        Args:
            memo: Raw memo text from transaction

        Returns:
            ProjectMetadata object or None if parse fails
        """
        if not memo or not isinstance(memo, str):
            logger.warning(f"Invalid memo format: {memo}")
            return None

        memo = memo.strip()

        if len(memo) > MAX_MEMO_LENGTH:
            logger.warning(f"Memo exceeds max length: {len(memo)} > {MAX_MEMO_LENGTH}")
            return None

        if MEMO_DELIMITER not in memo:
            logger.warning(f"Memo missing delimiter '{MEMO_DELIMITER}': {memo[:50]}")
            return None

        try:
            parts = memo.split(MEMO_DELIMITER, 1)  # Split on first delimiter only
            project_name = parts[0].strip()
            project_description = parts[1].strip()

            # Validate extracted data
            if not project_name or not project_description:
                logger.warning("Memo parsing resulted in empty fields")
                return None

            if len(project_name) > 100:
                logger.warning(f"Project name too long: {len(project_name)}")
                return None

            if len(project_description) > 1000:
                logger.warning(f"Description too long: {len(project_description)}")
                return None

            return ProjectMetadata(
                name=project_name, description=project_description, raw_memo=memo
            )

        except Exception as e:
            logger.error(f"Error parsing memo: {e}")
            return None


@dataclass
class ProcessedTransaction:
    """Transaction after processing through agent pipeline."""
    signature: str
    timestamp: str
    payer: str
    lamports_transferred: int
    project_name: str
    project_description: str
    marketing_post: str
    post_length: int
    sentiment: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return asdict(self)


class TransactionAgent:
    """
    Main agent for monitoring and processing Solana transactions.

    This agent continuously:
    1. Polls the target wallet for new signatures
    2. Fetches and validates transaction data
    3. Extracts project metadata from memo
    4. Generates marketing content via AI
    5. Stores results

    Production characteristics:
    - Async/await for non-blocking I/O
    - Comprehensive error handling
    - Rate limit aware
    - Resumable state (tracks last processed signature)
    - Configurable polling intervals
    """

    def __init__(
        self,
        wallet_address: str,
        solana_client: Optional[SolanaClient] = None,
        ai_engine: Optional[AIEngine] = None,
        polling_interval: int = 30,
    ):
        """
        Initialize transaction agent.

        Args:
            wallet_address: Target wallet to monitor
            solana_client: Optional Solana client instance
            ai_engine: Optional AI engine instance
            polling_interval: Seconds between polling cycles

        Raises:
            ValueError: If wallet address is invalid
        """
        if not is_valid_solana_address(wallet_address):
            raise ValueError(f"Invalid Solana address: {wallet_address}")

        self.wallet_address = wallet_address
        self.solana_client = solana_client or SolanaClient()
        self.ai_engine = ai_engine
        self.polling_interval = polling_interval
        self.is_running = False
        self.last_processed_signature: Optional[str] = None
        self.processed_count = 0
        self.error_count = 0
        self.results: List[ProcessedTransaction] = []

        logger.info(
            f"Initialized TransactionAgent for wallet: {wallet_address[:8]}..."
        )

    async def start(self):
        """Start the agent polling loop."""
        logger.info("Starting Transaction Agent")
        self.is_running = True

        try:
            await self.solana_client.connect()
            logger.info("Connected to Solana RPC")

            while self.is_running:
                try:
                    await self._poll_and_process()
                except asyncio.CancelledError:
                    logger.info("Agent polling cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in polling loop: {e}")
                    self.error_count += 1
                    await asyncio.sleep(self.polling_interval)

        except Exception as e:
            logger.error(f"Fatal error in agent: {e}")
            raise
        finally:
            await self.stop()

    async def stop(self):
        """Stop the agent."""
        logger.info("Stopping Transaction Agent")
        self.is_running = False
        await self.solana_client.disconnect()
        logger.info(f"Agent stats - Processed: {self.processed_count}, Errors: {self.error_count}")

    async def _poll_and_process(self):
        """
        Main polling cycle:
        1. Get new signatures
        2. Process each transaction
        3. Wait for next cycle
        """
        try:
            logger.debug(f"Polling wallet: {self.wallet_address[:8]}...")

            # Get recent signatures (limit to 10 per poll for efficiency)
            signatures = await self.solana_client.get_signatures_for_address(
                self.wallet_address, limit=10
            )

            if not signatures:
                logger.debug("No signatures found in this cycle")
                await asyncio.sleep(self.polling_interval)
                return

            logger.info(f"Found {len(signatures)} signatures")

            # Process signatures in reverse chronological order (oldest first)
            for sig_info in reversed(signatures):
                # Skip if already processed
                if self.last_processed_signature == sig_info.signature:
                    break

                # Skip failed transactions
                if sig_info.err is not None:
                    logger.debug(f"Skipping failed transaction: {sig_info.signature}")
                    continue

                # Process this transaction
                await self._process_transaction(sig_info.signature)

            # Update last processed
            if signatures:
                self.last_processed_signature = signatures[0].signature

        except Exception as e:
            logger.error(f"Error in polling cycle: {e}")
            self.error_count += 1

        finally:
            await asyncio.sleep(self.polling_interval)

    async def _process_transaction(self, signature: str) -> Optional[ProcessedTransaction]:
        """
        Process a single transaction:
        1. Fetch full transaction data
        2. Validate SOL transfer amount
        3. Extract and parse memo
        4. Generate marketing post
        5. Store result

        Args:
            signature: Transaction signature to process

        Returns:
            ProcessedTransaction object or None if processing fails
        """
        logger.info(f"Processing transaction: {signature[:16]}...")

        try:
            # Fetch transaction data
            tx_data = await self.solana_client.get_transaction(signature)

            if not tx_data:
                logger.warning(f"Could not fetch transaction: {signature}")
                return None

            # Validate SOL transfer amount
            min_lamports = int(MIN_SOL_TRANSFER * LAMPORTS_PER_SOL)
            if tx_data.lamports_transferred < min_lamports:
                logger.debug(
                    f"Transaction transfer ({tx_data.lamports_transferred} lamports) "
                    f"below minimum ({min_lamports})"
                )
                return None

            logger.info(
                f"Valid SOL transfer: {tx_data.lamports_transferred / LAMPORTS_PER_SOL} SOL"
            )

            # Extract memo
            if not tx_data.memo:
                logger.debug(f"No memo found in transaction: {signature}")
                return None

            logger.info(f"Memo found: {tx_data.memo[:50]}...")

            # Parse project metadata from memo
            project_metadata = ProjectMetadata.from_memo(tx_data.memo)

            if not project_metadata:
                logger.warning(f"Failed to parse project metadata from memo")
                result = ProcessedTransaction(
                    signature=signature,
                    timestamp=datetime.fromtimestamp(tx_data.block_time).isoformat(),
                    payer=tx_data.payer,
                    lamports_transferred=tx_data.lamports_transferred,
                    project_name="",
                    project_description="",
                    marketing_post="",
                    post_length=0,
                    error="Failed to parse memo format",
                )
                self.results.append(result)
                return result

            logger.info(
                f"Extracted project: {project_metadata.name} - {project_metadata.description[:30]}..."
            )

            # Generate marketing post
            marketing_post = ""
            if self.ai_engine:
                try:
                    marketing_post = await self.ai_engine.generate_viral_marketing_post(
                        project_name=project_metadata.name,
                        project_description=project_metadata.description,
                        max_length=280,
                    )
                except Exception as e:
                    logger.error(f"Error generating marketing post: {e}")
                    marketing_post = ""

            if marketing_post:
                logger.info(f"Generated post: {marketing_post[:50]}...")
            else:
                logger.warning("Failed to generate marketing post")

            # Get sentiment analysis
            sentiment = None
            if self.ai_engine:
                try:
                    sentiment = await self.ai_engine.analyze_market_sentiment(
                        project_metadata.description
                    )
                except Exception as e:
                    logger.debug(f"Error analyzing sentiment: {e}")

            # Create result object
            result = ProcessedTransaction(
                signature=signature,
                timestamp=datetime.fromtimestamp(tx_data.block_time).isoformat(),
                payer=tx_data.payer,
                lamports_transferred=tx_data.lamports_transferred,
                project_name=project_metadata.name,
                project_description=project_metadata.description,
                marketing_post=marketing_post,
                post_length=len(marketing_post),
                sentiment=sentiment,
            )

            self.results.append(result)
            self.processed_count += 1

            logger.info(
                f"✓ Transaction processed successfully: {project_metadata.name}"
            )

            return result

        except Exception as e:
            logger.error(f"Error processing transaction {signature}: {e}")
            self.error_count += 1
            return None

    async def get_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get processed transaction results.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of processed transaction dictionaries
        """
        return [result.to_dict() for result in self.results[-limit:]]

    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "wallet": self.wallet_address,
            "is_running": self.is_running,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "results_cached": len(self.results),
            "last_processed_signature": self.last_processed_signature,
        }
