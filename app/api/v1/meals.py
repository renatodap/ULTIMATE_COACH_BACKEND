"""
Meals API endpoints.

Handles meal creation, retrieval, update, and deletion with automatic
nutrition calculation from meal items.
"""

import structlog
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from uuid import UUID
from datetime import datetime, date

from app.models.nutrition import (
    Meal,
    CreateMealRequest,
    UpdateMealRequest,
    MealListResponse,
    NutritionStats,
)
from app.services.nutrition_service import nutrition_service
from app.services.meal_matching_service import meal_matching_service
from app.api.dependencies import get_current_user

logger = structlog.get_logger()

router = APIRouter()


@router.post(
    "/meals",
    response_model=Meal,
    status_code=status.HTTP_201_CREATED,
    summary="Create meal",
    description="Create a new meal with food items and automatic nutrition calculation",
)
async def create_meal(
    request: CreateMealRequest,
    current_user: dict = Depends(get_current_user),
) -> Meal:
    """
    Create a meal with items.

    Automatically calculates nutrition totals from items.
    Each item references a food and serving size.

    Args:
        request: Meal data with items
        current_user: Authenticated user

    Returns:
        Created meal with calculated nutrition totals
    """
    try:
        meal = await nutrition_service.create_meal(
            user_id=current_user["id"],
            name=request.name,
            meal_type=request.meal_type,
            logged_at=request.logged_at,
            notes=request.notes,
            items=request.items,
            source=request.source,
            ai_confidence=request.ai_confidence,
        )

        logger.info(
            "meal_created",
            meal_id=str(meal.id),
            meal_type=meal.meal_type,
            items_count=len(meal.items),
            calories=float(meal.total_calories),
            user_id=current_user["id"],
        )

        return meal

    except ValueError as e:
        logger.warning(
            "meal_creation_validation_error",
            user_id=current_user["id"],
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "meal_creation_error",
            user_id=current_user["id"],
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create meal",
        )


@router.get(
    "/meals",
    response_model=MealListResponse,
    status_code=status.HTTP_200_OK,
    summary="List meals",
    description="Get user's meals with optional date filtering",
)
async def list_meals(
    start_date: Optional[str] = Query(None, description="ISO date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="ISO date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
) -> MealListResponse:
    """
    Get user's meals.

    Supports date filtering and pagination.

    Args:
        start_date: Start date (inclusive)
        end_date: End date (exclusive)
        limit: Maximum number of meals
        offset: Pagination offset
        current_user: Authenticated user

    Returns:
        List of meals with items
    """
    try:
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        # DEBUG: Log query parameters
        logger.info(
            "meals_query_start",
            user_id=current_user["id"],
            start_date_raw=start_date,
            end_date_raw=end_date,
            start_dt_parsed=start_dt.isoformat() if start_dt else None,
            end_dt_parsed=end_dt.isoformat() if end_dt else None,
            limit=limit,
            offset=offset
        )

        meals = await nutrition_service.get_user_meals(
            user_id=current_user["id"],
            start_date=start_dt,
            end_date=end_dt,
            limit=limit,
            offset=offset,
        )

        # DEBUG: Log sample meal data
        logger.info(
            "meals_retrieved",
            user_id=current_user["id"],
            count=len(meals),
            start_date=start_date,
            end_date=end_date,
            sample_meals=[{
                "id": str(m.id),
                "meal_type": m.meal_type,
                "logged_at": m.logged_at.isoformat() if m.logged_at else None,
                "calories": float(m.total_calories)
            } for m in meals[:3]]  # First 3 meals for debugging
        )

        return MealListResponse(meals=meals, total=len(meals))

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {e}",
        )
    except Exception as e:
        logger.error(
            "meals_list_error",
            user_id=current_user["id"],
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve meals",
        )


@router.get(
    "/meals/{meal_id}",
    response_model=Meal,
    status_code=status.HTTP_200_OK,
    summary="Get meal",
    description="Get a single meal by ID with all items",
)
async def get_meal(
    meal_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> Meal:
    """
    Get a meal by ID.

    Args:
        meal_id: Meal UUID
        current_user: Authenticated user

    Returns:
        Meal with items
    """
    try:
        meal = await nutrition_service.get_meal(
            meal_id=meal_id,
            user_id=current_user["id"],
        )

        if not meal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal not found",
            )

        logger.info(
            "meal_retrieved",
            meal_id=str(meal_id),
            user_id=current_user["id"],
        )

        return meal

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "meal_retrieval_error",
            meal_id=str(meal_id),
            user_id=current_user["id"],
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve meal",
        )


