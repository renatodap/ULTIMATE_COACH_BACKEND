"""
Error Handling Package

Standardized error handling utilities for the backend.

Provides:
- Retry logic with exponential backoff
- Error handlers for consistent responses
- Custom exception types
- Error logging utilities

Usage:
    from app.errors import retry_with_backoff, ToolErrorHandler

    @retry_with_backoff(max_retries=3)
    async def flaky_operation():
        ...

    try:
        result = await tool.execute()
    except Exception as e:
        return ToolErrorHandler.handle(e)
"""

from app.errors.retry import retry_with_exponential_backoff, RetryableError
from app.errors.handlers import ToolErrorHandler, ServiceErrorHandler
from app.errors.exceptions import (
    ToolExecutionError,
    DatabaseError,
    ValidationError,
    AuthenticationError,
    RateLimitError
)

__all__ = [
    # Retry utilities
    "retry_with_exponential_backoff",
    "RetryableError",

    # Error handlers
    "ToolErrorHandler",
    "ServiceErrorHandler",

    # Custom exceptions
    "ToolExecutionError",
    "DatabaseError",
    "ValidationError",
    "AuthenticationError",
    "RateLimitError",
]
