"""
User profile API endpoints.

Handles user profile operations (requires authentication).
"""

import structlog
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse

from app.api.dependencies import get_current_user
from app.services.supabase_service import supabase_service
from uuid import UUID

logger = structlog.get_logger()

router = APIRouter()


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Get the authenticated user's profile data",
)
async def get_my_profile(user: dict = Depends(get_current_user)) -> JSONResponse:
    """
    Get current authenticated user's profile.

    This endpoint demonstrates how to use the authentication middleware.
    The `user` parameter is automatically injected by FastAPI's Depends()
    using the get_current_user dependency.

    Args:
        user: Current authenticated user (injected by dependency)

    Returns:
        User profile data including full_name, onboarding status, etc.
    """
    try:
        user_id = UUID(user["id"])
        profile = await supabase_service.get_profile(user_id)

        if not profile:
            logger.error("profile_not_found", user_id=str(user_id))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        logger.info("profile_retrieved", user_id=str(user_id))

        return JSONResponse(content={
            "id": user["id"],
            "email": user["email"],
            "full_name": profile.get("full_name"),
            "onboarding_completed": profile.get("onboarding_completed", False),
            "created_at": profile.get("created_at"),
            "updated_at": profile.get("updated_at"),
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error("profile_retrieval_error", user_id=user["id"], error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile",
        )


@router.patch(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Update the authenticated user's profile data",
)
async def update_my_profile(
    full_name: str = None,
    user: dict = Depends(get_current_user)
) -> JSONResponse:
    """
    Update current authenticated user's profile.

    Args:
        full_name: New full name (optional)
        user: Current authenticated user (injected by dependency)

    Returns:
        Updated user profile data
    """
    try:
        user_id = UUID(user["id"])

        # Build update data
        update_data = {}
        if full_name is not None:
            update_data["full_name"] = full_name

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        # Update profile
        updated_profile = await supabase_service.update_profile(user_id, update_data)

        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        logger.info("profile_updated", user_id=str(user_id), fields=list(update_data.keys()))

        return JSONResponse(content={
            "id": user["id"],
            "email": user["email"],
            "full_name": updated_profile.get("full_name"),
            "onboarding_completed": updated_profile.get("onboarding_completed", False),
            "updated_at": updated_profile.get("updated_at"),
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error("profile_update_error", user_id=user["id"], error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )
