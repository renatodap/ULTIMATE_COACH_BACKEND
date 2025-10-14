"""
Pydantic models for meal planning.

Models for 14-day meal plans, grocery lists, and daily meal structures.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID


class MealItem(BaseModel):
    """Individual food item in a meal"""
    food_id: Optional[UUID] = None
    food_name: str
    quantity: float
    unit: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float

    class Config:
        from_attributes = True


class Meal(BaseModel):
    """A complete meal (breakfast, lunch, dinner, snack)"""
    meal_type: str = Field(..., description="breakfast, lunch, dinner, snack")
    name: str
    items: List[MealItem]
    total_calories: int
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    prep_time_minutes: Optional[int] = None
    recipe_instructions: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class MealPlanDay(BaseModel):
    """A single day in the meal plan"""
    day: int = Field(..., ge=1, le=14, description="Day number (1-14)")
    date: Optional[str] = None  # ISO date string for specific date
    meals: List[Meal]
    daily_totals: Dict[str, float] = Field(
        ...,
        description="Daily totals: calories, protein_g, carbs_g, fat_g"
    )

    class Config:
        from_attributes = True


class GroceryItem(BaseModel):
    """Item on grocery list"""
    item: str
    quantity: str  # "2 lbs", "1 dozen", "500g"
    category: str = Field(
        ...,
        description="produce, proteins, grains, dairy, snacks, condiments, etc."
    )
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class GroceryList(BaseModel):
    """Organized grocery list by category"""
    produce: List[GroceryItem] = Field(default_factory=list)
    proteins: List[GroceryItem] = Field(default_factory=list)
    grains: List[GroceryItem] = Field(default_factory=list)
    dairy: List[GroceryItem] = Field(default_factory=list)
    snacks: List[GroceryItem] = Field(default_factory=list)
    condiments: List[GroceryItem] = Field(default_factory=list)
    other: List[GroceryItem] = Field(default_factory=list)

    def get_all_items(self) -> List[GroceryItem]:
        """Get all items from all categories"""
        return (
            self.produce + self.proteins + self.grains +
            self.dairy + self.snacks + self.condiments + self.other
        )

    class Config:
        from_attributes = True


class MealPlan(BaseModel):
    """Complete 14-day meal plan"""
    id: UUID
    user_id: UUID
    plan_version: int
    days: List[MealPlanDay]
    grocery_list: Optional[Dict[str, Any]] = None  # JSONB from database

    # Macro targets (denormalized)
    target_calories_per_day: Optional[int] = None
    target_protein_g_per_day: Optional[int] = None
    target_carbs_g_per_day: Optional[int] = None
    target_fat_g_per_day: Optional[int] = None

    # Validity
    valid_from: datetime
    valid_until: datetime
    is_active: bool = True

    # Generation metadata
    generation_prompt: Optional[str] = None
    ai_model: Optional[str] = None
    generation_cost_usd: Optional[float] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateMealPlanRequest(BaseModel):
    """Request to generate a meal plan"""
    user_id: UUID

    # Nutritional targets
    daily_calorie_goal: int = Field(..., ge=1000, le=10000)
    daily_protein_g: int = Field(..., ge=50, le=500)
    daily_carbs_g: int = Field(..., ge=50, le=800)
    daily_fat_g: int = Field(..., ge=20, le=300)

    # Preferences
    dietary_restrictions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    meal_preferences: Dict[str, Any] = Field(default_factory=dict)

    # Persona-specific
    persona_type: Optional[str] = None

    class Config:
        from_attributes = True


class MealPlanSummary(BaseModel):
    """Summary of a meal plan (for list views)"""
    id: UUID
    plan_version: int
    valid_from: datetime
    valid_until: datetime
    is_active: bool
    total_days: int
    avg_calories_per_day: float
    avg_protein_per_day: float
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateMealInPlanRequest(BaseModel):
    """Request to update a single meal in the plan"""
    day: int = Field(..., ge=1, le=14)
    meal_type: str
    new_meal: Meal

    class Config:
        from_attributes = True


class MacroTargets(BaseModel):
    """Daily macro targets"""
    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int

    # Calculated fields
    protein_pct: Optional[float] = None
    carbs_pct: Optional[float] = None
    fat_pct: Optional[float] = None

    class Config:
        from_attributes = True
