"""
FastAPI dependencies for authentication and authorization.

Provides dependency injection for protected routes.
"""

import structlog
from typing import Optional
from fastapi import HTTPException, status, Request
from app.services.auth_service import auth_service
from app.config import settings
from supabase import create_client, Client

logger = structlog.get_logger()


def get_supabase_client() -> Client:
    """
    Dependency to get Supabase client.

    Returns:
        Supabase client instance
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


async def get_current_user(request: Request) -> dict:
    """
    Dependency to get the current authenticated user from httpOnly cookie.

    Reads the access_token from httpOnly cookies, validates it with Supabase,
    and returns the user data.

    Args:
        request: FastAPI request object

    Returns:
        User dict with id, email, full_name, onboarding_completed

    Raises:
        HTTPException 401: If token is missing or invalid
    """
    # Get access token from httpOnly cookie
    access_token = request.cookies.get("access_token")

    if not access_token:
        logger.warning("auth_missing_token", path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate token and get user
    user = await auth_service.get_user_from_token(access_token)

    if not user:
        logger.warning("auth_invalid_token", path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("auth_success", user_id=user["id"], path=request.url.path)
    return user


async def get_current_user_optional(request: Request) -> Optional[dict]:
    """
    Dependency to get the current user if authenticated, None otherwise.

    Useful for endpoints that work for both authenticated and anonymous users.

    Args:
        request: FastAPI request object

    Returns:
        User dict or None if not authenticated
    """
    access_token = request.cookies.get("access_token")

    if not access_token:
        return None

    user = await auth_service.get_user_from_token(access_token)

    if user:
        logger.info("auth_optional_success", user_id=user["id"], path=request.url.path)

    return user


async def require_onboarding_completed(user: dict = None) -> dict:
    """
    Dependency to ensure user has completed onboarding.

    Use this in combination with get_current_user for routes that require
    onboarding to be completed.

    Args:
        user: User dict from get_current_user

    Returns:
        User dict if onboarding completed

    Raises:
        HTTPException 403: If onboarding not completed
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    if not user.get("onboarding_completed", False):
        logger.warning("onboarding_incomplete", user_id=user["id"])
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please complete onboarding first",
        )

    return user
