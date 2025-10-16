"""
Authentication service for user signup, login, and JWT token management.

Uses Supabase Auth for user management.
"""

import structlog
from typing import Dict, Any, Optional
from uuid import UUID

from app.config import settings
from app.services.supabase_service import supabase_service

logger = structlog.get_logger()


class AuthService:
    """
    Authentication service using Supabase Auth.

    Handles:
    - User signup with profile creation
    - User login with JWT tokens
    - Password reset
    - Email verification
    """

    async def signup(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sign up a new user and create their profile.

        Args:
            email: User email
            password: User password (min 6 chars)
            full_name: Optional full name

        Returns:
            Dict with user data and session tokens

        Raises:
            Exception: If signup fails
        """
        try:
            # Create user in Supabase Auth, passing full_name as metadata
            #
            # PROFILE CREATION - 3 LAYERS OF DEFENSE:
            # Layer 1 (Proactive): Migration 038 adds trigger (handle_new_user) that auto-creates
            #                      profile on signup. Best practice, cleanest solution.
            # Layer 2 (Reactive):  update_profile() uses service role for INSERT, bypassing RLS.
            #                      Works even if migration not applied or trigger fails.
            # Layer 3 (Emergency): get_user_from_token() creates profile if missing on any auth.
            #                      Self-healing for existing users who signed up before fixes.
            #
            signup_options: dict[str, Any] = {
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "onboarding_completed": False,
                    }
                },
            }
            # If FRONTEND_URL configured, set email redirect for confirmation
            if settings.FRONTEND_URL:
                signup_options["options"]["email_redirect_to"] = f"{settings.FRONTEND_URL}/auth/callback"

            auth_response = supabase_service.client.auth.sign_up(signup_options)

            if not auth_response.user:
                raise ValueError("Failed to create user account")

            user_id = UUID(auth_response.user.id)

            # Structured log with Supabase response metadata
            logger.info(
                "supabase_signup_success",
                extra={
                    "email": email,
                    "user_id": str(user_id),
                    "session_present": bool(auth_response.session),
                    "email_confirmed_at": getattr(auth_response.user, "email_confirmed_at", None),
                    "email_redirect_to": signup_options["options"].get("email_redirect_to"),
                },
            )

            return {
                "user": {
                    "id": str(user_id),
                    "email": email,
                    "full_name": full_name,
                },
                "session": {
                    "access_token": auth_response.session.access_token if auth_response.session else None,
                    "refresh_token": auth_response.session.refresh_token if auth_response.session else None,
                },
            }

        except Exception as e:
            message = str(e)
            # Try to extract HTTP details from underlying client error (httpx)
            status_code = None
            response_text = None
            try:
                resp = getattr(e, "response", None)
                if resp is not None:
                    status_code = getattr(resp, "status_code", None)
                    response_text = getattr(resp, "text", None)
            except Exception:
                pass

            logger.error(
                "supabase_signup_error",
                extra={
                    "email": email,
                    "error": message,
                    "error_type": type(e).__name__,
                    "http_status": status_code,
                    "http_body": response_text,
                },
            )
            # Normalize common Supabase errors to 400s
            lower = message.lower()
            if "already" in lower and ("registered" in lower or "exists" in lower or "duplicate" in lower):
                raise ValueError("User already exists. Please sign in or use a different email.")
            raise

    async def login(
        self,
        email: str,
        password: str,
    ) -> Dict[str, Any]:
        """
        Log in an existing user.

        Args:
            email: User email
            password: User password

        Returns:
            Dict with user data and session tokens

        Raises:
            Exception: If login fails
        """
        try:
            # Sign in with Supabase Auth
            auth_response = supabase_service.client.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })

            if not auth_response.user:
                raise ValueError("Invalid credentials")

            # Enforce email confirmation before allowing login
            # Supabase user usually exposes `email_confirmed_at` when verified
            email_confirmed_at = getattr(auth_response.user, "email_confirmed_at", None)
            if not email_confirmed_at:
                raise ValueError("Email not confirmed. Please check your email to verify your account.")

            user_id = UUID(auth_response.user.id)

            # Get user profile
            profile = await supabase_service.get_profile(user_id)

            logger.info(f"User logged in successfully: {email}")

            return {
                "user": {
                    "id": str(user_id),
                    "email": email,
                    "full_name": profile.get("full_name") if profile else None,
                    "onboarding_completed": profile.get("onboarding_completed", False) if profile else False,
                },
                "session": {
                    "access_token": auth_response.session.access_token if auth_response.session else None,
                    "refresh_token": auth_response.session.refresh_token if auth_response.session else None,
                },
            }

        except Exception as e:
            message = str(e)
            logger.error(f"Login failed for {email}: {message}")
            lower = message.lower()
            # Normalize common GoTrue errors
            if "invalid login credentials" in lower or "invalid credentials" in lower:
                raise ValueError("Invalid email or password")
            if "email not confirmed" in lower or "email not confirmed" in lower:
                raise ValueError("Email not confirmed. Please check your email to verify your account.")
            raise

    async def get_user_from_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user data from JWT access token.

        Args:
            access_token: JWT access token

        Returns:
            User dict or None if invalid token
        """
        try:
            # Verify token with Supabase
            user_response = supabase_service.client.auth.get_user(access_token)

            if not user_response.user:
                logger.warning("Token validation failed: No user in response")
                return None

            user_id = UUID(user_response.user.id)
            profile = await supabase_service.get_profile(user_id)

            # LAYER 3 FIX: Emergency fallback - create profile if missing
            # This handles existing users who signed up before trigger was added
            # Self-healing on any authenticated request
            if not profile:
                logger.warning(
                    f"User {user_id} authenticated but profile not found - creating emergency profile",
                    extra={
                        "user_id": str(user_id),
                        "email": user_response.user.email
                    }
                )
                try:
                    # Get full_name from user metadata if available
                    full_name = user_response.user.user_metadata.get("full_name") if user_response.user.user_metadata else None

                    # Create profile using create_profile (uses service role)
                    profile = await supabase_service.create_profile(user_id, {
                        "full_name": full_name,
                        "onboarding_completed": False,
                    })
                    logger.info(f"Emergency profile created successfully for user {user_id}")
                except Exception as e:
                    logger.error(
                        f"Failed to create emergency profile for user {user_id}",
                        extra={
                            "error": str(e),
                            "error_type": type(e).__name__
                        },
                        exc_info=True
                    )
                    # Profile will be None, but don't fail authentication
                    # Let the user continue and we'll try again on next request

            return {
                "id": str(user_id),
                "email": user_response.user.email,
                "full_name": profile.get("full_name") if profile else None,
                "onboarding_completed": profile.get("onboarding_completed", False) if profile else False,
            }

        except Exception as e:
            logger.error(
                "Token validation failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "token_prefix": access_token[:20] if access_token else None
                },
                exc_info=True
            )
            return None

    async def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token using refresh token.

        Args:
            refresh_token: Refresh token from login

        Returns:
            Dict with new access and refresh tokens

        Raises:
            Exception: If refresh fails
        """
        try:
            auth_response = supabase_service.client.auth.refresh_session(refresh_token)

            if not auth_response.session:
                raise ValueError("Failed to refresh session")

            logger.info("Session refreshed successfully")

            return {
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token,
            }

        except Exception as e:
            logger.error(f"Session refresh failed: {e}")
            raise

    async def logout(self, access_token: str) -> bool:
        """
        Log out a user (revoke token).

        Args:
            access_token: JWT access token

        Returns:
            True if successful
        """
        try:
            supabase_service.client.auth.sign_out()
            logger.info("User logged out successfully")
            return True

        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False

    async def request_password_reset(self, email: str) -> bool:
        """
        Send password reset email.

        Args:
            email: User email

        Returns:
            True if email sent
        """
        try:
            supabase_service.client.auth.reset_password_for_email(email)
            logger.info(f"Password reset email sent to {email}")
            return True

        except Exception as e:
            logger.error(f"Password reset request failed for {email}: {e}")
            return False


# Global singleton instance
auth_service = AuthService()
