"""
Environment configuration using Pydantic Settings.

All environment variables are loaded and validated here.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API Configuration
    CORS_ORIGINS: str = "http://localhost:3000"
    ALLOW_ALL_ORIGINS: bool = False

    # Database (Supabase)
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    DATABASE_URL: str | None = None  # Direct PostgreSQL connection string (optional)

    # AI API Keys
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    CRON_SECRET: str | None = None
    WEBHOOK_SECRET: str | None = None

    # Monitoring
    SENTRY_DSN: str | None = None

    # Frontend base URL (for auth email redirects)
    FRONTEND_URL: str | None = None

    # Wearables
    WEARABLE_CRED_SECRET: str | None = None  # Symmetric key for encrypting wearable credentials (Fernet base64 key)
    GARMIN_ENABLED: bool = False

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS comma-separated string into list."""
        if self.ALLOW_ALL_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"


# Global settings instance
settings = Settings()
