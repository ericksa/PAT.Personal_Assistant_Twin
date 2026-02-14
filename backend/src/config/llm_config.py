# src/config/llm_config.py - LLM Configuration for Llama 3.2
from pydantic_settings import BaseSettings
from typing import Optional


class LLMConfig(BaseSettings):
    """Configuration for LLM service supporting multiple providers"""

    # Model Configuration
    MODEL: str = "glm-4.6v-flash"
    PROVIDER: str = "lm_studio"  # Supports: ollama, lm_studio, openai

    # LM Studio Configuration (GLM-4.6v-flash)
    BASE_URL: str = "http://localhost:1234"
    API_URL: str = "http://localhost:1234/v1/chat/completions"
    CHAT_API_URL: str = "http://localhost:1234/v1/chat/completions"

    # Ollama Configuration (fallback)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_API_URL: str = "http://localhost:11434/api/generate"
    OLLAMA_CHAT_API_URL: str = "http://localhost:11434/api/chat"

    # Generation Parameters
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    MAX_TOKENS: int = 2048
    NUM_PREDICT: int = -1  # -1 for unlimited (model's default)

    # Context
    CONTEXT_WINDOW: int = 128000  # 128K tokens for most models
    NUM_CTX: int = 8192  # Context size for generation

    # Features
    ENABLE_TOOL_CALLING: bool = True
    ENABLE_STREAMING: bool = True
    ENABLE_STRUCTURED_OUTPUT: bool = True

    # Model-specific settings
    MAX_TOKENS_glm46v: int = 8192  # GLM-4.6v-flash context
    MAX_TOKENS_llama32_3b: int = 8192  # Llama 3.2 3B context

    # Authentication for OpenAI-compatible APIs
    API_KEY: Optional[str] = None

    # Rate limiting
    REQUESTS_PER_MINUTE: int = 60
    REQUESTS_PER_HOUR: int = 1000

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


settings = LLMConfig()
