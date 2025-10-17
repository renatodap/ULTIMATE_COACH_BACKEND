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
    Dependency to get the current authenticated user from httpOnly cookie or Authorization header.

    Tries multiple authentication methods (in priority order):
    1. access_token cookie (backend standard - most secure, httpOnly)
    2. sb-access-token cookie (Supabase standard - fallback)
    3. Authorization header (Bearer token - for mobile/API clients)

    PRIORITY RATIONALE:
    - Cookies are checked first because they're more secure (httpOnly, CSRF protection)
    - Cookies are the primary auth method for web clients
    - Authorization headers are secondary for mobile/API/external clients
    - This prevents issues with stale or orphaned Authorization header tokens

    Args:
        request: FastAPI request object

    Returns:
        User dict with id, email, full_name, onboarding_completed

    Raises:
        HTTPException 401: If token is missing or invalid
    """
    access_token = None
    auth_method = None

    # Method 1: Check access_token cookie (backend standard - highest priority)
    access_token = request.cookies.get("access_token")
    if access_token:
        auth_method = "access_token_cookie"

    # Method 2: Check sb-access-token cookie (Supabase standard - fallback)
    if not access_token:
        access_token = request.cookies.get("sb-access-token")
        if access_token:
            auth_method = "sb_access_token_cookie"

    # Method 3: Check Authorization header (Bearer token - for mobile/API clients)
    if not access_token:
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            access_token = auth_header.split(" ", 1)[1]
            auth_method = "header"

    if not access_token:
        logger.warning(
            "auth_missing_token",
            path=request.url.path,
            has_auth_header=bool(auth_header),
            has_cookies=bool(request.cookies)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid input: Neither bearer token or basic authentication scheme is provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate token and get user
    user = await auth_service.get_user_from_token(access_token)

    if not user:
        logger.warning(
            "auth_invalid_token",
            path=request.url.path,
            auth_method=auth_method,
            token_prefix=access_token[:20] if access_token else None
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(
        "auth_success",
        user_id=user["id"],
        path=request.url.path,
        auth_method=auth_method
    )
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
