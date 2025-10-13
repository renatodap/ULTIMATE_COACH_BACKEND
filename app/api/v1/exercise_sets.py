"""
Exercise Sets API endpoints.

Handles individual set tracking for strength training activities.
"""

import structlog
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from uuid import UUID

from app.models.exercise_sets import (
    CreateExerciseSetRequest,
    UpdateExerciseSetRequest,
    ExerciseSet,
    ExerciseSearchResult,
    PersonalRecord,
    ExerciseHistory,
    BulkCreateExerciseSetsRequest,
    ExerciseSetsResponse,
    SuccessResponse
)
from app.services.supabase_service import SupabaseService
from app.api.dependencies import get_current_user

logger = structlog.get_logger()

router = APIRouter()
db_service = SupabaseService()


@router.get(
    "/exercises/search",
    response_model=list[ExerciseSearchResult],
    status_code=status.HTTP_200_OK,
    summary="Search exercises",
    description="Search exercises by name with autocomplete"
)
async def search_exercises(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    current_user: dict = Depends(get_current_user)
):
    """
    Search exercises with full-text search and autocomplete.

    - **q**: Search query (partial match supported)
    - **category**: Optional category filter
    - **limit**: Maximum results to return

    Returns exercises sorted by relevance and popularity.
    """
    try:
        logger.info(
            "searching_exercises",
            user_id=current_user["id"],
            query=q,
            category=category
        )

        exercises = await db_service.search_exercises(
            query=q,
            category=category,
            limit=limit
        )

        logger.info(
            "exercises_found",
            user_id=current_user["id"],
            count=len(exercises)
        )

        return [ExerciseSearchResult(**ex) for ex in exercises]

    except Exception as e:
        logger.error(
            "search_exercises_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search exercises"
        )


@router.get(
    "/activities/{activity_id}/sets",
    response_model=ExerciseSetsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get exercise sets for activity",
    description="Get all exercise sets for a specific activity"
)
async def get_activity_sets(
    activity_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all exercise sets for an activity.

    Returns sets ordered by set_number with exercise details.
    """
    try:
        logger.info(
            "fetching_activity_sets",
            activity_id=str(activity_id),
            user_id=current_user["id"]
        )

        sets = await db_service.get_exercise_sets(
            activity_id=activity_id,
            user_id=UUID(current_user["id"])
        )

        logger.info(
            "activity_sets_fetched",
            activity_id=str(activity_id),
            count=len(sets)
        )

        return ExerciseSetsResponse(
            sets=[ExerciseSet(**s) for s in sets],
            total=len(sets)
        )

    except Exception as e:
        logger.error(
            "fetch_activity_sets_error",
            activity_id=str(activity_id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch exercise sets"
        )


@router.post(
    "/activities/{activity_id}/sets",
    response_model=ExerciseSetsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create exercise sets",
    description="Create multiple exercise sets for an activity"
)
async def create_activity_sets(
    activity_id: UUID,
    request: BulkCreateExerciseSetsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create multiple exercise sets for an activity.

    Allows bulk creation of sets for efficient strength workout logging.
    """
    try:
        # Validate activity_id matches request
        if activity_id != request.activity_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activity ID mismatch"
            )

        logger.info(
            "creating_exercise_sets",
            activity_id=str(activity_id),
            user_id=current_user["id"],
            count=len(request.sets)
        )

        # Prepare sets data
        sets_data = [
            {
                **set_data.dict(),
                "activity_id": str(activity_id),
                "user_id": current_user["id"]
            }
            for set_data in request.sets
        ]

        # Create sets
        created_sets = await db_service.create_exercise_sets(sets_data)

        logger.info(
            "exercise_sets_created",
            activity_id=str(activity_id),
            count=len(created_sets)
        )

        return ExerciseSetsResponse(
            sets=[ExerciseSet(**s) for s in created_sets],
            total=len(created_sets)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "create_exercise_sets_error",
            activity_id=str(activity_id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create exercise sets"
        )


@router.patch(
    "/sets/{set_id}",
    response_model=ExerciseSet,
    status_code=status.HTTP_200_OK,
    summary="Update exercise set",
    description="Update a specific exercise set"
)
async def update_set(
    set_id: UUID,
    request: UpdateExerciseSetRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update an exercise set.

    All fields are optional - only provide fields to update.
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
            "updating_exercise_set",
            set_id=str(set_id),
            user_id=current_user["id"],
            fields=list(updates.keys())
        )

        updated_set = await db_service.update_exercise_set(
            set_id=set_id,
            user_id=UUID(current_user["id"]),
            updates=updates
        )

        logger.info(
            "exercise_set_updated",
            set_id=str(set_id),
            user_id=current_user["id"]
        )

        return ExerciseSet(**updated_set)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "update_exercise_set_error",
            set_id=str(set_id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update exercise set"
        )


@router.delete(
    "/sets/{set_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete exercise set",
    description="Delete a specific exercise set"
)
async def delete_set(
    set_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an exercise set.

    Verifies ownership before deletion.
    """
    try:
        logger.info(
            "deleting_exercise_set",
            set_id=str(set_id),
            user_id=current_user["id"]
        )

        success = await db_service.delete_exercise_set(
            set_id=set_id,
            user_id=UUID(current_user["id"])
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete exercise set"
            )

        logger.info(
            "exercise_set_deleted",
            set_id=str(set_id),
            user_id=current_user["id"]
        )

        return SuccessResponse(
            success=True,
            message="Exercise set deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "delete_exercise_set_error",
            set_id=str(set_id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete exercise set"
        )


@router.get(
    "/exercises/history",
    response_model=list[ExerciseHistory],
    status_code=status.HTTP_200_OK,
    summary="Get exercise history",
    description="Get user's exercise history with performance tracking"
)
async def get_exercise_history(
    exercise_id: Optional[UUID] = Query(None, description="Filter by exercise"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get exercise history for the authenticated user.

    Useful for tracking progressive overload and performance trends.
    """
    try:
        logger.info(
            "fetching_exercise_history",
            user_id=current_user["id"],
            exercise_id=str(exercise_id) if exercise_id else None
        )

        history = await db_service.get_user_exercise_history(
            user_id=UUID(current_user["id"]),
            exercise_id=exercise_id,
            limit=limit
        )

        logger.info(
            "exercise_history_fetched",
            user_id=current_user["id"],
            count=len(history)
        )

        return [ExerciseHistory(**h) for h in history]

    except Exception as e:
        logger.error(
            "fetch_exercise_history_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch exercise history"
        )


@router.get(
    "/exercises/personal-records",
    response_model=list[PersonalRecord],
    status_code=status.HTTP_200_OK,
    summary="Get personal records",
    description="Get user's personal records (PRs) for exercises"
)
async def get_personal_records(
    exercise_id: Optional[UUID] = Query(None, description="Filter by exercise"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get personal records for the authenticated user.

    Returns max weight, estimated 1RM, and max volume per exercise.
    """
    try:
        logger.info(
            "fetching_personal_records",
            user_id=current_user["id"],
            exercise_id=str(exercise_id) if exercise_id else None
        )

        prs = await db_service.get_personal_records(
            user_id=UUID(current_user["id"]),
            exercise_id=exercise_id
        )

        logger.info(
            "personal_records_fetched",
            user_id=current_user["id"],
            count=len(prs)
        )

        return [PersonalRecord(**pr) for pr in prs]

    except Exception as e:
        logger.error(
            "fetch_personal_records_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch personal records"
        )
