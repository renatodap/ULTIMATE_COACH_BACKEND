"""
Error Handlers

Standardized error handling for consistent responses across the application.

Provides handlers for:
- Tool execution errors
- Service errors
- API errors
- Database errors

Usage:
    try:
        result = await tool.execute()
    except Exception as e:
        return ToolErrorHandler.handle(e)
"""

import structlog
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.errors.exceptions import BaseError

logger = structlog.get_logger()


class ToolErrorHandler:
    """
    Standardized error handling for tool execution.

    Ensures all tools return consistent error responses.
    """

    @staticmethod
    def handle(
        error: Exception,
        tool_name: Optional[str] = None,
        user_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle tool execution error and return standardized response.

        Args:
            error: Exception that occurred
            tool_name: Name of tool that failed
            user_id: User ID (for logging)
            params: Tool parameters (for logging)

        Returns:
            Standardized error response dict

        Example:
            try:
                result = await tool.execute(user_id, params)
                return result
            except Exception as e:
                return ToolErrorHandler.handle(e, "get_user_profile", user_id, params)
        """
        # Log error with context
        logger.error(
            "tool_execution_error",
            tool_name=tool_name,
            user_id=user_id,
            error=str(error),
            error_type=type(error).__name__,
            params=params,
            exc_info=True
        )

        # Handle custom errors
        if isinstance(error, BaseError):
            return {
                "error": error.code,
                "message": error.message,
                "metadata": error.metadata
            }

        # Handle generic errors
        return {
            "error": "TOOL_EXECUTION_ERROR",
            "message": f"Tool execution failed: {str(error)}",
            "tool_name": tool_name
        }

    @staticmethod
    def handle_with_fallback(
        error: Exception,
        fallback_value: Any,
        tool_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Any:
        """
        Handle error and return fallback value instead of error dict.

        Useful for non-critical operations where we want to continue
        with a default value rather than failing.

        Args:
            error: Exception that occurred
            fallback_value: Value to return on error
            tool_name: Name of tool that failed
            user_id: User ID (for logging)

        Returns:
            Fallback value

        Example:
            try:
                metrics = await get_body_metrics(user_id)
            except Exception as e:
                metrics = ToolErrorHandler.handle_with_fallback(
                    e, fallback_value=[], tool_name="get_body_metrics"
                )
        """
        logger.warning(
            "tool_execution_error_with_fallback",
            tool_name=tool_name,
            user_id=user_id,
            error=str(error),
            fallback_value=type(fallback_value).__name__
        )

        return fallback_value


class ServiceErrorHandler:
    """
    Standardized error handling for service layer.

    Converts errors to appropriate HTTP responses.
    """

    @staticmethod
    def to_http_exception(error: Exception) -> HTTPException:
        """
        Convert error to HTTPException for FastAPI.

        Args:
            error: Exception to convert

        Returns:
            HTTPException with appropriate status code

        Example:
            try:
                result = await service.operation()
            except Exception as e:
                raise ServiceErrorHandler.to_http_exception(e)
        """
        # Custom errors have http_status
        if isinstance(error, BaseError):
            return HTTPException(
                status_code=error.http_status,
                detail={
                    "error": error.code,
                    "message": error.message,
                    "metadata": error.metadata
                }
            )

        # Generic errors default to 500
        logger.error(
            "unhandled_service_error",
            error=str(error),
            error_type=type(error).__name__,
            exc_info=True
        )

        return HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred"
            }
        )

    @staticmethod
    def handle_database_error(
        error: Exception,
        operation: str,
        **context
    ) -> HTTPException:
        """
        Handle database operation error.

        Args:
            error: Exception that occurred
            operation: Operation being performed (e.g., "create_user")
            **context: Additional context for logging

        Returns:
            HTTPException

        Example:
            try:
                user = await db.create_user(data)
            except Exception as e:
                raise ServiceErrorHandler.handle_database_error(
                    e, "create_user", user_id=user_id
                )
        """
        logger.error(
            "database_error",
            operation=operation,
            error=str(error),
            error_type=type(error).__name__,
            context=context,
            exc_info=True
        )

        return HTTPException(
            status_code=500,
            detail={
                "error": "DATABASE_ERROR",
                "message": f"Database operation failed: {operation}",
                "operation": operation
            }
        )

    @staticmethod
    def handle_validation_error(
        error: Exception,
        field: Optional[str] = None,
        **context
    ) -> HTTPException:
        """
        Handle validation error.

        Args:
            error: Exception that occurred
            field: Field that failed validation
            **context: Additional context

        Returns:
            HTTPException with 400 status

        Example:
            if not is_valid_email(email):
                raise ServiceErrorHandler.handle_validation_error(
                    ValueError("Invalid email"),
                    field="email",
                    value=email
                )
        """
        logger.warning(
            "validation_error",
            field=field,
            error=str(error),
            context=context
        )

        return HTTPException(
            status_code=400,
            detail={
                "error": "VALIDATION_ERROR",
                "message": str(error),
                "field": field
            }
        )


class APIErrorHandler:
    """
    Centralized error handling for API endpoints.

    Use in FastAPI exception handlers.
    """

    @staticmethod
    async def handle_unexpected_error(error: Exception) -> Dict[str, Any]:
        """
        Handle unexpected errors in API endpoints.

        Args:
            error: Exception that occurred

        Returns:
            Error response dict

        Example:
            @app.exception_handler(Exception)
            async def global_exception_handler(request, exc):
                return await APIErrorHandler.handle_unexpected_error(exc)
        """
        logger.error(
            "unexpected_api_error",
            error=str(error),
            error_type=type(error).__name__,
            exc_info=True
        )

        # Don't expose internal errors to client
        return {
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later."
        }

    @staticmethod
    def format_validation_error(errors: list) -> Dict[str, Any]:
        """
        Format Pydantic validation errors for API response.

        Args:
            errors: List of validation errors from Pydantic

        Returns:
            Formatted error response

        Example:
            try:
                data = RequestModel(**request_data)
            except ValidationError as e:
                return APIErrorHandler.format_validation_error(e.errors())
        """
        formatted_errors = []
        for error in errors:
            formatted_errors.append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })

        return {
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "errors": formatted_errors
        }
