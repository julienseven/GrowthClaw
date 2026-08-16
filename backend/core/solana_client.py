"""
Solana RPC client wrapper.
Provides abstractions for interacting with the Solana blockchain.
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import httpx
from solana.rpc.async_api import AsyncClient
from solana.rpc.core import RPCException
from solana.publickey import PublicKey
from solana.transaction import Transaction

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class TransactionSignature:
    """Transaction signature info."""
    signature: str
    slot: int
    block_time: int
    err: Optional[Dict] = None


@dataclass
class TransactionData:
    """Parsed transaction data."""
    signature: str
    block_time: int
    payer: str
    lamports_transferred: int
    memo: Optional[str] = None
    status: str = "confirmed"


class SolanaClient:
    """
    Solana blockchain client wrapper with async support.
    
    Encapsulates connections and interactions with Solana RPC endpoints.
    Uses solana-py library with async HTTP client for high-performance
    transaction polling and data extraction.
    """

    def __init__(self, rpc_url: Optional[str] = None):
        """
        Initialize Solana client.

        Args:
            rpc_url: Optional override for RPC URL. Defaults to settings.
        """
        self.rpc_url = rpc_url or settings.solana_rpc_url
        self.network = settings.solana_network
        self.commitment_level = settings.solana_commitment_level
        self.client: Optional[AsyncClient] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.request_count = 0
        self.last_reset = asyncio.get_event_loop().time() if asyncio.get_event_loop() else 0

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Establish async connections."""
        try:
            self.client = AsyncClient(self.rpc_url, commitment=self.commitment_level)
            self.http_client = httpx.AsyncClient(timeout=30.0)
            logger.info(f"Connected to Solana RPC: {self.rpc_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Solana RPC: {e}")
            raise

    async def disconnect(self):
        """Close async connections."""
        if self.http_client:
            await self.http_client.aclose()
        if self.client:
            await self.client.close()
        logger.info("Disconnected from Solana RPC")

    async def get_signatures_for_address(
        self, address: str, limit: int = 10, before: Optional[str] = None
    ) -> List[TransactionSignature]:
        """
        Get transaction signatures for a wallet address.

        Args:
            address: Solana wallet address
            limit: Maximum number of signatures to return (max 1000)
            before: Get signatures before this one (for pagination)

        Returns:
            List of TransactionSignature objects

        Raises:
            ValueError: If address is invalid
            RPCException: If RPC call fails
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        try:
            # Validate address
            PublicKey(address)
        except Exception as e:
            logger.error(f"Invalid Solana address: {address}")
            raise ValueError(f"Invalid Solana address: {address}") from e

        try:
            # Rate limit: max 40 requests per 10 seconds
            await self._handle_rate_limit()

            # Get signatures from RPC
            response = await self.client.get_signatures_for_address(
                PublicKey(address),
                limit=min(limit, 1000),
                before=PublicKey(before) if before else None,
            )

            if response.get("result") is None:
                logger.warning(f"No signatures found for address: {address}")
                return []

            # Convert response to TransactionSignature objects
            signatures = []
            for tx_info in response["result"]:
                try:
                    sig = TransactionSignature(
                        signature=tx_info["signature"],
                        slot=tx_info["slot"],
                        block_time=tx_info.get("blockTime", 0),
                        err=tx_info.get("err"),
                    )
                    signatures.append(sig)
                except KeyError as e:
                    logger.warning(f"Missing field in transaction info: {e}")
                    continue

            logger.info(f"Retrieved {len(signatures)} signatures for {address}")
            return signatures

        except RPCException as e:
            logger.error(f"RPC error getting signatures: {e}")
            raise
        except asyncio.TimeoutError:
            logger.error("Timeout getting signatures from RPC")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting signatures: {e}")
            raise

    async def get_transaction(self, signature: str) -> Optional[TransactionData]:
        """
        Get full transaction data including instructions.

        Args:
            signature: Transaction signature

        Returns:
            TransactionData object or None if parsing fails

        Raises:
            RPCException: If RPC call fails
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        try:
            await self._handle_rate_limit()

            # Get transaction with full details
            response = await self.client.get_transaction(
                signature,
                encoding="json",
                max_supported_transaction_version=0,
            )

            if response.get("result") is None:
                logger.warning(f"Transaction not found: {signature}")
                return None

            tx_data = response["result"]
            
            # Parse transaction
            try:
                parsed_tx = self._parse_transaction(signature, tx_data)
                return parsed_tx
            except Exception as e:
                logger.warning(f"Failed to parse transaction {signature}: {e}")
                return None

        except RPCException as e:
            logger.error(f"RPC error getting transaction {signature}: {e}")
            raise
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting transaction {signature}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting transaction {signature}: {e}")
            raise

    def _parse_transaction(self, signature: str, tx_data: Dict[str, Any]) -> Optional[TransactionData]:
        """
        Parse transaction data to extract relevant fields.

        Args:
            signature: Transaction signature
            tx_data: Raw transaction data from RPC

        Returns:
            TransactionData object or None if critical data missing
        """
        try:
            transaction = tx_data.get("transaction", {})
            meta = tx_data.get("meta", {})

            # Extract basic info
            block_time = tx_data.get("blockTime", 0)
            
            # Get payer (first signer)
            message = transaction.get("message", {})
            account_keys = message.get("accountKeys", [])
            payer = account_keys[0] if account_keys else "unknown"

            # Calculate SOL transferred from fee and balance changes
            lamports_transferred = 0
            pre_balances = meta.get("preBalances", [])
            post_balances = meta.get("postBalances", [])
            
            if pre_balances and post_balances:
                for i, (pre, post) in enumerate(zip(pre_balances, post_balances)):
                    if post < pre:  # Balance decreased
                        lamports_transferred = pre - post
                        break

            # Extract memo from instructions
            memo = self._extract_memo_from_instructions(message.get("instructions", []))

            # Check transaction status
            status = "success" if meta.get("err") is None else "failed"

            return TransactionData(
                signature=signature,
                block_time=block_time,
                payer=payer,
                lamports_transferred=lamports_transferred,
                memo=memo,
                status=status,
            )

        except Exception as e:
            logger.error(f"Error parsing transaction {signature}: {e}")
            return None

    def _extract_memo_from_instructions(self, instructions: List[Dict]) -> Optional[str]:
        """
        Extract memo from Solana Memo Program instruction.

        The Memo Program instruction has a specific structure where
        the memo text is in the data field.

        Args:
            instructions: List of transaction instructions

        Returns:
            Memo text if found, None otherwise
        """
        MEMO_PROGRAM_ID = "MemoSq4gDiRynqzStXoESKyXKpy4xjqJMmLeQMwr08"  # Standard Memo Program ID

        for instruction in instructions:
            try:
                # Check if this is a Memo Program instruction
                program_id = instruction.get("programId", "")
                
                if program_id == MEMO_PROGRAM_ID:
                    # Memo is encoded in the data field (base64 or string)
                    data = instruction.get("data", "")
                    
                    if isinstance(data, str):
                        # Try to decode as string
                        try:
                            # If it's base64, decode it
                            import base64
                            decoded = base64.b64decode(data).decode("utf-8", errors="ignore")
                            return decoded.strip() if decoded else None
                        except Exception:
                            # If not base64, try as-is
                            return data.strip() if data else None
                    
                    return None
                    
            except Exception as e:
                logger.debug(f"Error parsing instruction: {e}")
                continue

        return None

    async def get_balance(self, address: str) -> float:
        """
        Get SOL balance for an address in lamports.

        Args:
            address: Solana address (base58 encoded)

        Returns:
            Balance in lamports

        Raises:
            ValueError: If address is invalid
            RPCException: If RPC call fails
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        try:
            PublicKey(address)
        except Exception as e:
            raise ValueError(f"Invalid Solana address: {address}") from e

        try:
            await self._handle_rate_limit()

            response = await self.client.get_balance(PublicKey(address))
            
            if response.get("result") is None:
                logger.warning(f"Could not get balance for {address}")
                return 0.0

            return float(response["result"]["value"])

        except Exception as e:
            logger.error(f"Error getting balance for {address}: {e}")
            raise

    async def get_token_balance(
        self, token_address: str, owner_address: str
    ) -> Optional[float]:
        """
        Get token balance for an address.

        Args:
            token_address: SPL token mint address
            owner_address: Token account owner address

        Returns:
            Token balance or None if error occurs
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        try:
            await self._handle_rate_limit()

            # This would require finding the token account for the owner
            # Implementation would depend on token program interactions
            logger.info(f"Getting token balance for {owner_address}")
            return None

        except Exception as e:
            logger.error(f"Error getting token balance: {e}")
            return None

    async def get_account_info(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get account information from Solana.

        Args:
            address: Solana address

        Returns:
            Account info dict or None if error occurs
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        try:
            PublicKey(address)
        except Exception as e:
            raise ValueError(f"Invalid Solana address: {address}") from e

        try:
            await self._handle_rate_limit()

            response = await self.client.get_account_info(PublicKey(address))
            
            if response.get("result") is None:
                logger.warning(f"Account not found: {address}")
                return None

            return response["result"]["value"]

        except Exception as e:
            logger.error(f"Error getting account info for {address}: {e}")
            raise

    async def _handle_rate_limit(self):
        """
        Handle rate limiting for RPC requests.
        
        Solana RPC has rate limits. This implements a simple token-bucket approach.
        """
        # Approximately 40 requests per 10 seconds for public RPC
        MAX_REQUESTS = 40
        WINDOW_SECONDS = 10

        current_time = asyncio.get_event_loop().time()
        
        # Reset counter if window has passed
        if current_time - self.last_reset > WINDOW_SECONDS:
            self.request_count = 0
            self.last_reset = current_time

        # Check if we're at the limit
        if self.request_count >= MAX_REQUESTS:
            sleep_time = WINDOW_SECONDS - (current_time - self.last_reset)
            if sleep_time > 0:
                logger.warning(f"Rate limit approaching, sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                self.request_count = 0
                self.last_reset = asyncio.get_event_loop().time()

        self.request_count += 1
