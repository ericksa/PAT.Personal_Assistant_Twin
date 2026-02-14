"""
Application Configuration Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Basic app settings
    APP_NAME: str = "PAT Backend API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database settings
    DATABASE_URL: str = "postgresql://user:password@localhost/pat_db"
    
    # PostgreSQL specific settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "pat_db"
    DB_USER: str = "user"
    DB_PASSWORD: str = "password"
    DB_MIN_CONNECTIONS: int = 5
    DB_MAX_CONNECTIONS: int = 20
    DB_COMMAND_TIMEOUT: int = 60
    
    # Redis settings (for future use)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in environment
    )


# Create global settings instance
settings = Settings()