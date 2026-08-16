"""
OpenAI AI engine wrapper.
Provides production-ready async abstractions for OpenAI API interactions.
Implements viral marketing post generation and market analysis.
"""
import asyncio
import logging
import re
from typing import Optional, Dict, Any

import httpx
from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError

from config import settings

logger = logging.getLogger(__name__)


class AIEngine:
    """
    OpenAI AI engine wrapper with async support.
    
    Encapsulates all interactions with OpenAI API for:
    - Viral crypto marketing post generation (< 280 chars)
    - Market sentiment analysis
    - Strategic recommendations
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AI engine.

        Args:
            api_key: Optional override for API key. Defaults to settings.
        
        Raises:
            ValueError: If no API key available
        """
        self.api_key = api_key or settings.openai_api_key
        
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature
        
        # Initialize async OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_viral_marketing_post(
        self, project_name: str, project_description: str, max_length: int = 280
    ) -> Optional[str]:
        """
        Generate a viral, high-energy marketing post under character limit.

        This is the core function for the agent infrastructure. It takes project
        metadata extracted from Solana memo instructions and creates engaging
        crypto marketing content.

        Args:
            project_name: Name of the project
            project_description: Description of the project
            max_length: Maximum character length (default 280 for tweet-like)

        Returns:
            Generated marketing post or None if generation fails

        Raises:
            ValueError: If inputs are invalid
            APIError: If OpenAI API call fails
        """
        if not project_name or not project_description:
            logger.error("Project name and description required")
            raise ValueError("Project name and description cannot be empty")

        if max_length < 50:
            raise ValueError("max_length must be at least 50 characters")

        # Sanitize inputs
        project_name = project_name.strip()[:100]
        project_description = project_description.strip()[:500]

        prompt = f"""Generate a viral, high-energy cryptocurrency marketing post for Twitter/X.

Project: {project_name}
Description: {project_description}

Requirements:
- Maximum {max_length} characters (STRICT LIMIT)
- Use crypto/web3 slang and emojis appropriately
- Create FOMO and excitement
- Be authentic but promotional
- Include 1-2 relevant emojis
- No hashtags (unless essential)
- Sound like a crypto native, not a bot
- Make it shareable and engaging

Generate ONLY the post text, no explanations."""

        try:
            logger.info(f"Generating marketing post for: {project_name}")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a crypto marketing expert who writes viral, engaging posts that appeal to crypto natives.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=100,  # Posts should be short
                timeout=10.0,
            )

            if not response.choices or not response.choices[0].message:
                logger.error("No response from OpenAI")
                return None

            post = response.choices[0].message.content.strip()

            # Enforce character limit
            if len(post) > max_length:
                logger.warning(
                    f"Generated post exceeds limit ({len(post)} > {max_length}), trimming..."
                )
                post = post[: max_length - 3] + "..."

            logger.info(f"Generated post ({len(post)} chars): {post[:50]}...")
            return post

        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise
        except APIConnectionError as e:
            logger.error(f"Connection error with OpenAI: {e}")
            raise
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except asyncio.TimeoutError:
            logger.error("Timeout calling OpenAI API")
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating post: {e}")
            raise

    async def analyze_market_sentiment(
        self, project_description: str, market_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze market sentiment for a token/project.

        Args:
            project_description: Description of the project
            market_data: Optional market metrics (price, volume, etc.)

        Returns:
            Analysis dict with sentiment, score, and reasoning
        """
        if not project_description:
            logger.error("Project description required for sentiment analysis")
            return None

        prompt = f"""Analyze the market sentiment for this crypto project.

Project Description: {project_description}

Provide analysis in JSON format with:
- sentiment: "bullish", "neutral", or "bearish"
- score: 0-100 confidence score
- reasoning: brief explanation
- keywords: list of key insights

Respond ONLY with valid JSON."""

        try:
            logger.info("Analyzing market sentiment")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert crypto market analyst. Provide insights in valid JSON format only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=200,
                timeout=10.0,
            )

            if not response.choices or not response.choices[0].message:
                return None

            response_text = response.choices[0].message.content.strip()

            # Parse JSON response
            import json

            try:
                analysis = json.loads(response_text)
                logger.info(f"Sentiment analysis complete: {analysis.get('sentiment')}")
                return analysis
            except json.JSONDecodeError:
                logger.warning("Failed to parse sentiment analysis as JSON")
                return None

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return None

    async def generate_marketing_strategy(
        self, project_name: str, project_description: str
    ) -> Optional[str]:
        """
        Generate autonomous marketing strategy recommendations.

        Args:
            project_name: Name of the project
            project_description: Description of the project

        Returns:
            Strategy recommendations or None if error occurs
        """
        if not project_name or not project_description:
            logger.error("Project name and description required")
            return None

        prompt = f"""Create a brief marketing strategy for this crypto project.

Project: {project_name}
Description: {project_description}

Provide:
1. Target audience
2. Key messages
3. Primary channels
4. First actions

Keep it concise and actionable."""

        try:
            logger.info(f"Generating strategy for: {project_name}")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a crypto marketing strategist. Provide practical, actionable advice.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=300,
                timeout=10.0,
            )

            if not response.choices or not response.choices[0].message:
                return None

            strategy = response.choices[0].message.content.strip()
            logger.info("Strategy generation complete")
            return strategy

        except Exception as e:
            logger.error(f"Error generating strategy: {e}")
            return None

    async def evaluate_growth_opportunities(
        self, project_description: str
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate growth opportunities based on project analysis.

        Args:
            project_description: Description of the project

        Returns:
            Growth opportunities dict or None if error occurs
        """
        if not project_description:
            return None

        prompt = f"""Evaluate growth opportunities for this crypto project.

Project Description: {project_description}

Analyze:
- Market potential (1-10)
- Community building potential (1-10)
- Viral potential (1-10)
- Partnership opportunities
- Key success factors

Respond in JSON format only."""

        try:
            logger.info("Evaluating growth opportunities")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a crypto growth analyst. Provide insights in valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=300,
                timeout=10.0,
            )

            if not response.choices or not response.choices[0].message:
                return None

            response_text = response.choices[0].message.content.strip()

            import json

            try:
                opportunities = json.loads(response_text)
                logger.info("Growth evaluation complete")
                return opportunities
            except json.JSONDecodeError:
                logger.warning("Failed to parse growth opportunities as JSON")
                return None

        except Exception as e:
            logger.error(f"Error evaluating growth opportunities: {e}")
            return None
