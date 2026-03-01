"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/trade_copilot"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MetaAPI
    METAAPI_TOKEN: str = ""
    METAAPI_PROVISIONING_TOKEN: str = ""

    # AI Keys
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # JWT
    JWT_SECRET: str = "change-me-in-production-super-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days

    # CORS
    CORS_ORIGINS: str = '["*"]'

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    # Notifications
    NOTIFICATION_WEBHOOK_URL: str = ""
    SENDGRID_API_KEY: str = ""
    NOTIFICATION_EMAIL_FROM: str = ""
    NOTIFICATION_EMAIL_TO: str = ""
    # MetaAPI behavior
    # When False (default) disconnect will NOT undeploy the MetaAPI terminal
    # to avoid re-provisioning costs when the user reconnects the same account.
    METAAPI_UNDEPLOY_ON_DISCONNECT: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
