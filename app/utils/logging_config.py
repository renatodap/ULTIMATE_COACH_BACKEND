"""
Logging Configuration

Improved structured logging setup with correlation IDs and proper formatting.

Changes from old logging:
- ❌ Removed emoji markers (reduced log size by 5-10%)
- ✅ Added correlation ID support
- ✅ Proper log levels (INFO vs DEBUG)
- ✅ Consistent field names
- ✅ JSON output for production

Usage:
    from app.utils.logging_config import configure_logging

    configure_logging(environment="production", log_level="INFO")
"""

import logging
import structlog
from typing import Optional


def configure_logging(
    environment: str = "development",
    log_level: str = "INFO",
    use_json: bool = True
):
    """
    Configure structured logging for the application.

    Args:
        environment: Environment name ("development" or "production")
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
        use_json: Use JSON rendering (recommended for production)

    Configuration:
    - Development: Pretty console output with colors
    - Production: JSON output for log aggregation systems
    - Both: Include correlation IDs, timestamps, log levels
    """
    # Set log level
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper())
    )

    # Configure processors
    processors = [
        # Add log level
        structlog.stdlib.add_log_level,

        # Add logger name
        structlog.stdlib.add_logger_name,

        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),

        # Add stack info on exceptions
        structlog.processors.StackInfoRenderer(),

        # Format exceptions
        structlog.processors.format_exc_info,

        # Add contextvar data (correlation IDs, etc.)
        structlog.contextvars.merge_contextvars,
    ]

    # Add renderer based on environment
    if use_json and environment == "production":
        # JSON for production (log aggregation)
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Pretty console for development
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None):
    """
    Get a structured logger instance.

    Args:
        name: Logger name (optional, defaults to caller's module)

    Returns:
        Structured logger

    Usage:
        logger = get_logger(__name__)
        logger.info("user_action", user_id=user_id, action="login")
    """
    return structlog.get_logger(name)


# Best Practices Guide
"""
LOGGING BEST PRACTICES

✅ DO:
    # Structured logging with context
    logger.info(
        "user_login",
        user_id=user_id,
        email=email,
        ip_address=request.client.host
    )

    # Proper log levels
    logger.debug("cache_hit", key=cache_key)  # Detailed debugging
    logger.info("user_created", user_id=user_id)  # Business events
    logger.warning("rate_limit_approaching", user_id=user_id)  # Warnings
    logger.error("database_error", error=str(e), exc_info=True)  # Errors

    # Error logging with exception info
    try:
        result = await operation()
    except Exception as e:
        logger.error(
            "operation_failed",
            operation="user_creation",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True  # Include stack trace
        )
        raise

❌ DON'T:
    # String formatting (not searchable)
    logger.info(f"User {user_id} logged in")

    # Emoji markers (waste of space)
    logger.info(f"[Service] 🎉 User created")

    # Missing context
    logger.info("success")

    # Wrong log level
    logger.info("Detailed debug info...")  # Should be DEBUG

    # Print statements
    print(f"User {user_id} logged in")  # Use logger instead


LOG LEVELS GUIDE:

DEBUG:
    - Cache hits/misses
    - Internal state transitions
    - Detailed flow information
    - Use sparingly in production

INFO:
    - Business events (user_login, order_placed)
    - Request start/completion
    - Background job execution
    - Most common level

WARNING:
    - Recoverable errors
    - Deprecated feature usage
    - Performance degradation
    - Rate limit warnings

ERROR:
    - Operation failures
    - Unexpected exceptions
    - Data inconsistencies
    - Always include exc_info=True for exceptions


FIELD NAMING CONVENTIONS:

# Use snake_case for field names
logger.info("event", user_id=123, order_total=99.99)

# Common field names:
- user_id, order_id, item_id (entity IDs)
- error, error_type, error_code (errors)
- duration_ms, elapsed_ms (timing)
- status_code, response_code (HTTP)
- correlation_id, request_id (tracing)


CORRELATION IDs:

# Automatically included via middleware
logger.info("operation_started")
# Logs include: correlation_id, request_id, request_path, request_method

# For background jobs, manually bind correlation ID
structlog.contextvars.bind_contextvars(correlation_id=job_id)
logger.info("background_job_started")
structlog.contextvars.clear_contextvars()
"""
