"""
Nutrition models for foods, food servings, meals, and meal items.

These models align with the database schema in migrations/001_IMPROVED_schema.sql.
Key design: Foods have nutrition per 100g, food_servings provide conversions,
meal_items track both user input and calculated values.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_serializer


# =====================================================
# Food Models
# =====================================================

class FoodServing(BaseModel):
    """
    A specific serving size for a food with gram conversion.

    Examples:
    - Whey protein: 1 scoop = 30g
    - Chicken breast: 1 medium breast = 174g
    - Rice: 1 cup cooked = 158g
    """
    id: UUID
    food_id: UUID
    serving_size: Decimal = Field(gt=0, description="Amount (e.g., 1, 2, 0.5)")
    serving_unit: str = Field(description="Unit name (e.g., 'scoop', 'cup', 'oz')")
    serving_label: Optional[str] = Field(None, description="Optional label (e.g., 'medium breast')")
    grams_per_serving: Decimal = Field(gt=0, description="Grams for this serving")
    is_default: bool = Field(default=False, description="Default serving for UI")
    display_order: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('serving_size', 'grams_per_serving')
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization."""
        return float(value)


class Food(BaseModel):
    """
    Base food with nutrition per 100g and available serving sizes.

    Nutrition is stored per 100g (canonical unit), then scaled based
    on servings when logging meals.
    """
    id: UUID
    name: str
    brand_name: Optional[str] = None

    # Nutrition per 100g (CANONICAL BASE)
    calories_per_100g: Decimal = Field(ge=0)
    protein_g_per_100g: Decimal = Field(ge=0)
    carbs_g_per_100g: Decimal = Field(ge=0)
    fat_g_per_100g: Decimal = Field(ge=0)

    # Optional micros per 100g
    fiber_g_per_100g: Optional[Decimal] = Field(None, ge=0)
    sugar_g_per_100g: Optional[Decimal] = Field(None, ge=0)
    sodium_mg_per_100g: Optional[Decimal] = Field(None, ge=0)

    # Metadata
    food_type: Optional[str] = Field(None, description="ingredient, dish, branded, restaurant")
    dietary_flags: Optional[List[str]] = None
    is_public: bool = True
    verified: bool = False
    usage_count: int = 0

    # Available serving sizes
    servings: List[FoodServing] = Field(default_factory=list)

    # Ownership
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer(
        'calories_per_100g', 'protein_g_per_100g', 'carbs_g_per_100g', 'fat_g_per_100g',
        'fiber_g_per_100g', 'sugar_g_per_100g', 'sodium_mg_per_100g'
    )
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[float]:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None


class FoodSearchResponse(BaseModel):
    """Response for food search endpoint."""
    foods: List[Food]
    total: int


class CreateCustomFoodRequest(BaseModel):
    """
    Request to create a custom food with a single serving size.

    User provides nutrition for their specific serving, system converts
    to per-100g for storage.

    IMPORTANT: grams_per_serving is NOW REQUIRED to avoid estimation errors.
    """
    name: str = Field(min_length=1, max_length=200)
    brand_name: Optional[str] = Field(None, max_length=200)

    # Serving definition
    serving_size: Decimal = Field(gt=0, description="Amount (e.g., 1)")
    serving_unit: str = Field(min_length=1, max_length=50, description="Unit (e.g., 'serving', 'piece')")
    grams_per_serving: Decimal = Field(gt=0, description="Grams for this serving (e.g., 25g for 1 cookie)")

    # Nutrition for this serving (will be converted to per-100g)
    calories: Decimal = Field(ge=0)
    protein_g: Decimal = Field(ge=0)
    carbs_g: Decimal = Field(ge=0)
    fat_g: Decimal = Field(ge=0)
    fiber_g: Optional[Decimal] = Field(None, ge=0)


# =====================================================
# Meal Models
# =====================================================

class MealItemBase(BaseModel):
    """Base meal item data for creation."""
    food_id: UUID
    quantity: Decimal = Field(gt=0, description="Amount of servings (e.g., 2)")
    serving_id: UUID = Field(description="Which serving size to use")


class MealItem(BaseModel):
    """
    A single food entry in a meal.

    Stores both what user logged (quantity + serving) and calculated
    nutrition values in grams.
    """
    id: UUID
    meal_id: UUID
    food_id: UUID

    # What user logged
    quantity: Decimal = Field(gt=0)
    serving_id: UUID

    # Calculated at log time (stored for history)
    grams: Decimal = Field(gt=0)
    calories: Decimal = Field(ge=0)
    protein_g: Decimal = Field(ge=0)
    carbs_g: Decimal = Field(ge=0)
    fat_g: Decimal = Field(ge=0)

    # Display info (denormalized for UI)
    display_unit: str
    display_label: Optional[str] = None

    display_order: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('quantity', 'grams', 'calories', 'protein_g', 'carbs_g', 'fat_g')
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization."""
        return float(value)


class CreateMealRequest(BaseModel):
    """Request to create a new meal with items."""
    name: Optional[str] = Field(None, max_length=200)
    meal_type: str = Field(description="breakfast, lunch, dinner, snack, other")
    logged_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)
    items: List[MealItemBase] = Field(min_length=1, description="At least one food item")

    # AI tracking (optional)
    source: str = Field(default="manual", description="manual, ai_text, ai_voice, ai_photo, coach_chat")
    ai_confidence: Optional[Decimal] = Field(None, ge=0, le=1)


class UpdateMealRequest(BaseModel):
    """Request to update meal metadata (not items)."""
    name: Optional[str] = Field(None, max_length=200)
    meal_type: Optional[str] = None
    logged_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)


class Meal(BaseModel):
    """
    A meal with nutrition totals and food items.
    """
    id: UUID
    user_id: UUID

    # Meal info
    name: Optional[str] = None
    meal_type: str
    logged_at: datetime
    notes: Optional[str] = None

    # Nutrition totals (sum of meal_items)
    total_calories: Decimal = Field(ge=0)
    total_protein_g: Decimal = Field(ge=0)
    total_carbs_g: Decimal = Field(ge=0)
    total_fat_g: Decimal = Field(ge=0)

    # AI tracking
    source: str = "manual"
    ai_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    ai_cost_usd: Decimal = Field(default=Decimal("0"))

    # Items
    items: List[MealItem] = Field(default_factory=list)

    # Metadata
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('total_calories', 'total_protein_g', 'total_carbs_g', 'total_fat_g', 'ai_confidence', 'ai_cost_usd')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[float]:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None


class MealListResponse(BaseModel):
    """Response for meal list endpoint."""
    meals: List[Meal]
    total: int


# =====================================================
# Nutrition Stats Models
# =====================================================

class NutritionStats(BaseModel):
    """
    Daily nutrition summary.

    Shows totals consumed vs goals for a specific date.
    """
    date: str = Field(description="ISO date (YYYY-MM-DD)")

    # Consumed totals
    calories_consumed: Decimal = Field(ge=0)
    protein_consumed: Decimal = Field(ge=0)
    carbs_consumed: Decimal = Field(ge=0)
    fat_consumed: Decimal = Field(ge=0)

    # Goals (from user profile)
    calories_goal: Optional[int] = None
    protein_goal: Optional[int] = None
    carbs_goal: Optional[int] = None
    fat_goal: Optional[int] = None

    # Meal breakdown
    meals_count: int = 0
    meals_by_type: dict = Field(default_factory=dict, description="Count by meal_type")

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('calories_consumed', 'protein_consumed', 'carbs_consumed', 'fat_consumed')
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization."""
        return float(value)
