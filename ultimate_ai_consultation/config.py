"""
Configuration management for Ultimate AI Consultation system.

Loads environment variables and provides typed config objects.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
try:
    # Pydantic v2 recommended config
    from pydantic_settings import SettingsConfigDict
except Exception:  # pragma: no cover
    SettingsConfigDict = None  # type: ignore


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Anthropic API
    ANTHROPIC_API_KEY: str = Field(..., description="Anthropic API key")
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-20241022")

    # Supabase
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_KEY: str = Field(..., description="Supabase service role key")
    SUPABASE_JWT_SECRET: Optional[str] = Field(default=None, description="JWT secret for token validation (optional, uses JWT_SECRET if not set)")
    JWT_SECRET: Optional[str] = Field(default=None, description="Main JWT secret (fallback for SUPABASE_JWT_SECRET)")

    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")

    # Solver Configuration
    SOLVER_TIMEOUT_SECONDS: int = Field(default=30, ge=1, le=300)
    SOLVER_MAX_THREADS: int = Field(default=4, ge=1, le=16)
    MAX_TRADE_OFFS_TO_GENERATE: int = Field(default=3, ge=2, le=5)

    # Nutrition Calculation
    TDEE_CONFIDENCE_INTERVAL: float = Field(default=0.15, ge=0.05, le=0.30)
    MACRO_FLEXIBILITY_PERCENT: float = Field(default=5.0, ge=0.0, le=10.0)
    MIN_PROTEIN_G_PER_KG: float = Field(default=1.6, ge=1.2, le=2.0)
    MAX_PROTEIN_G_PER_KG: float = Field(default=2.4, ge=2.0, le=3.0)
    MIN_FAT_G_PER_KG: float = Field(default=0.6, ge=0.4, le=1.0)
    MIN_CALORIES_FEMALE: int = Field(default=1200, ge=1000, le=1500)
    MIN_CALORIES_MALE: int = Field(default=1500, ge=1200, le=2000)

    # Training Progression
    MAX_VOLUME_INCREASE_PERCENT: float = Field(default=20.0, ge=5.0, le=30.0)
    DELOAD_FREQUENCY_WEEKS: int = Field(default=5, ge=3, le=8)
    MIN_DELOAD_VOLUME_REDUCTION: float = Field(default=0.40, ge=0.30, le=0.50)
    MAX_DELOAD_VOLUME_REDUCTION: float = Field(default=0.60, ge=0.50, le=0.70)

    # Adaptive Control
    REASSESSMENT_FREQUENCY_DAYS: int = Field(default=14, ge=7, le=28)
    PID_PROPORTIONAL_GAIN: float = Field(default=200.0, ge=50.0, le=500.0)
    PID_MAX_ADJUSTMENT_KCAL: float = Field(default=200.0, ge=50.0, le=500.0)
    MIN_ADHERENCE_FOR_PROGRESS: float = Field(default=0.70, ge=0.50, le=0.90)
    LOW_HRV_THRESHOLD_PERCENT: float = Field(default=-10.0, ge=-20.0, le=-5.0)

    # Cost Controls
    MAX_COST_PER_GENERATION: float = Field(default=0.50, ge=0.10, le=2.00)
    DAILY_COST_LIMIT_PER_USER: float = Field(default=0.20, ge=0.05, le=1.00)
    ENABLE_VISION_API: bool = Field(default=False)
    MAX_VISION_CALLS_PER_WEEK: int = Field(default=5, ge=1, le=20)

    # Feature Flags
    ENABLE_BUDGET_OPTIMIZER: bool = Field(default=True)
    ENABLE_WEARABLE_SYNC: bool = Field(default=False)
    ENABLE_SENTIMENT_ANALYSIS: bool = Field(default=True)
    ENABLE_CONFIDENCE_TRACKING: bool = Field(default=True)

    # LLM Personalization (cost-controlled)
    ENABLE_LLM_PERSONALIZATION: bool = Field(default=False)
    LLM_PROVIDER: str = Field(default="groq")
    LLM_MAX_TOKENS_PER_CALL: int = Field(default=128, ge=16, le=2048)
    LLM_CACHE_ENABLED: bool = Field(default=True)
    GROQ_MODEL: str = Field(default="llama-3.1-8b-instant")
    GROQ_API_KEY: str | None = Field(default=None, description="Groq API key (optional)")

    # Integration
    BACKEND_BASE_URL: str = Field(default="http://localhost:8000")
    BACKEND_API_PREFIX: str = Field(default="/api/v1")
    FRONTEND_BASE_URL: str = Field(default="http://localhost:3000")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_ENABLED: bool = Field(default=False)

    # Monitoring
    SENTRY_DSN: Optional[str] = Field(default=None)
    ENABLE_METRICS: bool = Field(default=True)

    # Safety & Validation
    ENABLE_SAFETY_GATE: bool = Field(default=True)
    ENABLE_DOMAIN_RULES: bool = Field(default=True)
    ENABLE_ADHERENCE_RISK_SCORING: bool = Field(default=True)

    # Database Pool
    DB_POOL_SIZE: int = Field(default=10, ge=1, le=50)
    DB_MAX_OVERFLOW: int = Field(default=20, ge=0, le=100)
    DB_POOL_TIMEOUT: int = Field(default=30, ge=5, le=120)

    # Logging
    LOG_FORMAT: str = Field(default="json")
    LOG_FILE: str = Field(default="adaptive_system.log")
    ENABLE_SQL_LOGGING: bool = Field(default=False)

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of the allowed values."""
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v_upper

    @field_validator("LOG_FORMAT")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        allowed = {"json", "console"}
        if v not in allowed:
            raise ValueError(f"LOG_FORMAT must be one of {allowed}")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"

    @property
    def jwt_secret(self) -> str:
        """Get JWT secret, with fallback to JWT_SECRET if SUPABASE_JWT_SECRET not set."""
        return self.SUPABASE_JWT_SECRET or self.JWT_SECRET or ""

    class Config:
        """Pydantic config (compat for pydantic v2)."""

        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # allow unrelated env vars to coexist

    # Note: Avoid mixing Config and model_config to keep compatibility.


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get global settings instance."""
    return settings
