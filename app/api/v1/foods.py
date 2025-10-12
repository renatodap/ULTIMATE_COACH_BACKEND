"""
Foods API endpoints.

Handles food search, retrieval, and custom food creation.
"""

import structlog
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from uuid import UUID

from app.models.nutrition import (
    Food,
    FoodServing,
    FoodSearchResponse,
    CreateCustomFoodRequest,
)
from app.services.nutrition_service import nutrition_service
from app.api.dependencies import get_current_user

logger = structlog.get_logger()

router = APIRouter()


@router.get(
    "/foods/search",
    response_model=FoodSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search foods",
    description="Search curated food database by name",
)
async def search_foods(
    q: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
) -> FoodSearchResponse:
    """
    Search for foods by name.

    Args:
        q: Search query (minimum 2 characters)
        limit: Maximum number of results (default 20, max 100)
        current_user: Authenticated user

    Returns:
        List of matching foods with nutrition info
    """
    try:
        # Validate query
        if len(q) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query must be at least 2 characters",
            )

        # Validate limit
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100",
            )

        foods = await nutrition_service.search_foods(
            query=q,
            limit=limit,
            user_id=current_user["id"],
        )

        logger.info(
            "foods_search_success",
            query=q,
            results_count=len(foods),
            user_id=current_user["id"],
        )

        return FoodSearchResponse(foods=foods, total=len(foods))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "foods_search_error",
            query=q,
            user_id=current_user["id"],
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search foods",
        )


@router.get(
    "/foods/{food_id}",
    response_model=Food,
    status_code=status.HTTP_200_OK,
    summary="Get food by ID",
    description="Get detailed food information including all serving sizes",
)
async def get_food(
    food_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> Food:
    """
    Get a single food by ID.

    Args:
        food_id: Food UUID
        current_user: Authenticated user

    Returns:
        Food with nutrition info and available serving sizes
    """
    try:
        food = await nutrition_service.get_food(
            food_id=food_id,
            user_id=current_user["id"],
        )

        if not food:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Food not found",
            )

        logger.info(
            "food_retrieved",
            food_id=str(food_id),
            user_id=current_user["id"],
        )

        return food

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "food_retrieval_error",
            food_id=str(food_id),
            user_id=current_user["id"],
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve food",
        )


@router.get(
    "/foods/{food_id}/servings",
    response_model=List[FoodServing],
    status_code=status.HTTP_200_OK,
    summary="Get food servings",
    description="Get all available serving sizes for a food",
)
async def get_food_servings(
    food_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> List[FoodServing]:
    """
    Get all serving sizes for a food.

    Args:
        food_id: Food UUID
        current_user: Authenticated user

    Returns:
        List of available serving sizes with gram conversions
    """
    try:
        servings = await nutrition_service.get_food_servings(
            food_id=food_id,
            user_id=current_user["id"],
        )

        logger.info(
            "food_servings_retrieved",
            food_id=str(food_id),
            servings_count=len(servings),
            user_id=current_user["id"],
        )

        return servings

    except Exception as e:
        logger.error(
            "food_servings_error",
            food_id=str(food_id),
            user_id=current_user["id"],
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve food servings",
        )


@router.post(
    "/foods/custom",
    response_model=Food,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom food",
    description="Create a custom food when user can't find it in database",
)
async def create_custom_food(
    request: CreateCustomFoodRequest,
    current_user: dict = Depends(get_current_user),
) -> Food:
    """
    Create a custom food.

    Allows users to add foods not in the main database.
    Custom foods are private to the user who created them.

    Args:
        request: Custom food data
        current_user: Authenticated user

    Returns:
        Created food with serving size
    """
    try:
        food = await nutrition_service.create_custom_food(
            user_id=current_user["id"],
            name=request.name,
            brand_name=request.brand_name,
            serving_size=request.serving_size,
            serving_unit=request.serving_unit,
            grams_per_serving=request.grams_per_serving,
            calories=request.calories,
            protein_g=request.protein_g,
            carbs_g=request.carbs_g,
            fat_g=request.fat_g,
            fiber_g=request.fiber_g,
        )

        logger.info(
            "custom_food_created",
            food_id=str(food.id),
            food_name=food.name,
            user_id=current_user["id"],
        )

        return food

    except ValueError as e:
        logger.warning(
            "custom_food_validation_error",
            user_id=current_user["id"],
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "custom_food_creation_error",
            user_id=current_user["id"],
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create custom food",
        )
