"""
Pydantic models for authentication.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """Request model for user signup."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")
    full_name: Optional[str] = Field(None, max_length=100, description="User's full name")


class LoginRequest(BaseModel):
    """Request model for user login."""

    email: EmailStr = Field(..., description="User email address")
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

    email: EmailStr = Field(..., description="User email address")
