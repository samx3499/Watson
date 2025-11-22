"""Configuration management for Watson project."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class for Watson project."""
    
    # API Keys - OpenRouter is OpenAI-compatible
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    # OpenPipe API key is optional (only needed for cloud logging/fine-tuning)
    OPENPIPE_API_KEY: Optional[str] = os.getenv("OPENPIPE_API_KEY")
    OPENPIPE_BASE_URL: str = os.getenv(
        "OPENPIPE_BASE_URL", 
        "https://app.openpipe.ai/api/v1"
    )
    
    # OpenRouter base URL (OpenAI-compatible API)
    OPENROUTER_BASE_URL: str = os.getenv(
        "OPENROUTER_BASE_URL",
        "https://openrouter.ai/api/v1"
    )
    
    # WandB for experiment tracking
    WANDB_API_KEY: Optional[str] = os.getenv("WANDB_API_KEY")
    WANDB_PROJECT: str = os.getenv("WANDB_PROJECT", "watson")
    WANDB_ENTITY: Optional[str] = os.getenv("WANDB_ENTITY")
    
    # Model configurations (OpenRouter model names)
    AGENT_MODEL: str = os.getenv("AGENT_MODEL", "openai/gpt-4")
    ENVIRONMENT_MODEL: str = os.getenv("ENVIRONMENT_MODEL", "openai/gpt-4")
    REWARD_MODEL: str = os.getenv("REWARD_MODEL", "openai/gpt-4")
    
    # OpenPipe tags for tracking different components
    AGENT_TAG: str = "watson-agent"
    ENVIRONMENT_TAG: str = "watson-environment"
    REWARD_TAG: str = "watson-reward"
    
    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is present."""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required")
        # OpenPipe API key is optional - only needed for cloud logging

