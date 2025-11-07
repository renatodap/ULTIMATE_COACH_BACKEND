"""
Retry Logic with Exponential Backoff

Provides retry functionality for transient failures.

Features:
- Exponential backoff
- Configurable max retries
- Selective exception handling
- Logging of retry attempts

Usage:
    @retry_with_exponential_backoff(max_retries=3)
    async def flaky_database_query():
        return await db.query(...)

    # Or as function call
    result = await retry_with_exponential_backoff(
        func=lambda: db.query(...),
        max_retries=3
    )
"""

import asyncio
import structlog
from typing import Callable, Any, Optional, Tuple, Type
from functools import wraps

logger = structlog.get_logger()


class RetryableError(Exception):
    """Base class for errors that should trigger retry."""
    pass


async def retry_with_exponential_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
) -> Any:
    """
    Retry function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation (2.0 = double each time)
        exceptions: Tuple of exception types to retry on
        on_retry: Optional callback function called on each retry

    Returns:
        Function result if successful

    Raises:
        Last exception if all retries exhausted

    Example:
        async def flaky_operation():
            result = await api_call()
            return result

        result = await retry_with_exponential_backoff(
            func=flaky_operation,
            max_retries=3,
            base_delay=2.0,
            exceptions=(TimeoutError, ConnectionError)
        )
    """
    last_exception = None

    for attempt in range(max_retries + 1):  # +1 for initial attempt
        try:
            result = await func()
            if attempt > 0:
                logger.info(
                    "retry_succeeded",
                    attempt=attempt,
                    max_retries=max_retries
                )
            return result

        except exceptions as e:
            last_exception = e

            # Last attempt - don't retry
            if attempt == max_retries:
                logger.error(
                    "retry_exhausted",
                    attempt=attempt,
                    max_retries=max_retries,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise

            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** attempt), max_delay)

            logger.warning(
                "retry_attempt",
                attempt=attempt + 1,
                max_retries=max_retries,
                delay_seconds=delay,
                error=str(e),
                error_type=type(e).__name__
            )

            # Call retry callback if provided
            if on_retry:
                try:
                    await on_retry(attempt, e)
                except Exception as callback_error:
                    logger.warning(
                        "retry_callback_failed",
                        error=str(callback_error)
                    )

            # Wait before retry
            await asyncio.sleep(delay)

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic error: no exception but no result")


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for retry with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic

    Example:
        @retry(max_retries=3, base_delay=2.0)
        async def fetch_data():
            return await api.get_data()
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_exponential_backoff(
                func=lambda: func(*args, **kwargs),
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                exceptions=exceptions
            )
        return wrapper
    return decorator


# Specialized retry decorators for common scenarios

def retry_on_database_error(max_retries: int = 3, base_delay: float = 1.0):
    """
    Retry on database-related errors.

    Retries on common transient database errors:
    - Connection errors
    - Timeout errors
    - Lock errors

    Example:
        @retry_on_database_error(max_retries=3)
        async def query_users():
            return await db.query("SELECT * FROM users")
    """
    from app.errors.exceptions import DatabaseError

    return retry(
        max_retries=max_retries,
        base_delay=base_delay,
        exceptions=(DatabaseError, ConnectionError, TimeoutError)
    )


def retry_on_external_service_error(max_retries: int = 3, base_delay: float = 2.0):
    """
    Retry on external service errors (API calls, etc.).

    Example:
        @retry_on_external_service_error(max_retries=3)
        async def call_external_api():
            return await api.fetch_data()
    """
    from app.errors.exceptions import ExternalServiceError

    return retry(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=30.0,
        exceptions=(ExternalServiceError, ConnectionError, TimeoutError)
    )


def retry_on_rate_limit(max_retries: int = 5, base_delay: float = 5.0):
    """
    Retry on rate limit errors with longer delays.

    Uses longer delays since rate limits usually have time windows.

    Example:
        @retry_on_rate_limit(max_retries=5)
        async def call_rate_limited_api():
            return await api.fetch_data()
    """
    from app.errors.exceptions import RateLimitError

    return retry(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=120.0,  # Up to 2 minutes
        exponential_base=2.0,
        exceptions=(RateLimitError,)
    )