@router.delete(
    "/meals/{meal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete meal",
    description="Delete a meal and all its items",
)
async def delete_meal(
    meal_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> None:
    """
    Delete a meal.

    Deletes the meal and all associated meal_items via CASCADE.

    Args:
        meal_id: Meal UUID
        current_user: Authenticated user
    """
    try:
        deleted = await nutrition_service.delete_meal(
            meal_id=meal_id,
            user_id=current_user["id"],
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal not found",
            )

        logger.info(
            "meal_deleted",
            meal_id=str(meal_id),
            user_id=current_user["id"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "meal_deletion_error",
            meal_id=str(meal_id),
            user_id=current_user["id"],
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete meal",
        )


@router.get(
    "/nutrition/stats",
    response_model=NutritionStats,
    status_code=status.HTTP_200_OK,
    summary="Get nutrition stats",
    description="Get daily nutrition summary for a specific date",
)
async def get_nutrition_stats(
    date: str = Query(..., description="ISO date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user),
) -> NutritionStats:
    """
    Get daily nutrition stats.

    Shows total calories, macros consumed vs goals.

    Args:
        date: ISO date (YYYY-MM-DD)
        current_user: Authenticated user

    Returns:
        Nutrition stats for the date
    """
    try:
        # Validate date format
        datetime.fromisoformat(date)

        stats = await nutrition_service.get_nutrition_stats(
            user_id=current_user["id"],
            date=date,
        )

        logger.info(
            "nutrition_stats_retrieved",
            user_id=current_user["id"],
            date=date,
            calories=float(stats.calories_consumed),
        )

        return stats

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )
    except Exception as e:
        logger.error(
            "nutrition_stats_error",
            user_id=current_user["id"],
            date=date,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve nutrition stats",
        )


@router.post(
    "/meals/{meal_id}/match",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Match meal to planned meal",
    description="Manually trigger matching for an existing meal"
)
async def match_meal(
    meal_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Manually match a logged meal to a planned meal.

    This endpoint:
    1. Finds planned meals for the meal's day and type
    2. Calculates similarity scores based on macros
    3. Links to best match (if score > threshold)
    4. Creates adherence_record with macro variance

    Use cases:
    - Retry matching if it failed during creation
    - Re-match after updating meal details
    - Manual nutrition adherence tracking
    """
    try:
        logger.info(
            "manual_meal_matching",
            meal_id=str(meal_id),
            user_id=current_user["id"]
        )

        adherence = await meal_matching_service.match_meal_to_plan(
            meal_log_id=str(meal_id),
            user_id=current_user["id"]
        )

        if not adherence:
            return {
                "matched": False,
                "message": "No matching planned meal found"
            }

        logger.info(
            "meal_matched",
            meal_id=str(meal_id),
            adherence_id=adherence["id"],
            status=adherence["status"]
        )

        return {
            "matched": True,
            "adherence_record": adherence,
            "message": f"Meal matched with status: {adherence['status']}"
        }

    except Exception as e:
        logger.error(
            "match_meal_error",
            meal_id=str(meal_id),
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to match meal"
        )


@router.post(
    "/meals/check-skipped",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Check for skipped meals",
    description="Find planned meals that were not logged"
)
async def check_skipped_meals(
    target_date: Optional[str] = Query(None, description="Date to check (YYYY-MM-DD), defaults to today"),
    current_user: dict = Depends(get_current_user)
):
    """
    Check for planned meals that were not logged on a given day.

    Creates adherence records with status="skipped" for meals that have no matching log.

    Returns:
    - List of skipped meals
    - Count of skipped meals
    """
    try:
        # Parse date or use today
        date_obj = date.fromisoformat(target_date) if target_date else date.today()

        logger.info(
            "checking_skipped_meals",
            user_id=current_user["id"],
            date=str(date_obj)
        )

        skipped = await meal_matching_service.match_skipped_meals(
            user_id=current_user["id"],
            target_date=date_obj
        )

        logger.info(
            "skipped_meals_checked",
            user_id=current_user["id"],
            date=str(date_obj),
            skipped_count=len(skipped)
        )

        return {
            "date": str(date_obj),
            "skipped_count": len(skipped),
            "skipped_meals": skipped
        }

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
            "check_skipped_meals_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check skipped meals"
        )


@router.get(
    "/nutrition/adherence",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get daily macro adherence",
    description="Calculate macro adherence for a specific day"
)
async def get_macro_adherence(
    target_date: Optional[str] = Query(None, description="Date to check (YYYY-MM-DD), defaults to today"),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate daily macro adherence.

    Compares total logged macros vs total planned macros for the day.

    Returns:
    - Actual vs target for calories, protein, carbs, fat
    - Variance (actual - target)
    - Variance percentage
    - Adherence percentage (100% = exact match)
    """
    try:
        # Parse date or use today
        date_obj = date.fromisoformat(target_date) if target_date else date.today()

        logger.info(
            "calculating_macro_adherence",
            user_id=current_user["id"],
            date=str(date_obj)
        )

        adherence = await meal_matching_service.calculate_daily_macro_adherence(
            user_id=current_user["id"],
            target_date=date_obj
        )

        logger.info(
            "macro_adherence_calculated",
            user_id=current_user["id"],
            date=str(date_obj)
        )

        return {
            "date": str(date_obj),
            "macros": adherence
        }

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
            "macro_adherence_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate macro adherence"
        )
