"""
Personalized Coaching Configuration

Centralized configuration for all personalized coaching features.
ALL hard-coded values extracted here for easy modification without code changes.

Future-proof: Add env vars to override any value.
"""

import os
from typing import Dict, Any


class PersonalizedCoachingConfig:
    """Configuration for personalized coaching system."""

    # ========================================================================
    # CONVERSATIONAL PROFILE GENERATION
    # ========================================================================

    # Target word count for conversational profile
    PROFILE_WORD_COUNT: int = int(os.getenv("PROFILE_WORD_COUNT", "200"))

    # Claude model for profile generation
    PROFILE_MODEL: str = os.getenv("PROFILE_MODEL", "claude-3-5-sonnet-20241022")

    # Max tokens for profile generation
    PROFILE_MAX_TOKENS: int = int(os.getenv("PROFILE_MAX_TOKENS", "500"))

    # Temperature for profile generation (creativity)
    PROFILE_TEMPERATURE: float = float(os.getenv("PROFILE_TEMPERATURE", "0.7"))

    # ========================================================================
    # SYSTEM PROMPT GENERATION
    # ========================================================================

    # Target word range for system prompts
    PROMPT_MIN_WORDS: int = int(os.getenv("PROMPT_MIN_WORDS", "500"))
    PROMPT_MAX_WORDS: int = int(os.getenv("PROMPT_MAX_WORDS", "800"))

    # Claude model for prompt generation
    PROMPT_MODEL: str = os.getenv("PROMPT_MODEL", "claude-3-5-sonnet-20241022")

    # Max tokens for prompt generation
    PROMPT_MAX_TOKENS: int = int(os.getenv("PROMPT_MAX_TOKENS", "2000"))

    # Temperature for prompt generation
    PROMPT_TEMPERATURE: float = float(os.getenv("PROMPT_TEMPERATURE", "0.7"))

    # ========================================================================
    # BEHAVIORAL CHANGE DETECTION THRESHOLDS
    # ========================================================================

    # Minimum adherence rate change to trigger prompt update (0.10 = 10%)
    ADHERENCE_CHANGE_THRESHOLD: float = float(
        os.getenv("ADHERENCE_CHANGE_THRESHOLD", "0.10")
    )

    # Minimum logging rate change to trigger prompt update (0.10 = 10%)
    LOGGING_CHANGE_THRESHOLD: float = float(
        os.getenv("LOGGING_CHANGE_THRESHOLD", "0.10")
    )

    # Minimum streak change (in days) to trigger prompt update
    STREAK_CHANGE_THRESHOLD: int = int(
        os.getenv("STREAK_CHANGE_THRESHOLD", "7")
    )

    # Days of behavioral data to analyze for updates
    BEHAVIORAL_ANALYSIS_DAYS: int = int(
        os.getenv("BEHAVIORAL_ANALYSIS_DAYS", "30")
    )

    # ========================================================================
    # BACKGROUND JOB SCHEDULES
    # ========================================================================

    # Weekly prompt update schedule (cron format: day_of_week, hour, minute)
    PROMPT_UPDATE_DAY: str = os.getenv("PROMPT_UPDATE_DAY", "sun")  # Sunday
    PROMPT_UPDATE_HOUR: int = int(os.getenv("PROMPT_UPDATE_HOUR", "3"))  # 3 AM
    PROMPT_UPDATE_MINUTE: int = int(os.getenv("PROMPT_UPDATE_MINUTE", "0"))

    # Minimum days between prompt updates (prevents too-frequent updates)
    MIN_DAYS_BETWEEN_UPDATES: int = int(
        os.getenv("MIN_DAYS_BETWEEN_UPDATES", "7")
    )

    # ========================================================================
    # COST OPTIMIZATION
    # ========================================================================

    # Enable/disable change detection (if false, always updates)
    ENABLE_CHANGE_DETECTION: bool = os.getenv(
        "ENABLE_CHANGE_DETECTION", "true"
    ).lower() == "true"

    # Log costs for monitoring
    LOG_PROMPT_GENERATION_COSTS: bool = os.getenv(
        "LOG_PROMPT_GENERATION_COSTS", "true"
    ).lower() == "true"

    # Estimated cost per prompt generation (for logging)
    ESTIMATED_COST_PER_PROMPT: float = float(
        os.getenv("ESTIMATED_COST_PER_PROMPT", "0.05")
    )

    # ========================================================================
    # FEATURE FLAGS
    # ========================================================================

    # Enable automatic prompt updates via background jobs
    ENABLE_AUTOMATIC_UPDATES: bool = os.getenv(
        "ENABLE_AUTOMATIC_UPDATES", "true"
    ).lower() == "true"

    # Enable fallback to generic prompt if personalized fails
    ENABLE_GENERIC_FALLBACK: bool = os.getenv(
        "ENABLE_GENERIC_FALLBACK", "true"
    ).lower() == "true"

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    @classmethod
    def get_change_detection_thresholds(cls) -> Dict[str, Any]:
        """Get all change detection thresholds as dict."""
        return {
            "adherence_threshold": cls.ADHERENCE_CHANGE_THRESHOLD,
            "logging_threshold": cls.LOGGING_CHANGE_THRESHOLD,
            "streak_threshold": cls.STREAK_CHANGE_THRESHOLD,
            "enabled": cls.ENABLE_CHANGE_DETECTION
        }

    @classmethod
    def get_prompt_update_schedule(cls) -> Dict[str, Any]:
        """Get prompt update schedule as dict."""
        return {
            "day_of_week": cls.PROMPT_UPDATE_DAY,
            "hour": cls.PROMPT_UPDATE_HOUR,
            "minute": cls.PROMPT_UPDATE_MINUTE,
            "min_days_between": cls.MIN_DAYS_BETWEEN_UPDATES
        }

    @classmethod
    def should_update_prompt(
        cls,
        adherence_change: float,
        logging_change: float,
        streak_change: int
    ) -> bool:
        """
        Determine if prompt should be updated based on behavioral changes.

        Args:
            adherence_change: Absolute change in adherence rate (0-1)
            logging_change: Absolute change in logging rate (0-1)
            streak_change: Absolute change in streak days

        Returns:
            True if any threshold is exceeded, False otherwise
        """
        if not cls.ENABLE_CHANGE_DETECTION:
            return True  # Always update if change detection disabled

        return (
            adherence_change >= cls.ADHERENCE_CHANGE_THRESHOLD
            or logging_change >= cls.LOGGING_CHANGE_THRESHOLD
            or abs(streak_change) >= cls.STREAK_CHANGE_THRESHOLD
        )


# Export singleton instance
config = PersonalizedCoachingConfig()
