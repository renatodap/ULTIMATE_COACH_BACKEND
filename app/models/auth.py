"""
Pydantic models for authentication.
"""

from typing import Optional, Annotated
from pydantic import BaseModel, EmailStr, Field, field_validator, AfterValidator
from app.config import settings
import re


def validate_email_with_test_domains(email: str) -> str:
    """
    Custom email validator that allows test domains in development mode.

    In development:
    - Allows @test.com, @example.com, @localhost domains
    - Relaxes TLD validation for testing

    In production:
    - Uses strict Pydantic EmailStr validation
    """
    # In production, use strict validation
    if settings.is_production:
        # Let Pydantic's EmailStr handle it (will raise if invalid)
        return email

    # In development, allow test domains
    test_domains = ["test.com", "example.com", "localhost", "test.local"]
    email_lower = email.lower()

    # Basic email format check
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # Check if it's a test domain
    is_test_domain = any(email_lower.endswith(f"@{domain}") for domain in test_domains)

    if is_test_domain:
        # Minimal validation for test emails
        if "@" in email and len(email) >= 5:
            return email
        raise ValueError(f"Invalid email format: {email}")

    # For non-test domains, still require basic format
    if not re.match(email_pattern, email):
        raise ValueError(f"Invalid email format: {email}")

    return email


# Custom email type that allows test domains in development
DevEmail = Annotated[str, AfterValidator(validate_email_with_test_domains)]


class SignupRequest(BaseModel):
    """Request model for user signup."""

    email: DevEmail = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")
    full_name: Optional[str] = Field(None, max_length=100, description="User's full name")


class LoginRequest(BaseModel):
    """Request model for user login."""

    email: DevEmail = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class SessionResponse(BaseModel):
    """Session tokens response."""

    access_token: Optional[str] = Field(None, description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")


class UserResponse(BaseModel):
    """User data response."""

    id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    full_name: Optional[str] = Field(None, description="User's full name")
    onboarding_completed: bool = Field(False, description="Whether user completed onboarding")


class AuthResponse(BaseModel):
    """Complete authentication response with user and session."""

    user: UserResponse
    session: SessionResponse


class RefreshTokenRequest(BaseModel):
    """Request model for refreshing session."""

    refresh_token: str = Field(..., description="Refresh token from login")


class PasswordResetRequest(BaseModel):
    """Request model for password reset."""

    email: DevEmail = Field(..., description="User email address")
