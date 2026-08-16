"""
Pydantic schemas for request/response validation.

Includes schemas for transactions, agents, and market data.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service status")
    environment: str = Field(..., description="Environment name")
    service: str = Field(..., description="Service name")


class MarketData(BaseModel):
    """Market data schema."""

    token_address: str = Field(..., description="SPL token mint address")
    price: float = Field(..., description="Current token price in USD")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    volume_24h: Optional[float] = Field(None, description="24-hour trading volume")
    holders_count: Optional[int] = Field(None, description="Number of token holders")
    liquidity: Optional[float] = Field(None, description="DEX liquidity in USD")


class StrategyRecommendation(BaseModel):
    """AI-generated strategy recommendation schema."""

    strategy_id: str = Field(..., description="Unique strategy identifier")
    title: str = Field(..., description="Strategy title")
    description: str = Field(..., description="Detailed description")
    priority: str = Field(..., description="Priority level: high, medium, low")
    confidence_score: float = Field(..., description="AI confidence score 0-1")
    estimated_impact: Optional[str] = Field(None, description="Expected impact")
    actions: List[str] = Field(..., description="List of recommended actions")


class TokenInfo(BaseModel):
    """Token information schema."""

    mint_address: str = Field(..., description="SPL token mint address")
    name: str = Field(..., description="Token name")
    symbol: str = Field(..., description="Token symbol")
    decimals: int = Field(..., description="Token decimals")
    total_supply: Optional[float] = Field(None, description="Total supply")
    current_holders: Optional[int] = Field(None, description="Current holder count")


class ProjectMetadata(BaseModel):
    """Extracted project metadata from memo."""

    name: str = Field(..., description="Project name", min_length=2, max_length=100)
    description: str = Field(
        ..., description="Project description", min_length=5, max_length=1000
    )


class TransactionResult(BaseModel):
    """Processed transaction result schema."""

    signature: str = Field(..., description="Transaction signature")
    timestamp: str = Field(..., description="Block timestamp (ISO format)")
    payer: Optional[str] = Field(None, description="Transaction payer address")
    lamports_transferred: int = Field(..., description="SOL transferred in lamports")
    project_name: str = Field(..., description="Extracted project name")
    project_description: str = Field(..., description="Extracted project description")
    marketing_post: str = Field(..., description="Generated marketing post")
    post_length: int = Field(..., description="Length of marketing post")
    sentiment: Optional[Dict[str, Any]] = Field(
        None, description="Sentiment analysis results"
    )
    error: Optional[str] = Field(None, description="Error message if processing failed")


class AgentStatus(BaseModel):
    """Transaction agent status schema."""

    is_running: bool = Field(..., description="Whether agent is currently running")
    processed_count: int = Field(..., description="Total transactions processed")
    error_count: int = Field(..., description="Total processing errors")
    wallet_address: str = Field(..., description="Monitored wallet address")
    last_processed_signature: Optional[str] = Field(
        None, description="Last processed transaction signature"
    )


class MemoParseResult(BaseModel):
    """Result of memo parsing operation."""

    raw_text: str = Field(..., description="Raw memo text")
    is_valid: bool = Field(..., description="Whether memo is valid")
    project_name: Optional[str] = Field(None, description="Extracted project name")
    project_description: Optional[str] = Field(
        None, description="Extracted project description"
    )
    error_message: Optional[str] = Field(None, description="Error message if parsing failed")
    encoding_type: str = Field(default="utf-8", description="Encoding used")


class MarketingPostRequest(BaseModel):
    """Request to generate marketing post."""

    project_name: str = Field(..., description="Project name", min_length=2, max_length=100)
    project_description: str = Field(
        ..., description="Project description", min_length=5, max_length=1000
    )
    max_length: int = Field(default=280, ge=50, le=500, description="Max post length")


class MarketingPostResponse(BaseModel):
    """Generated marketing post response."""

    post: str = Field(..., description="Generated marketing post")
    length: int = Field(..., description="Length of post")
    project_name: str = Field(..., description="Project name")


class SentimentAnalysisRequest(BaseModel):
    """Request sentiment analysis."""

    project_name: str = Field(..., description="Project name")
    project_description: str = Field(..., description="Project description")


class SentimentAnalysisResponse(BaseModel):
    """Sentiment analysis response."""

    sentiment: str = Field(..., description="bullish, neutral, or bearish")
    score: int = Field(..., ge=0, le=100, description="Confidence score")
    reasoning: str = Field(..., description="Explanation of sentiment")
    keywords: List[str] = Field(..., description="Key insights")
