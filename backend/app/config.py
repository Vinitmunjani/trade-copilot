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
    OPENAI_MODEL: str = "gpt-5.2"
    ANTHROPIC_API_KEY: str = ""
    ENABLE_M15_CONTEXT: bool = False

    # JWT
    JWT_SECRET: str = "change-me-in-production-super-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days

    # CORS
    CORS_ORIGINS: str = '["*"]'

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    # Admin API access
    ADMIN_API_KEY: str = ""
    ADMIN_EMAILS: str = ""
    # Notifications
    NOTIFICATION_WEBHOOK_URL: str = ""
    SENDGRID_API_KEY: str = ""
    NOTIFICATION_EMAIL_FROM: str = ""
    NOTIFICATION_EMAIL_TO: str = ""
    # MetaAPI behavior
    # When False (default) disconnect will NOT undeploy the MetaAPI terminal
    # to avoid re-provisioning costs when the user reconnects the same account.
    METAAPI_UNDEPLOY_ON_DISCONNECT: bool = False

    # Beta auto-adjust behavior
    AUTO_ADJUST_BETA_ENABLED: bool = True
    AUTO_ADJUST_DEFAULT_THRESHOLD: int = 3
    AUTO_ADJUST_INTERVAL_SECONDS: int = 30
    AUTO_ADJUST_COOLDOWN_SECONDS: int = 120
    AUTO_ADJUST_DEFAULT_MODE: str = "hybrid"  # close | modify | hybrid
    AUTO_ADJUST_LOW_LATENCY_ENABLED: bool = True
    AUTO_ADJUST_FAST_CONTEXT_TIMEOUT_SECONDS: int = 2
    AUTO_ADJUST_MAX_ACTIONS_PER_TRADE: int = 1

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
