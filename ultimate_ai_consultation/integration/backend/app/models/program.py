"""
Pydantic Models for Program Management API

Drop-in file for: ULTIMATE_COACH_BACKEND/app/models/program.py

These models define request/response schemas for the programs API.
All models are designed to serialize directly to JSON for frontend consumption.
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from enum import Enum


# =============================================================================
# Request Models
# =============================================================================


class GenerateProgramRequest(BaseModel):
    """
    Request to generate initial program from consultation data.

    Expected after user completes ConsultationAIService flow.
    """

    user_id: str = Field(..., description="User UUID")

    consultation_data: Dict[str, Any] = Field(
        ...,
        description="Raw consultation data with all user inputs",
        example={
            "goal": "muscle_gain",
            "age": 28,
            "biological_sex": "male",
            "height_cm": 180,
            "weight_kg": 82,
            "activity_level": "moderately_active",
            "training_experience": "intermediate",
            "workouts_per_week": 5,
            "workout_duration_minutes": 60,
            "equipment_access": ["full_gym"],
            "dietary_preferences": ["none"],
            "medical_conditions": [],
        }
    )

    force_regenerate: bool = Field(
        False,
        description="If True, regenerate even if active plan exists"
    )


class TriggerReassessmentRequest(BaseModel):
    """Request to manually trigger bi-weekly reassessment"""

    user_id: str
    force: bool = Field(
        False,
        description="If True, run reassessment even if not due yet"
    )


# =============================================================================
# Response Models - Enums for Type Safety
# =============================================================================


class PlanStatus(str, Enum):
    """Plan version status"""
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class AdjustmentReason(str, Enum):
    """Why was an adjustment made?"""
    BI_WEEKLY_REASSESSMENT = "bi_weekly_reassessment"
    PROGRESS_TOO_SLOW = "progress_too_slow"
    PROGRESS_TOO_FAST = "progress_too_fast"
    LOW_ADHERENCE = "low_adherence"
    EXCESSIVE_FATIGUE = "excessive_fatigue"
    INJURY_PREVENTION = "injury_prevention"
    MANUAL_TRIGGER = "manual_trigger"


class SplitType(str, Enum):
    """Training split types"""
    FULL_BODY = "full_body"
    UPPER_LOWER = "upper_lower"
    PUSH_PULL_LEGS = "push_pull_legs"
    BODY_PART_SPLIT = "body_part_split"


class DayOfWeek(str, Enum):
    """Days of the week"""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


# =============================================================================
# Nested Models - Building Blocks
# =============================================================================


class MacroTargets(BaseModel):
    """Daily macro targets"""

    calories: int = Field(..., ge=1200, le=6000)
    protein_g: int = Field(..., ge=50, le=500)
    carbs_g: int = Field(..., ge=50, le=800)
    fat_g: int = Field(..., ge=30, le=200)

    # Helpful for UI display
    protein_kcal: Optional[int] = None
    carbs_kcal: Optional[int] = None
    fat_kcal: Optional[int] = None

    @validator('protein_kcal', 'carbs_kcal', 'fat_kcal', always=True)
    def calculate_macro_calories(cls, v, values, field):
        """Auto-calculate kcal from grams"""
        if field.name == 'protein_kcal' and 'protein_g' in values:
            return values['protein_g'] * 4
        elif field.name == 'carbs_kcal' and 'carbs_g' in values:
            return values['carbs_g'] * 4
        elif field.name == 'fat_kcal' and 'fat_g' in values:
            return values['fat_g'] * 9
        return v


class ExerciseSet(BaseModel):
    """Single set in an exercise"""

    set_number: int
    reps: int
    weight_kg: Optional[float] = None
    rpe: Optional[float] = Field(None, ge=1, le=10, description="Rate of Perceived Exertion")
    rest_seconds: int = Field(..., ge=30, le=600)


class Exercise(BaseModel):
    """Single exercise in a workout"""

    exercise_id: str
    exercise_name: str
    muscle_group: str
    sets: List[ExerciseSet]
    total_sets: int
    notes: Optional[str] = None

    # Helpful for UI
    video_url: Optional[str] = None
    form_cues: List[str] = Field(default_factory=list)


class WorkoutSession(BaseModel):
    """Complete workout for a single day"""

    workout_id: str
    day_name: str  # "Day 1: Upper Body" or "Monday: Push"
    muscle_groups: List[str]
    exercises: List[Exercise]
    estimated_duration_minutes: int
    total_sets: int
    notes: Optional[str] = None


class MealItem(BaseModel):
    """Single food item in a meal"""

    food_id: str
    food_name: str
    quantity: float
    unit: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float


class Meal(BaseModel):
    """Single meal (breakfast, lunch, etc)"""

    meal_id: str
    meal_name: str  # "Breakfast", "Lunch", "Dinner", "Snack"
    meal_number: int  # 1, 2, 3, 4
    foods: List[MealItem]
    total_calories: int
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    prep_time_minutes: Optional[int] = None
    recipe_url: Optional[str] = None


class DayMealPlan(BaseModel):
    """Complete meal plan for one day"""

    day_number: int  # 1-14
    meals: List[Meal]
    daily_totals: MacroTargets


class GroceryItem(BaseModel):
    """Single item on shopping list"""

    food_name: str
    quantity: float
    unit: str
    category: str  # "Protein", "Produce", "Grains", etc
    estimated_cost_usd: Optional[float] = None
    notes: Optional[str] = None


# =============================================================================
# Main Response Models
# =============================================================================


class ProgramSummary(BaseModel):
    """
    Summary response after generating initial program.

    This is what the frontend receives immediately after generation.
    """

    plan_id: str
    user_id: str
    version: int
    status: PlanStatus

    # High-level plan info
    split_type: SplitType
    workouts_per_week: int
    estimated_workout_duration: int
    cycle_length_weeks: int

    # Nutrition targets
    macro_targets: MacroTargets

    # Metadata
    created_at: datetime
    valid_from: date
    valid_until: Optional[date] = None

    # Warnings/flags
    warnings: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)

    # User-facing message
    welcome_message: str = Field(
        ...,
        description="Personalized message sent to user via coach"
    )


class ActivePlanResponse(BaseModel):
    """
    Complete active plan details.

    Returns everything the user needs to follow their program.
    """

    # Plan metadata
    plan_id: str
    user_id: str
    version: int
    status: PlanStatus

    # Plan parameters
    split_type: SplitType
    workouts_per_week: int
    cycle_length_weeks: int
    current_week: int
    current_day: int

    # Targets
    macro_targets: MacroTargets

    # Complete workouts (all days in microcycle)
    workouts: List[WorkoutSession]

    # Complete meal plans (14 days)
    meal_plans: List[DayMealPlan]

    # Dates
    valid_from: date
    valid_until: Optional[date]
    created_at: datetime

    # Grocery list
    grocery_list: List[GroceryItem]

    # Any warnings or notes
    warnings: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class TodayPlanResponse(BaseModel):
    """
    Today's specific workout and meals.

    This is the most commonly requested endpoint - what should I do today?
    """

    plan_id: str
    user_id: str
    today_date: date

    # What day are we on?
    cycle_day: int  # Which day in the microcycle (1-7 for Upper/Lower)
    cycle_week: int  # Which week in the mesocycle
    calendar_day: DayOfWeek

    # Is today a training day?
    is_training_day: bool
    training_day_number: Optional[int] = None  # 1st, 2nd, 3rd workout this week

    # Today's workout (if training day)
    workout: Optional[WorkoutSession] = None

    # Today's meals
    meals: List[Meal]

    # Targets
    macro_targets: MacroTargets

    # Helpful context
    days_until_next_reassessment: int
    last_reassessment_date: Optional[date] = None

    # Quick actions for user
    suggested_actions: List[str] = Field(
        default_factory=lambda: [
            "Log your meals",
            "Complete your workout",
            "Weigh yourself (if scheduled)",
        ]
    )


class ProgressMetrics(BaseModel):
    """Aggregated progress metrics"""

    # Weight progression
    start_weight_kg: Optional[float] = None
    current_weight_kg: Optional[float] = None
    weight_change_kg: Optional[float] = None
    weight_change_rate_per_week: Optional[float] = None
    target_rate_per_week: Optional[float] = None

    # Adherence
    meal_logging_adherence: float = Field(..., ge=0.0, le=1.0)
    training_adherence: float = Field(..., ge=0.0, le=1.0)

    # Nutrition compliance
    avg_calories_consumed: Optional[int] = None
    avg_protein_consumed_g: Optional[float] = None
    calorie_adherence: Optional[float] = Field(None, ge=0.0, le=2.0)

    # Training volume
    total_sets_completed: Optional[int] = None
    avg_sets_per_workout: Optional[float] = None

    # Data quality
    days_with_meals_logged: int
    days_with_workouts_logged: int
    days_with_weight_logged: int
    total_days_in_period: int


class ProgressResponse(BaseModel):
    """
    Progress summary for last N days.

    Used for progress dashboard and charts.
    """

    user_id: str
    plan_id: str
    plan_version: int

    # Time period
    start_date: date
    end_date: date
    days_analyzed: int

    # Metrics
    metrics: ProgressMetrics

    # Trend analysis
    trend_direction: Literal["exceeding", "on_track", "slow", "stalled", "insufficient_data"]
    confidence_score: float = Field(..., ge=0.0, le=1.0)

    # Flags
    red_flags: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    # Time series data for charts (frontend can plot these)
    weight_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="[{date: '2024-01-01', weight_kg: 82.0}, ...]"
    )

    calorie_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="[{date: '2024-01-01', calories: 2500}, ...]"
    )


class GroceryListResponse(BaseModel):
    """
    Shopping list for current meal plan.

    Organized by category for easy shopping.
    """

    plan_id: str
    user_id: str
    generated_at: datetime

    # Items organized by category
    items_by_category: Dict[str, List[GroceryItem]] = Field(
        ...,
        description="{'Protein': [...], 'Produce': [...], ...}"
    )

    # Totals
    total_items: int
    estimated_total_cost_usd: Optional[float] = None

    # Metadata
    covers_days: int = Field(..., description="How many days this list covers")
    notes: List[str] = Field(
        default_factory=lambda: [
            "Buy fresh produce mid-week if needed",
            "Check pantry before shopping",
        ]
    )


class AdjustmentRecord(BaseModel):
    """
    Single adjustment made to a plan.

    Stored in plan_adjustments table.
    """

    adjustment_id: str
    plan_id: str
    from_version: int
    to_version: int

    # What changed?
    calories_before: int
    calories_after: int
    volume_before: int
    volume_after: int

    # Why did it change?
    adjustment_reason: AdjustmentReason
    rationale: str

    # When?
    created_at: datetime

    # Supporting data
    progress_metrics: Optional[ProgressMetrics] = None


class PlanVersion(BaseModel):
    """
    Single version of a user's plan.

    Plans are versioned - each reassessment creates a new version.
    """

    plan_id: str
    version: int
    user_id: str
    status: PlanStatus

    # Dates
    created_at: datetime
    valid_from: date
    valid_until: Optional[date]

    # Summary info
    macro_targets: MacroTargets
    split_type: SplitType
    workouts_per_week: int

    # What changed? (if version > 1)
    changes_from_previous: Optional[str] = None


class PlanHistoryResponse(BaseModel):
    """
    Complete history of a user's plan versions and adjustments.

    Used for "Why did my plan change?" transparency.
    """

    user_id: str
    current_plan_id: str
    current_version: int

    # All versions
    versions: List[PlanVersion]

    # All adjustments
    adjustments: List[AdjustmentRecord]

    # Summary stats
    total_versions: int
    total_adjustments: int
    plan_start_date: date
    days_on_plan: int


# =============================================================================
# Database Models (for internal use, not API responses)
# =============================================================================


class PlanVersionDB(BaseModel):
    """
    Internal database model for plan_versions table.

    Includes full JSONB plan data.
    """

    id: str
    user_id: str
    version: int
    status: PlanStatus

    # Full plan stored as JSONB
    plan_data: Dict[str, Any]  # Complete plan with workouts, meals, everything

    # Metadata
    created_at: datetime
    valid_from: date
    valid_until: Optional[date]
    superseded_by: Optional[str]  # ID of newer version

    # Extracted for querying
    split_type: str
    workouts_per_week: int
    daily_calories: int


class AdjustmentRecordDB(BaseModel):
    """
    Internal database model for plan_adjustments table.
    """

    id: str
    plan_id: str
    from_version: int
    to_version: int

    adjustment_type: str  # "calorie", "volume", "both"
    adjustment_reason: AdjustmentReason

    # Changes
    changes_json: Dict[str, Any]  # Complete diff

    # Supporting data
    progress_data_json: Optional[Dict[str, Any]]
    rationale: str

    created_at: datetime


# =============================================================================
# Error Responses
# =============================================================================


class ErrorResponse(BaseModel):
    """Standard error response"""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationErrorDetail(BaseModel):
    """Detailed validation error"""

    field: str
    issue: str
    provided_value: Any


class ValidationErrorResponse(BaseModel):
    """Validation error with field-level details"""

    error: str = "validation_error"
    message: str
    errors: List[ValidationErrorDetail]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Success Responses
# =============================================================================


class SuccessResponse(BaseModel):
    """Generic success response"""

    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ReassessmentTriggeredResponse(BaseModel):
    """Response when reassessment is triggered"""

    success: bool = True
    message: str = "Reassessment triggered and running in background"
    estimated_completion_seconds: int = 30
    check_progress_url: str  # URL to poll for completion
