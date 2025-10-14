"""
Activities API endpoints.

Handles activity tracking, daily summaries, and CRUD operations.
"""

import structlog
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from uuid import UUID
from datetime import date

from app.models.activities import (
    CreateActivityRequest,
    UpdateActivityRequest,
    Activity,
    DailySummary,
    ActivityListResponse,
    SuccessResponse
)
from app.services.activity_service import activity_service
from app.api.dependencies import get_current_user

logger = structlog.get_logger()

router = APIRouter()


@router.get(
    "/activities",
    response_model=ActivityListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's activities",
    description="Retrieve activities for authenticated user with optional date filtering"
)
async def get_activities(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(20, ge=1, le=100, description="Max activities to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get activities for the authenticated user.

    - **start_date**: Filter activities after this date (ISO format)
    - **end_date**: Filter activities before this date (ISO format)
    - **limit**: Maximum number of activities to return (1-100)
    - **offset**: Number of activities to skip (for pagination)

    Returns activities sorted by start_time descending (most recent first).
    """
    try:
        # Parse dates if provided
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None

        logger.info(
            "fetching_activities",
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        activities = await activity_service.get_user_activities(
            user_id=UUID(current_user["id"]),
            start_date=start_date_obj,
            end_date=end_date_obj,
            limit=limit,
            offset=offset
        )

        logger.info(
            "activities_fetched",
            user_id=current_user["id"],
            count=len(activities)
        )

        return ActivityListResponse(
            activities=[Activity(**activity) for activity in activities],
            total=len(activities),
            limit=limit,
            offset=offset
        )

    except ValueError as e:
        logger.warning(
            "invalid_date_format",
            user_id=current_user["id"],
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "fetch_activities_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch activities"
        )


@router.get(
    "/activities/summary",
    response_model=DailySummary,
    status_code=status.HTTP_200_OK,
    summary="Get daily activity summary",
    description="Get aggregated statistics for a specific day"
)
async def get_daily_summary(
    target_date: Optional[str] = Query(None, description="Target date (YYYY-MM-DD), defaults to today"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get daily activity summary with aggregated statistics.

    - **target_date**: Date to summarize (defaults to today)

    Returns:
    - total_calories_burned
    - total_duration_minutes
    - average_intensity (METs)
    - activity_count
    - daily_goal_calories
    - goal_percentage
    """
    try:
        # Parse date or use today
        date_obj = date.fromisoformat(target_date) if target_date else date.today()

        logger.info(
            "fetching_daily_summary",
            user_id=current_user["id"],
            date=str(date_obj)
        )

        summary = await activity_service.get_daily_summary(
            user_id=UUID(current_user["id"]),
            target_date=date_obj
        )

        logger.info(
            "daily_summary_fetched",
            user_id=current_user["id"],
            date=str(date_obj),
            total_calories=summary["total_calories_burned"]
        )

        return DailySummary(**summary)

    except ValueError as e:
        logger.warning(
            "invalid_date_format",
            user_id=current_user["id"],
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "fetch_summary_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch daily summary"
        )


@router.get(
    "/activities/{activity_id}",
    response_model=Activity,
    status_code=status.HTTP_200_OK,
    summary="Get activity by ID",
    description="Retrieve a single activity with full details"
)
async def get_activity(
    activity_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a single activity by ID.

    Verifies that the activity belongs to the authenticated user.
    """
    try:
        logger.info(
            "fetching_activity",
            activity_id=str(activity_id),
            user_id=current_user["id"]
        )

        activity = await activity_service.get_activity(
            activity_id=activity_id,
            user_id=UUID(current_user["id"])
        )

        logger.info(
            "activity_fetched",
            activity_id=str(activity_id),
            user_id=current_user["id"]
        )

        return Activity(**activity)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "fetch_activity_error",
            activity_id=str(activity_id),
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch activity"
        )


@router.post(
    "/activities",
    response_model=Activity,
    status_code=status.HTTP_201_CREATED,
    summary="Create new activity",
    description="Log a new activity with metrics"
)
async def create_activity(
    request: CreateActivityRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new activity.

    Required fields:
    - **category**: Activity category (cardio_steady_state, strength_training, etc.)
    - **activity_name**: Custom name for the activity
    - **start_time**: When the activity started (ISO 8601)
    - One of: **duration_minutes** OR **end_time** (service will calculate duration if end_time is provided)

    Optional fields:
    - **end_time**: When the activity ended (required if duration_minutes not provided)
    - **duration_minutes**: Duration in minutes (required if end_time not provided)
    - **calories_burned**: If omitted, auto-calculated based on category, duration, and user weight
    - **intensity_mets**: If omitted, auto-looked-up/estimated for the category
    - **metrics**: Activity-specific metrics (distance, HR, exercises, etc.)
    - **notes**: User notes
    """
    try:
        logger.info(
            "creating_activity",
            user_id=current_user["id"],
            category=request.category,
            activity_name=request.activity_name
        )

        activity = await activity_service.create_activity(
            user_id=UUID(current_user["id"]),
            category=request.category,
            activity_name=request.activity_name,
            start_time=request.start_time,
            end_time=request.end_time,
            duration_minutes=request.duration_minutes,
            calories_burned=request.calories_burned,
            intensity_mets=request.intensity_mets,
            metrics=request.metrics,
            notes=request.notes
        )

        logger.info(
            "activity_created",
            activity_id=activity["id"],
            user_id=current_user["id"]
        )

        return Activity(**activity)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "create_activity_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create activity"
        )


@router.patch(
    "/activities/{activity_id}",
    response_model=Activity,
    status_code=status.HTTP_200_OK,
    summary="Update activity",
    description="Update an existing activity"
)
async def update_activity(
    activity_id: UUID,
    request: UpdateActivityRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing activity.

    All fields are optional - only provide the fields you want to update.

    Verifies that the activity belongs to the authenticated user.
    """
    try:
        # Build updates dict (exclude None values)
        updates = request.dict(exclude_unset=True)

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        logger.info(
            "updating_activity",
            activity_id=str(activity_id),
            user_id=current_user["id"],
            fields=list(updates.keys())
        )

        activity = await activity_service.update_activity(
            activity_id=activity_id,
            user_id=UUID(current_user["id"]),
            updates=updates
        )

        logger.info(
            "activity_updated",
            activity_id=str(activity_id),
            user_id=current_user["id"]
        )

        return Activity(**activity)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "update_activity_error",
            activity_id=str(activity_id),
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update activity"
        )


@router.delete(
    "/activities/{activity_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete activity",
    description="Delete an activity (soft delete)"
)
async def delete_activity(
    activity_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an activity (soft delete).

    The activity is marked as deleted but not removed from the database.
    Verifies that the activity belongs to the authenticated user.
    """
    try:
        logger.info(
            "deleting_activity",
            activity_id=str(activity_id),
            user_id=current_user["id"]
        )

        success = await activity_service.delete_activity(
            activity_id=activity_id,
            user_id=UUID(current_user["id"])
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete activity"
            )

        logger.info(
            "activity_deleted",
            activity_id=str(activity_id),
            user_id=current_user["id"]
        )

        return SuccessResponse(
            success=True,
            message="Activity deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "delete_activity_error",
            activity_id=str(activity_id),
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete activity"
        )
