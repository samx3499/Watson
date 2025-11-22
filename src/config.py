"""Configuration management for Watson project."""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class for Watson project."""

    # API Keys - OpenRouter is OpenAI-compatible
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    # OpenRouter base URL (OpenAI-compatible API)
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    # WandB for experiment tracking
    WANDB_API_KEY: Optional[str] = os.getenv("WANDB_API_KEY")
    WANDB_PROJECT: str = os.getenv("WANDB_PROJECT", "watson")
    WANDB_ENTITY: Optional[str] = os.getenv("WANDB_ENTITY")

    # Model configurations (OpenRouter model names)
    # Default to fastest models for speed and cost efficiency
    # Try: google/gemini-1.5-flash, openai/gpt-4o-mini, anthropic/claude-3-haiku
    AGENT_MODEL: str = os.getenv("AGENT_MODEL", "openai/gpt-4o-mini")  # Fast, reliable tool calling
    ENVIRONMENT_MODEL: str = os.getenv("ENVIRONMENT_MODEL", "openai/gpt-4o-mini")  # Fast
    REWARD_MODEL: str = os.getenv("REWARD_MODEL", "openai/gpt-4o-mini")  # Fast

    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is present."""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required")
