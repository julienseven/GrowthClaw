"""
Environment configuration management for $GROWTH backend.
Uses Pydantic Settings v2 for environment variable validation and type checking.

All configuration is loaded from environment variables and .env files.
Supports both local development and production deployments.
"""
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Supports:
    - .env file loading (local development)
    - Environment variable overrides (production)
    - Type validation via Pydantic v2
    - Default values for optional settings
    """

    # ============================================================================
    # Solana Blockchain Configuration
    # ============================================================================
    
    solana_rpc_url: str = "https://api.mainnet-beta.solana.com"
    """Solana RPC endpoint for blockchain interaction."""
    
    solana_network: str = "mainnet-beta"
    """Network: mainnet-beta, devnet, testnet, localnet."""
    
    solana_commitment_level: str = "confirmed"
    """Commitment level: processed, confirmed, finalized."""

    # ============================================================================
    # OpenAI Configuration
    # ============================================================================
    
    openai_api_key: str = ""
    """OpenAI API key for GPT-4o-mini access (required for AI features)."""
    
    openai_model: str = "gpt-4o-mini"
    """OpenAI model to use (optimized for cost/speed)."""
    
    openai_max_tokens: int = 200
    """Maximum tokens per OpenAI request (posts should be short)."""
    
    openai_temperature: float = 0.7
    """Temperature for OpenAI responses (0.0-2.0, higher = more creative)."""

    # ============================================================================
    # Target Token & Agent Configuration
    # ============================================================================
    
    target_token_address: Optional[str] = None
    """Target wallet address to monitor for transactions."""
    
    target_token_decimals: int = 6
    """Decimal places for token (usually 6)."""
    
    target_dex_program_id: str = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1xf"
    """Raydium DEX program ID."""

    agent_polling_interval: int = 30
    """Seconds between transaction polling cycles."""
    
    agent_min_sol_transfer: float = 0.05
    """Minimum SOL transfer to process (in SOL)."""
    
    agent_max_cached_results: int = 10000
    """Maximum results to keep in memory cache."""

    # ============================================================================
    # Redis Configuration
    # ============================================================================
    
    redis_url: str = "redis://localhost:6379"
    """Redis connection URL for caching and task queues."""
    
    redis_db: int = 0
    """Redis database number (0-15)."""

    # ============================================================================
    # API Configuration
    # ============================================================================
    
    api_host: str = "0.0.0.0"
    """Host to bind API server to."""
    
    api_port: int = 8000
    """Port to run API server on."""
    
    api_log_level: str = "info"
    """Logging level: debug, info, warning, error, critical."""
    
    api_workers: int = 1
    """Number of worker processes (for production deployment)."""

    # ============================================================================
    # Environment Configuration
    # ============================================================================
    
    environment: str = "development"
    """Deployment environment: development, staging, production."""
    
    debug: bool = True
    """Enable debug mode (logs, extended errors, etc.)."""

    class Config:
        """Pydantic v2 configuration for environment variable loading."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    def has_ai_enabled(self) -> bool:
        """Check if AI features are enabled (API key configured)."""
        return bool(self.openai_api_key)

    def has_agent_configured(self) -> bool:
        """Check if agent monitoring is configured."""
        return bool(self.target_token_address)


# Global settings instance - loaded once on module import
settings = Settings()
