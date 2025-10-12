"""
Structured logging utilities for consistent logging across the application.

This module enforces logging standards and provides type-safe logging helpers.
"""

import structlog
from typing import Any, Optional
from uuid import UUID

logger = structlog.get_logger()


# ============================================================================
# AUTHENTICATION EVENTS
# ============================================================================

def log_signup_success(user_id: str | UUID, email: str) -> None:
    """Log successful user signup."""
    logger.info("user_signup_success", user_id=str(user_id), email=email)


def log_login_success(user_id: str | UUID, email: str, ip: Optional[str] = None) -> None:
    """Log successful user login."""
    logger.info("user_login_success", user_id=str(user_id), email=email, ip=ip)


def log_logout(user_id: str | UUID) -> None:
    """Log user logout."""
    logger.info("user_logout", user_id=str(user_id))


def log_auth_missing_token(path: str) -> None:
    """Log missing authentication token."""
    logger.warning("auth_missing_token", path=path)


def log_auth_invalid_token(path: str, reason: Optional[str] = None) -> None:
    """Log invalid authentication token."""
    logger.warning("auth_invalid_token", path=path, reason=reason)


def log_token_refresh_success(user_id: str | UUID) -> None:
    """Log successful token refresh."""
    logger.info("token_refresh_success", user_id=str(user_id))


def log_token_refresh_failed(reason: str) -> None:
    """Log failed token refresh."""
    logger.error("token_refresh_failed", reason=reason)


# ============================================================================
# DATABASE EVENTS
# ============================================================================

def log_profile_created(user_id: str | UUID) -> None:
    """Log profile creation."""
    logger.info("profile_created", user_id=str(user_id))


def log_profile_updated(user_id: str | UUID, fields: list[str]) -> None:
    """Log profile update."""
    logger.info("profile_updated", user_id=str(user_id), fields=fields)


def log_profile_not_found(user_id: str | UUID) -> None:
    """Log profile not found error."""
    logger.error("profile_not_found", user_id=str(user_id))


def log_meal_created(user_id: str | UUID, meal_id: str | UUID) -> None:
    """Log meal creation."""
    logger.info("meal_created", user_id=str(user_id), meal_id=str(meal_id))


def log_meal_deleted(user_id: str | UUID, meal_id: str | UUID) -> None:
    """Log meal deletion."""
    logger.info("meal_deleted", user_id=str(user_id), meal_id=str(meal_id))


def log_activity_created(user_id: str | UUID, activity_id: str | UUID, activity_type: str) -> None:
    """Log activity creation."""
    logger.info(
        "activity_created",
        user_id=str(user_id),
        activity_id=str(activity_id),
        activity_type=activity_type
    )


def log_db_query_failed(table: str, operation: str, error: str) -> None:
    """Log database query failure."""
    logger.error("db_query_failed", table=table, operation=operation, error=error)


# ============================================================================
# API EVENTS
# ============================================================================

def log_api_request(method: str, path: str, status: int, duration_ms: Optional[float] = None) -> None:
    """Log API request."""
    logger.info("api_request", method=method, path=path, status=status, duration_ms=duration_ms)


def log_api_error(method: str, path: str, status: int, error: str, error_type: Optional[str] = None) -> None:
    """Log API error."""
    logger.error(
        "api_error",
        method=method,
        path=path,
        status=status,
        error=error,
        error_type=error_type
    )


def log_validation_error(endpoint: str, errors: list[dict]) -> None:
    """Log validation error."""
    logger.warning("validation_error", endpoint=endpoint, errors=errors)


# ============================================================================
# AI/COACH EVENTS
# ============================================================================

def log_conversation_created(user_id: str | UUID, conversation_id: str | UUID) -> None:
    """Log conversation creation."""
    logger.info("conversation_created", user_id=str(user_id), conversation_id=str(conversation_id))


def log_message_sent(
    user_id: str | UUID,
    conversation_id: str | UUID,
    role: str,
    token_count: Optional[int] = None
) -> None:
    """Log message sent in conversation."""
    logger.info(
        "message_sent",
        user_id=str(user_id),
        conversation_id=str(conversation_id),
        role=role,
        token_count=token_count
    )


def log_ai_request(provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> None:
    """Log AI API request."""
    logger.info(
        "ai_request",
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens
    )


def log_ai_error(provider: str, model: str, error: str, error_type: Optional[str] = None) -> None:
    """Log AI API error."""
    logger.error("ai_error", provider=provider, model=model, error=error, error_type=error_type)


# ============================================================================
# SYSTEM EVENTS
# ============================================================================

def log_startup(environment: str, debug: bool, log_level: str) -> None:
    """Log application startup."""
    logger.info("application_startup", environment=environment, debug=debug, log_level=log_level)


def log_shutdown() -> None:
    """Log application shutdown."""
    logger.info("application_shutdown")


def log_health_check(status: str, details: Optional[dict] = None) -> None:
    """Log health check."""
    logger.info("health_check", status=status, details=details)


def log_unhandled_exception(error: Exception, path: str, method: str) -> None:
    """Log unhandled exception."""
    logger.critical(
        "unhandled_exception",
        error=str(error),
        error_type=type(error).__name__,
        path=path,
        method=method,
        exc_info=True
    )


# ============================================================================
# PERFORMANCE EVENTS
# ============================================================================

def log_slow_query(query: str, duration_ms: float, threshold_ms: float = 1000) -> None:
    """Log slow database query."""
    if duration_ms > threshold_ms:
        logger.warning("slow_query", query=query[:100], duration_ms=duration_ms)


def log_cache_hit(key: str) -> None:
    """Log cache hit."""
    logger.debug("cache_hit", key=key)


def log_cache_miss(key: str) -> None:
    """Log cache miss."""
    logger.debug("cache_miss", key=key)


# ============================================================================
# CUSTOM EVENT LOGGER
# ============================================================================

def log_event(
    event_name: str,
    level: str = "info",
    **kwargs: Any
) -> None:
    """
    Generic event logger for custom events.

    Use this sparingly - prefer specific log functions above for consistency.

    Args:
        event_name: Snake_case event name (e.g., "feature_flag_enabled")
        level: Log level (debug, info, warning, error, critical)
        **kwargs: Additional context
    """
    log_fn = getattr(logger, level.lower(), logger.info)
    log_fn(event_name, **kwargs)
