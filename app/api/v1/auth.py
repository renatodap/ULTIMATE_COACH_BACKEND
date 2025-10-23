"""
Authentication API endpoints.

Handles user signup, login, logout, and token refresh.
"""

import structlog
from fastapi import APIRouter, HTTPException, status, Response
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.auth import (
    SignupRequest,
    LoginRequest,
    AuthResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
)
from app.services.auth_service import auth_service

logger = structlog.get_logger()

router = APIRouter()


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """Set secure httpOnly cookies for authentication tokens with cross-origin support."""
    # Access token (7 days)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.is_development,  # False in development (allows HTTP)
        samesite="none" if not settings.is_development else "lax",  # "none" requires secure=True in production
        path="/",  # Available across entire domain
        # Don't set domain - let browser handle it based on request origin
        max_age=60 * 60 * 24 * 7,  # 7 days
    )

    # Refresh token (30 days)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.is_development,  # False in development (allows HTTP)
        samesite="none" if not settings.is_development else "lax",  # "none" requires secure=True in production
        path="/",  # Available across entire domain
        # Don't set domain - let browser handle it based on request origin
        max_age=60 * 60 * 24 * 30,  # 30 days
    )


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sign up a new user",
    description="Create a new user account with email and password",
)
async def signup(request: SignupRequest, response: Response) -> AuthResponse:
    """
    Sign up a new user.

    Creates:
    - Supabase Auth user
    - User profile in database

    Returns:
        AuthResponse with user data (tokens set as httpOnly cookies)
    """
    try:
        result = await auth_service.signup(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
        )

        # Set auth cookies only if session tokens are present (may be None when email confirmation is required)
        access = result.get("session", {}).get("access_token")
        refresh = result.get("session", {}).get("refresh_token")
        if access and refresh:
            set_auth_cookies(
                response,
                access,
                refresh,
            )

        logger.info("user_signup_success", email=request.email)

        return AuthResponse(**result)

    except ValueError as e:
        logger.warning(
            "user_signup_validation_failed",
            extra={
                "email": request.email,
                "error": str(e),
                "error_type": "ValidationError"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "user_signup_unexpected_error",
            extra={
                "email": request.email,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        # Return user-friendly message (never expose internal errors)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create account. Please try again or contact support.",
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in a user",
    description="Authenticate user and return JWT tokens",
)
async def login(request: LoginRequest, response: Response) -> AuthResponse:
    """
    Log in an existing user.

    Args:
        request: Login credentials
        response: FastAPI response object

    Returns:
        AuthResponse with user data (tokens set as httpOnly cookies)
    """
    try:
        result = await auth_service.login(
            email=request.email,
            password=request.password,
        )

        # Set auth cookies
        set_auth_cookies(
            response,
            result["session"]["access_token"],
            result["session"]["refresh_token"],
        )

        logger.info("user_login_success", email=request.email)

        return AuthResponse(**result)

    except ValueError as e:
        logger.warning(
            "user_login_validation_failed",
            extra={
                "email": request.email,
                "error": str(e),
                "error_type": "ValidationError"
            }
        )
        # Return user-friendly error message
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "user_login_unexpected_error",
            extra={
                "email": request.email,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        # Return generic user-friendly message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to sign in. Please try again or contact support.",
        )


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Get new access token using refresh token",
)
async def refresh_token(request: RefreshTokenRequest) -> JSONResponse:
    """
    Refresh an expired access token.

    Args:
        request: Refresh token

    Returns:
        New access and refresh tokens
    """
    try:
        result = await auth_service.refresh_session(request.refresh_token)

        logger.info("token_refresh_success")

        return JSONResponse(content=result)

    except Exception as e:
        logger.error("token_refresh_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Log out a user",
    description="Revoke user session",
)
async def logout(response: Response) -> JSONResponse:
    """
    Log out the current user.

    Returns:
        Success message
    """
    try:
        await auth_service.logout("")

        # Clear httpOnly cookies on client
        # CRITICAL: Must match ALL attributes from set_cookie() for browser to recognize and delete
        # See: set_auth_cookies() lines 26-50
        try:
            response.delete_cookie(
                key="access_token",
                path="/",
                httponly=True,
                secure=not settings.is_development,
                samesite="none" if not settings.is_development else "lax",
            )
            response.delete_cookie(
                key="refresh_token",
                path="/",
                httponly=True,
                secure=not settings.is_development,
                samesite="none" if not settings.is_development else "lax",
            )
        except Exception as e:
            logger.warning("cookie_clear_failed", error=str(e))

        logger.info("user_logout_success")

        return JSONResponse(content={"message": "Logged out successfully"})

    except Exception as e:
        logger.error("user_logout_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed",
        )


@router.post(
    "/password-reset",
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Send password reset email to user",
)
async def request_password_reset(request: PasswordResetRequest) -> JSONResponse:
    """
    Send password reset email.

    Args:
        request: User email

    Returns:
        Success message
    """
    try:
        await auth_service.request_password_reset(request.email)

        logger.info("password_reset_requested", email=request.email)

        return JSONResponse(
            content={"message": "If an account exists, a password reset email has been sent"}
        )

    except Exception as e:
        logger.error("password_reset_error", email=request.email, error=str(e))
        # Always return success to prevent email enumeration
        return JSONResponse(
            content={"message": "If an account exists, a password reset email has been sent"}
        )
