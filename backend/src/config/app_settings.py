from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APPLICATION_NAME: str = "PAT Job Search Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database Config
    DATABASE_URL: Optional[str] = None

    # Redis Config
    REDIS_URL: Optional[str] = None

    # Job Search Config
    JOB_SEARCH_ENABLED: bool = True
    JOB_SEARCH_SCHEDULE: str = "0 8 * * *"

    # LinkedIn Config
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None

    # SMTP Config
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    PAT_NOTIFICATION_EMAIL: Optional[str] = None

    # MinIO Config
    MINIO_ENDPOINT: Optional[str] = None
    MINIO_ACCESS_KEY: Optional[str] = None
    MINIO_SECRET_KEY: Optional[str] = None
    MINIO_BUCKET: str = "pat-documents"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
