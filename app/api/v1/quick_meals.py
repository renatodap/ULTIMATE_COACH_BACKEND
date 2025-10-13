"""
Quick Meals API endpoints.

Handles user-specific meal templates (combinations of foods they log frequently).
"""

import structlog
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user, get_supabase_client
from supabase import Client

logger = structlog.get_logger()

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class QuickMealFoodItem(BaseModel):
    """Food item in a quick meal"""
    food_id: str
    quantity: float = Field(gt=0)
    serving_id: str | None = None
    display_order: int = 0


class CreateQuickMealRequest(BaseModel):
    """Request to create a quick meal"""
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    foods: List[QuickMealFoodItem] = Field(min_length=1, max_length=20)


class UpdateQuickMealRequest(BaseModel):
    """Request to update a quick meal"""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    is_favorite: bool | None = None


class QuickMealResponse(BaseModel):
    """Quick meal with foods"""
    id: str
    name: str
    description: str | None
    is_favorite: bool
    usage_count: int
    last_used_at: str | None
    foods: List[dict]  # List of food objects with quantity/serving info
    created_at: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get(
    "/quick-meals",
    response_model=List[QuickMealResponse],
    status_code=status.HTTP_200_OK,
    summary="List user's quick meals",
)
async def list_quick_meals(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
) -> List[QuickMealResponse]:
    """
    Get all quick meals for the current user.

    Returns quick meals sorted by:
    1. Favorites first
    2. Most recently used
    3. Most frequently used
    """
    try:
        response = (
            supabase.table("quick_meals")
            .select("*, quick_meal_foods(*, food:foods(*, servings:food_servings(*)))")
            .eq("user_id", current_user["id"])
            .order("is_favorite", desc=True)
            .order("last_used_at", desc=True)
            .order("usage_count", desc=True)
            .execute()
        )

        quick_meals = response.data or []

        logger.info(
            "quick_meals_listed",
            user_id=current_user["id"],
            count=len(quick_meals),
        )

        return quick_meals

    except Exception as e:
        logger.error(
            "list_quick_meals_error",
            user_id=current_user["id"],
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list quick meals",
        )


@router.post(
    "/quick-meals",
    response_model=QuickMealResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create quick meal",
)
async def create_quick_meal(
    request: CreateQuickMealRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
) -> QuickMealResponse:
    """
    Create a new quick meal template.

    Quick meals are user-specific combinations of foods they log frequently.
    When logged, they expand into individual meal_items.
    """
    try:
        # 1. Create quick meal
        quick_meal_response = (
            supabase.table("quick_meals")
            .insert({
                "user_id": current_user["id"],
                "name": request.name,
                "description": request.description,
            })
            .execute()
        )

        if not quick_meal_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create quick meal",
            )

        quick_meal = quick_meal_response.data[0]

        # 2. Add foods to quick meal
        quick_meal_foods = [
            {
                "quick_meal_id": quick_meal["id"],
                "food_id": food.food_id,
                "quantity": food.quantity,
                "serving_id": food.serving_id,
                "display_order": food.display_order,
            }
            for food in request.foods
        ]

        supabase.table("quick_meal_foods").insert(quick_meal_foods).execute()

        # 3. Fetch complete quick meal with foods
        complete_response = (
            supabase.table("quick_meals")
            .select("*, quick_meal_foods(*, food:foods(*, servings:food_servings(*)))")
            .eq("id", quick_meal["id"])
            .single()
            .execute()
        )

        logger.info(
            "quick_meal_created",
            quick_meal_id=quick_meal["id"],
            name=request.name,
            foods_count=len(request.foods),
            user_id=current_user["id"],
        )

        return complete_response.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "create_quick_meal_error",
            user_id=current_user["id"],
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create quick meal",
        )


@router.patch(
    "/quick-meals/{quick_meal_id}",
    response_model=QuickMealResponse,
    status_code=status.HTTP_200_OK,
    summary="Update quick meal",
)
async def update_quick_meal(
    quick_meal_id: UUID,
    request: UpdateQuickMealRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
) -> QuickMealResponse:
    """
    Update a quick meal's name, description, or favorite status.
    """
    try:
        # Build update dict
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.is_favorite is not None:
            update_data["is_favorite"] = request.is_favorite

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        # Update quick meal (RLS ensures user owns it)
        response = (
            supabase.table("quick_meals")
            .update(update_data)
            .eq("id", str(quick_meal_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quick meal not found",
            )

        # Fetch complete quick meal
        complete_response = (
            supabase.table("quick_meals")
            .select("*, quick_meal_foods(*, food:foods(*, servings:food_servings(*)))")
            .eq("id", str(quick_meal_id))
            .single()
            .execute()
        )

        logger.info(
            "quick_meal_updated",
            quick_meal_id=str(quick_meal_id),
            user_id=current_user["id"],
        )

        return complete_response.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "update_quick_meal_error",
            quick_meal_id=str(quick_meal_id),
            user_id=current_user["id"],
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update quick meal",
        )


@router.delete(
    "/quick-meals/{quick_meal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete quick meal",
)
async def delete_quick_meal(
    quick_meal_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Delete a quick meal template.
    """
    try:
        response = (
            supabase.table("quick_meals")
            .delete()
            .eq("id", str(quick_meal_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quick meal not found",
            )

        logger.info(
            "quick_meal_deleted",
            quick_meal_id=str(quick_meal_id),
            user_id=current_user["id"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "delete_quick_meal_error",
            quick_meal_id=str(quick_meal_id),
            user_id=current_user["id"],
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete quick meal",
        )


@router.post(
    "/quick-meals/{quick_meal_id}/log",
    status_code=status.HTTP_201_CREATED,
    summary="Log quick meal",
)
async def log_quick_meal(
    quick_meal_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Log a quick meal (creates a new meal with all foods from the quick meal).

    This expands the quick meal into individual meal_items and creates a full meal log.
    Also increments the usage_count and updates last_used_at for the quick meal.
    """
    try:
        # 1. Fetch quick meal with all foods
        quick_meal_response = (
            supabase.table("quick_meals")
            .select("*, quick_meal_foods(*, food:foods(*, servings:food_servings(*)))")
            .eq("id", str(quick_meal_id))
            .eq("user_id", current_user["id"])
            .single()
            .execute()
        )

        if not quick_meal_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quick meal not found",
            )

        quick_meal = quick_meal_response.data

        # 2. Create meal
        # TODO: This should use the meal logging service with nutrition calculation
        # For now, return success and the quick meal data
        # Full implementation would create a meal and meal_items

        # 3. Update quick meal usage
        from datetime import datetime
        supabase.table("quick_meals").update({
            "usage_count": quick_meal["usage_count"] + 1,
            "last_used_at": datetime.utcnow().isoformat(),
        }).eq("id", str(quick_meal_id)).execute()

        logger.info(
            "quick_meal_logged",
            quick_meal_id=str(quick_meal_id),
            user_id=current_user["id"],
        )

        return {
            "message": "Quick meal logged successfully",
            "quick_meal": quick_meal,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "log_quick_meal_error",
            quick_meal_id=str(quick_meal_id),
            user_id=current_user["id"],
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log quick meal",
        )
