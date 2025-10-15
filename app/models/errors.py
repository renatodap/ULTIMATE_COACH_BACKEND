"""
Nutrition Error Codes System

Provides structured error codes for i18n support and consistent error handling.
Error codes follow the pattern: NUTRITION_XXX where XXX is a 3-digit number.

Error code ranges:
- 001-099: Search errors
- 101-199: Food errors
- 201-299: Meal errors
- 301-399: Custom food errors
- 401-499: Validation errors
"""

from typing import Optional, Dict, Any


class NutritionError(Exception):
    """
    Base exception for all nutrition-related errors.

    Includes error code for i18n translation and structured details
    for debugging and user feedback.
    """

    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict for API responses."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


# =====================================================
# Search Errors (001-099)
# =====================================================

class SearchQueryTooShortError(NutritionError):
    """NUTRITION_001: Search query must be at least 2 characters."""

    def __init__(self, query: str, min_length: int = 2):
        super().__init__(
            code="NUTRITION_001",
            message=f"Search query must be at least {min_length} characters (got: {len(query)})",
            details={"query": query, "min_length": min_length, "actual_length": len(query)},
            status_code=400,
        )


class SearchFailedError(NutritionError):
    """NUTRITION_002: Search operation failed."""

    def __init__(self, query: str, original_error: Optional[str] = None):
        super().__init__(
            code="NUTRITION_002",
            message=f"Failed to search foods for query: {query}",
            details={"query": query, "original_error": original_error},
            status_code=500,
        )


# =====================================================
# Food Errors (101-199)
# =====================================================

class FoodNotFoundError(NutritionError):
    """NUTRITION_101: Food not found or user doesn't have access."""

    def __init__(self, food_id: str):
        super().__init__(
            code="NUTRITION_101",
            message=f"Food {food_id} not found or inaccessible",
            details={"food_id": food_id},
            status_code=404,
        )


class FoodAccessDeniedError(NutritionError):
    """NUTRITION_102: User doesn't have permission to access this food."""

    def __init__(self, food_id: str, user_id: str):
        super().__init__(
            code="NUTRITION_102",
            message=f"Access denied to food {food_id}",
            details={"food_id": food_id, "user_id": user_id},
            status_code=403,
        )


class InvalidServingError(NutritionError):
    """NUTRITION_103: Serving size not found or invalid."""

    def __init__(self, serving_id: str, food_id: Optional[str] = None):
        super().__init__(
            code="NUTRITION_103",
            message=f"Serving {serving_id} not found" + (f" for food {food_id}" if food_id else ""),
            details={"serving_id": serving_id, "food_id": food_id},
            status_code=400,
        )


class ServingMismatchError(NutritionError):
    """NUTRITION_104: Serving does not belong to the specified food."""

    def __init__(self, serving_id: str, food_id: str, actual_food_id: str):
        super().__init__(
            code="NUTRITION_104",
            message=f"Serving {serving_id} does not belong to food {food_id}",
            details={
                "serving_id": serving_id,
                "expected_food_id": food_id,
                "actual_food_id": actual_food_id,
            },
            status_code=400,
        )


# =====================================================
# Meal Errors (201-299)
# =====================================================

class MealNotFoundError(NutritionError):
    """NUTRITION_201: Meal not found."""

    def __init__(self, meal_id: str):
        super().__init__(
            code="NUTRITION_201",
            message=f"Meal {meal_id} not found",
            details={"meal_id": meal_id},
            status_code=404,
        )


class MealEmptyError(NutritionError):
    """NUTRITION_202: Meal must have at least one item."""

    def __init__(self):
        super().__init__(
            code="NUTRITION_202",
            message="Meal must have at least one food item",
            details={"min_items": 1},
            status_code=400,
        )


class MealItemInvalidError(NutritionError):
    """NUTRITION_203: Invalid meal item data."""

    def __init__(self, item_index: int, reason: str):
        super().__init__(
            code="NUTRITION_203",
            message=f"Invalid meal item at index {item_index}: {reason}",
            details={"item_index": item_index, "reason": reason},
            status_code=400,
        )


class NutritionCalculationError(NutritionError):
    """NUTRITION_204: Failed to calculate nutrition totals."""

    def __init__(self, meal_id: Optional[str] = None, original_error: Optional[str] = None):
        super().__init__(
            code="NUTRITION_204",
            message="Failed to calculate nutrition totals",
            details={"meal_id": meal_id, "original_error": original_error},
            status_code=500,
        )


class MealCreationFailedError(NutritionError):
    """NUTRITION_205: Failed to create meal in database."""

    def __init__(self, reason: Optional[str] = None):
        super().__init__(
            code="NUTRITION_205",
            message=f"Failed to create meal" + (f": {reason}" if reason else ""),
            details={"reason": reason},
            status_code=500,
        )


# =====================================================
# Custom Food Errors (301-399)
# =====================================================

class InvalidGramsPerServingError(NutritionError):
    """NUTRITION_301: grams_per_serving must be positive."""

    def __init__(self, grams_per_serving: float):
        super().__init__(
            code="NUTRITION_301",
            message=f"grams_per_serving must be positive (got: {grams_per_serving})",
            details={"grams_per_serving": grams_per_serving},
            status_code=400,
        )


class DuplicateCustomFoodError(NutritionError):
    """NUTRITION_302: Custom food with this name already exists for user."""

    def __init__(self, food_name: str, user_id: str):
        super().__init__(
            code="NUTRITION_302",
            message=f"Custom food '{food_name}' already exists",
            details={"food_name": food_name, "user_id": user_id},
            status_code=409,
        )


class CustomFoodCreationFailedError(NutritionError):
    """NUTRITION_303: Failed to create custom food."""

    def __init__(self, food_name: str, reason: Optional[str] = None):
        super().__init__(
            code="NUTRITION_303",
            message=f"Failed to create custom food '{food_name}'" + (f": {reason}" if reason else ""),
            details={"food_name": food_name, "reason": reason},
            status_code=500,
        )


# =====================================================
# Validation Errors (401-499)
# =====================================================

class InvalidQuantityError(NutritionError):
    """NUTRITION_401: Quantity must be positive."""

    def __init__(self, quantity: float, field_name: str = "quantity"):
        super().__init__(
            code="NUTRITION_401",
            message=f"{field_name} must be positive (got: {quantity})",
            details={"field": field_name, "value": quantity},
            status_code=400,
        )


class InvalidDateFormatError(NutritionError):
    """NUTRITION_402: Date format must be YYYY-MM-DD."""

    def __init__(self, date_string: str):
        super().__init__(
            code="NUTRITION_402",
            message=f"Invalid date format: {date_string}. Expected: YYYY-MM-DD",
            details={"date": date_string, "expected_format": "YYYY-MM-DD"},
            status_code=400,
        )


class InvalidMealTypeError(NutritionError):
    """NUTRITION_403: Invalid meal type."""

    def __init__(self, meal_type: str, valid_types: list):
        super().__init__(
            code="NUTRITION_403",
            message=f"Invalid meal_type: {meal_type}. Must be one of: {', '.join(valid_types)}",
            details={"meal_type": meal_type, "valid_types": valid_types},
            status_code=400,
        )
