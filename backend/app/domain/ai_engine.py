"""
AI engine — OpenAI helper that turns a project description into a viral,
high-energy crypto marketing post of < 280 characters.

Uses the async OpenAI client (``AsyncOpenAI``) so the growth worker can
overlap LLM calls with Solana polling instead of blocking the event loop.
"""

from __future__ import annotations

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion


class AIEngineError(RuntimeError):
    """Raised when the marketing post cannot be generated."""


class OpenAIEngine:
    """A thin, typed wrapper around ``AsyncOpenAI`` for post generation."""

    SYSTEM_PROMPT = (
        "You are a viral crypto marketing copywriter for the Solana ecosystem. "
        "You write short, high-energy, community-driven posts that spark hype, "
        "FOMO, and engagement without making false financial promises."
    )

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 256,
        timeout_seconds: float = 60.0,
    ) -> None:
        if not api_key:
            raise ValueError("OpenAI API key is required to build the AI engine")
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._client = AsyncOpenAI(
            api_key=api_key,
            timeout=timeout_seconds,
            max_retries=2,
        )

    async def close(self) -> None:
        await self._client.close()

    async def generate_marketing_post(
        self, project_name: str, description: str
    ) -> str:
        """Generate a viral marketing post (< 280 chars) from a description.

        Guarantees the result fits within 280 characters even if the model
        returns something longer, by truncating on a word boundary.
        """
        if not project_name or not description:
            raise AIEngineError("project_name and description are both required")

        user_prompt = self._build_prompt(project_name, description)

        try:
            response: ChatCompletion = await self._client.chat.completions.create(
                model=self._model,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:  # network, auth, rate-limit, etc.
            raise AIEngineError(f"OpenAI request failed: {exc}") from exc

        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise AIEngineError("OpenAI returned an empty completion")

        text = content.strip()
        return self._enforce_max_length(text, max_chars=280)

    @staticmethod
    def _build_prompt(project_name: str, description: str) -> str:
        return (
            f"Write ONE viral marketing post for this Solana project. It MUST be "
            f"under 280 characters (it will be posted to a microblogging feed).\n\n"
            f"Project name: {project_name}\n"
            f"Project description: {description}\n\n"
            f"Rules:\n"
            f"- High energy, punchy, and hype-driven.\n"
            f"- Crypto-native tone (mention Solana where natural).\n"
            f"- No financial advice, no guaranteed-returns claims.\n"
            f"- No hashtags spam, one or two at most.\n"
            f"- Return ONLY the post text, no quotes or commentary."
        )

    @staticmethod
    def _enforce_max_length(text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        truncated = text[: max_chars - 1]
        # Prefer cutting at the last word boundary; avoid orphan whitespace.
        cut = truncated.rfind(" ")
        if cut > 0:
            truncated = truncated[:cut]
        return truncated.strip()
