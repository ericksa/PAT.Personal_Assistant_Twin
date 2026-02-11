# src/config/llm_config.py - LLM Configuration for Llama 3.2
from pydantic_settings import BaseSettings
from typing import Optional


class LLMConfig(BaseSettings):
    """Configuration for LLM service using Llama 3.2 3B via Ollama"""

    # Model Configuration
    MODEL: str = "llama3.2:3b"
    PROVIDER: str = "ollama"

    # Ollama Connection
    BASE_URL: str = "http://localhost:11434"
    API_URL: str = "http://localhost:11434/api/generate"
    CHAT_API_URL: str = "http://localhost:11434/api/chat"

    # Generation Parameters
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    MAX_TOKENS: int = 2048
    NUM_PREDICT: int = -1  # -1 for unlimited (model's default)

    # Context
    CONTEXT_WINDOW: int = 128000  # 128K tokens for llama 3.2
    NUM_CTX: int = 8192  # Context size for generation

    # Features
    ENABLE_TOOL_CALLING: bool = True
    ENABLE_STREAMING: bool = True
    ENABLE_STRUCTURED_OUTPUT: bool = True

    # Model-specific settings for llama3.2:3b
    NUM_CTX_llama32_3b: int = 8192  # Smaller model can handle more context

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


settings = LLMConfig()
