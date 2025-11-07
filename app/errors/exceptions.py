"""
Custom Exception Types

Standardized exception hierarchy for the backend.

All custom exceptions include:
- Error code for API responses
- Human-readable message
- Optional metadata

Usage:
    raise ToolExecutionError(
        message="Tool execution failed",
        tool_name="get_user_profile",
        user_id="123"
    )
"""

from typing import Dict, Any, Optional


class BaseError(Exception):
    """Base exception for all custom errors."""

    code: str = "ERROR_000"
    default_message: str = "An error occurred"
    http_status: int = 500

    def __init__(
        self,
        message: Optional[str] = None,
        **metadata
    ):
        """
        Initialize error.

        Args:
            message: Error message (uses default if not provided)
            **metadata: Additional error context
        """
        self.message = message or self.default_message
        self.metadata = metadata
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to dictionary for API responses.

        Returns:
            Dict with code, message, and metadata
        """
        return {
            "error": self.code,
            "message": self.message,
            "metadata": self.metadata
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.__class__.__name__}(code={self.code}, message={self.message})"


class ToolExecutionError(BaseError):
    """Error during tool execution."""

    code = "TOOL_001"
    default_message = "Tool execution failed"
    http_status = 500


class DatabaseError(BaseError):
    """Database operation error."""

    code = "DATABASE_001"
    default_message = "Database operation failed"
    http_status = 500


class ValidationError(BaseError):
    """Data validation error."""

    code = "VALIDATION_001"
    default_message = "Validation failed"
    http_status = 400


class AuthenticationError(BaseError):
    """Authentication error."""

    code = "AUTH_001"
    default_message = "Authentication failed"
    http_status = 401


class AuthorizationError(BaseError):
    """Authorization error."""

    code = "AUTH_002"
    default_message = "Unauthorized access"
    http_status = 403


class RateLimitError(BaseError):
    """Rate limit exceeded."""

    code = "RATE_LIMIT_001"
    default_message = "Rate limit exceeded"
    http_status = 429


class NotFoundError(BaseError):
    """Resource not found."""

    code = "NOT_FOUND_001"
    default_message = "Resource not found"
    http_status = 404


class ConflictError(BaseError):
    """Resource conflict."""

    code = "CONFLICT_001"
    default_message = "Resource conflict"
    http_status = 409


class ExternalServiceError(BaseError):
    """External service error."""

    code = "EXTERNAL_001"
    default_message = "External service error"
    http_status = 502


class TimeoutError(BaseError):
    """Operation timeout."""

    code = "TIMEOUT_001"
    default_message = "Operation timed out"
    http_status = 504


# Nutrition-specific errors
class FoodNotFoundError(NotFoundError):
    """Food not found in database."""

    code = "NUTRITION_001"
    default_message = "Food not found"


class InvalidServingError(ValidationError):
    """Invalid serving data."""

    code = "NUTRITION_002"
    default_message = "Invalid serving"


class MealCreationError(DatabaseError):
    """Meal creation failed."""

    code = "NUTRITION_003"
    default_message = "Meal creation failed"


# Activity-specific errors
class ActivityValidationError(ValidationError):
    """Activity validation failed."""

    code = "ACTIVITY_001"
    default_message = "Activity validation failed"


class InvalidMETsError(ValidationError):
    """Invalid METs value."""

    code = "ACTIVITY_002"
    default_message = "Invalid METs value"


# Coach-specific errors
class ConversationNotFoundError(NotFoundError):
    """Conversation not found."""

    code = "COACH_001"
    default_message = "Conversation not found"


class MessageSaveError(DatabaseError):
    """Message save failed."""

    code = "COACH_002"
    default_message = "Message save failed"


class LanguageDetectionError(BaseError):
    """Language detection failed."""

    code = "COACH_003"
    default_message = "Language detection failed"
    http_status = 500
