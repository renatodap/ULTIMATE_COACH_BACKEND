"""
Correlation ID Middleware

Adds correlation IDs to all requests for distributed tracing.

Benefits:
- Trace requests through the system
- Debug production issues
- Monitor request flow
- Link logs across services

Features:
- Accepts correlation ID from header (X-Correlation-ID)
- Generates new ID if not provided
- Injects into structlog context
- Returns in response header

Usage:
    from app.middleware.correlation_id import CorrelationIDMiddleware

    app.add_middleware(CorrelationIDMiddleware)
"""

import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable

logger = structlog.get_logger()


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation IDs to requests.

    Correlation IDs help trace requests through the system and
    correlate logs across different services.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and inject correlation ID.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response with correlation ID header
        """
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID")

        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Inject into structlog context (available in all logs)
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            request_id=correlation_id,  # Alias for compatibility
            request_path=request.url.path,
            request_method=request.method
        )

        # Log request start
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            correlation_id=correlation_id
        )

        try:
            # Process request
            response = await call_next(request)

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            # Log request completion
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                correlation_id=correlation_id
            )

            return response

        except Exception as e:
            # Log request error
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                correlation_id=correlation_id,
                exc_info=True
            )
            raise

        finally:
            # Clean up context
            structlog.contextvars.clear_contextvars()


# Factory function for easy initialization
def get_correlation_id_middleware():
    """
    Get correlation ID middleware instance.

    Returns:
        CorrelationIDMiddleware class
    """
    return CorrelationIDMiddleware
