"""
Output schemas for program generation API.

These models define the structure of generated programs returned to external systems.
All models support JSON serialization for database storage.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from enum import Enum
import uuid


# ============================================================================
# TRAINING PLAN OUTPUTS
# ============================================================================

class ExerciseInstruction(BaseModel):
    """Single exercise in a workout."""
    
    exercise_id: Optional[str] = Field(None, description="Exercise UUID (if from database)")
    exercise_name: str = Field(..., description="Exercise name")
    
    # Volume prescription
    sets: int = Field(..., ge=1, le=20, description="Number of sets")
    rep_range: str = Field(..., description="Rep range (e.g., '6-8', '8-12', 'AMRAP')")
    rir: Optional[int] = Field(None, ge=0, le=5, description="Reps in reserve (0-5)")
    rpe: Optional[int] = Field(None, ge=1, le=10, description="Rate of perceived exertion (1-10)")
    
    # Rest and tempo
    rest_seconds: int = Field(default=90, ge=30, le=600, description="Rest between sets")
    tempo: Optional[str] = Field(None, description="Tempo (e.g., '3-1-1-0')")
    
    # Progression notes
    weight_recommendation: Optional[str] = Field(None, description="Weight guidance")
    progression_notes: Optional[str] = Field(None, description="How to progress")
    
    # Metadata
    muscle_groups_primary: List[str] = Field(default_factory=list, description="Primary muscles")
    muscle_groups_secondary: List[str] = Field(default_factory=list, description="Secondary muscles")
    equipment_needed: List[str] = Field(default_factory=list, description="Required equipment")
    
    # Instructions
    video_url: Optional[str] = Field(None, description="Exercise demonstration video")
    instructions: Optional[str] = Field(None, description="How to perform")
    common_mistakes: Optional[str] = Field(None, description="What to avoid")
    
    class Config:
        json_schema_extra = {
            "example": {
                "exercise_name": "Barbell Squat",
                "sets": 4,
                "rep_range": "6-8",
                "rir": 2,
                "rest_seconds": 180,
                "weight_recommendation": "Start with 80% of 1RM",
                "muscle_groups_primary": ["quadriceps", "glutes"],
                "equipment_needed": ["barbell", "squat_rack"]
            }
        }


class TrainingSession(BaseModel):
    """Complete workout session."""
    
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Session UUID")
    session_name: str = Field(..., description="Session name (e.g., 'Upper Body A', 'Leg Day')")
    day_of_week: Optional[str] = Field(None, description="Planned day (monday, tuesday, etc.)")
    time_of_day: Optional[str] = Field(None, description="morning, afternoon, evening")
    
    # Session structure
    exercises: List[ExerciseInstruction] = Field(..., description="Exercises in order")
    
    # Timing
    estimated_duration_minutes: int = Field(..., ge=15, le=180, description="Estimated duration")
    warmup_notes: Optional[str] = Field(None, description="Warmup recommendations")
    cooldown_notes: Optional[str] = Field(None, description="Cooldown recommendations")
    
    # Volume metrics
    total_sets: int = Field(..., description="Total sets in session")
    total_volume_per_muscle: Dict[str, int] = Field(default_factory=dict, description="Sets per muscle group")
    
    # Intensity
    average_intensity: Optional[float] = Field(None, ge=0, le=1, description="Average intensity (0-1)")
    
    # Notes
    focus: Optional[str] = Field(None, description="Session focus (e.g., 'Strength', 'Hypertrophy')")
    notes: Optional[str] = Field(None, description="Additional session notes")


class TrainingPlan(BaseModel):
    """Complete training program."""
    
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Training plan UUID")
    
    # Program structure
    split_type: str = Field(..., description="Split type (e.g., 'upper_lower', 'ppl', 'full_body')")
    sessions_per_week: int = Field(..., ge=1, le=7, description="Training frequency")
    
    # Weekly sessions
    weekly_sessions: List[TrainingSession] = Field(..., description="Sessions for the week")
    
    # Volume distribution
    weekly_volume_per_muscle: Dict[str, int] = Field(..., description="Total sets per muscle per week")
    
    # Periodization
    current_phase: str = Field(default="accumulation", description="Training phase")
    deload_week: int = Field(default=5, ge=3, le=8, description="Deload every N weeks")
    progression_scheme: str = Field(default="linear", description="How to progress (linear, wave, etc.)")
    
    # Intensity zones
    primary_intensity_zone: str = Field(..., description="Main intensity focus (strength/hypertrophy/endurance)")
    
    # Notes
    program_notes: Optional[str] = Field(None, description="Overall program notes")
    exercise_substitutions: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Alternative exercises for each movement"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "split_type": "upper_lower_4x",
                "sessions_per_week": 4,
                "weekly_volume_per_muscle": {
                    "chest": 14,
                    "back": 16,
                    "quadriceps": 14,
                    "hamstrings": 10
                },
                "primary_intensity_zone": "hypertrophy",
                "deload_week": 5
            }
        }


# ============================================================================
# NUTRITION PLAN OUTPUTS
# ============================================================================

class FoodItem(BaseModel):
    """Single food item in a meal."""
    
    food_id: Optional[str] = Field(None, description="Food UUID (if from database)")
    food_name: str = Field(..., description="Food name")
    
    # Serving
    serving_size: float = Field(..., gt=0, description="Serving amount")
    serving_unit: str = Field(..., description="Unit (g, oz, cup, etc.)")
    
    # Macros
    calories: float = Field(..., ge=0, description="Calories")
    protein_g: float = Field(..., ge=0, description="Protein grams")
    carbs_g: float = Field(..., ge=0, description="Carbohydrate grams")
    fat_g: float = Field(..., ge=0, description="Fat grams")
    fiber_g: Optional[float] = Field(None, ge=0, description="Fiber grams")
    
    # Prep notes
    preparation: Optional[str] = Field(None, description="How to prepare")
    
    class Config:
        json_schema_extra = {
            "example": {
                "food_name": "Chicken Breast",
                "serving_size": 200,
                "serving_unit": "g",
                "calories": 330,
                "protein_g": 62,
                "carbs_g": 0,
                "fat_g": 7.2
            }
        }


class Meal(BaseModel):
    """Single meal with foods."""
    
    meal_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Meal UUID")
    meal_name: str = Field(..., description="Meal name (e.g., 'Breakfast', 'Post-Workout')")
    meal_time: Optional[str] = Field(None, description="Time of day")
    
    # Foods
    foods: List[FoodItem] = Field(..., description="Foods in this meal")
    
    # Totals
    total_calories: float = Field(..., ge=0, description="Total calories")
    total_protein_g: float = Field(..., ge=0, description="Total protein")
    total_carbs_g: float = Field(..., ge=0, description="Total carbs")
    total_fat_g: float = Field(..., ge=0, description="Total fat")
    total_fiber_g: Optional[float] = Field(None, ge=0, description="Total fiber")
    
    # Notes
    recipe_url: Optional[str] = Field(None, description="Recipe link if applicable")
    prep_time_minutes: Optional[int] = Field(None, ge=0, description="Prep time")
    notes: Optional[str] = Field(None, description="Meal notes")


# ============================================================================
# MULTIMODAL TRAINING (ENDURANCE/HIIT/SPORT)
# ============================================================================

class MultimodalInterval(BaseModel):
    """Interval step for endurance/HIIT sessions."""

    work_minutes: float = Field(..., gt=0, description="Work interval length (minutes)")
    rest_minutes: Optional[float] = Field(None, ge=0, description="Rest interval length (minutes)")
    target: Optional[str] = Field(None, description="Target pace/HR/RPE for the work segment")


class MultimodalDrill(BaseModel):
    """Skill drill for sport sessions (e.g., tennis)."""

    name: str = Field(..., description="Drill name")
    duration_minutes: int = Field(..., ge=5, le=180, description="Estimated duration")
    focus: Optional[str] = Field(None, description="Skill focus (serve, footwork, rally)")


class MultimodalSession(BaseModel):
    """Generic non-resistance session: endurance, HIIT, sport."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Session UUID")
    session_kind: str = Field(..., description="endurance | hiit | sport")
    modality: str = Field(..., description="running | cycling | tennis | rowing | swimming | other")
    day_of_week: Optional[str] = Field(None, description="monday..sunday (optional)")
    time_of_day: Optional[str] = Field(None, description="morning, afternoon, evening")
    start_hour: Optional[int] = Field(None, ge=0, le=23, description="Start hour (0-23) if fixed")
    end_hour: Optional[int] = Field(None, ge=1, le=24, description="End hour (1-24) if fixed")
    duration_minutes: int = Field(..., ge=10, le=300, description="Planned session length")
    intensity_target: Optional[str] = Field(None, description="pace/HR zone/RPE")
    intervals: Optional[List[MultimodalInterval]] = Field(None, description="Interval structure, if any")
    drills: Optional[List[MultimodalDrill]] = Field(None, description="Sport drills, if any")
    notes: Optional[str] = Field(None, description="Session notes")


class DailyMealPlan(BaseModel):
    """Meals for one day."""
    
    plan_date: date = Field(..., description="Date for this meal plan")
    day_name: Optional[str] = Field(None, description="Day name (e.g., 'Monday')")
    training_day: bool = Field(default=False, description="Is this a training day?")
    
    # Meals
    meals: List[Meal] = Field(..., description="Meals for the day (3-6 meals)")
    
    # Daily totals
    daily_calories: float = Field(..., ge=0, description="Total daily calories")
    daily_protein_g: float = Field(..., ge=0, description="Total daily protein")
    daily_carbs_g: float = Field(..., ge=0, description="Total daily carbs")
    daily_fat_g: float = Field(..., ge=0, description="Total daily fat")
    daily_fiber_g: Optional[float] = Field(None, ge=0, description="Total daily fiber")
    
    # Adherence
    meal_timing_notes: Optional[str] = Field(None, description="Timing recommendations")
    hydration_target_ml: Optional[int] = Field(None, ge=0, description="Water intake goal")


class NutritionPlan(BaseModel):
    """Complete nutrition program."""
    
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Nutrition plan UUID")
    
    # Targets
    daily_calorie_target: int = Field(..., ge=1000, le=6000, description="Daily calorie goal")
    daily_protein_g: int = Field(..., ge=50, le=500, description="Daily protein goal")
    daily_carbs_g: int = Field(..., ge=0, le=1000, description="Daily carbs goal")
    daily_fat_g: int = Field(..., ge=20, le=300, description="Daily fat goal")
    
    # Flexibility ranges (for adherence)
    calorie_range_lower: int = Field(..., description="Lower acceptable bound")
    calorie_range_upper: int = Field(..., description="Upper acceptable bound")
    
    # Meal plans (typically 14 days)
    meal_plans: List[DailyMealPlan] = Field(..., description="Daily meal plans")
    
    # Dietary info
    dietary_preference: str = Field(..., description="Diet type (omnivore, vegetarian, etc.)")
    excluded_foods: List[str] = Field(default_factory=list, description="Foods to avoid")
    
    # Macro split
    protein_percentage: float = Field(..., ge=10, le=50, description="% of calories from protein")
    carbs_percentage: float = Field(..., ge=10, le=70, description="% of calories from carbs")
    fat_percentage: float = Field(..., ge=15, le=50, description="% of calories from fat")
    
    # Notes
    meal_timing_strategy: Optional[str] = Field(None, description="Meal timing approach")
    supplement_recommendations: Optional[List[str]] = Field(None, description="Suggested supplements")
    notes: Optional[str] = Field(None, description="Nutrition notes")


# ============================================================================
# GROCERY LIST
# ============================================================================

class GroceryCategory(str, Enum):
    """Grocery store sections."""
    PRODUCE = "produce"
    PROTEINS = "proteins"
    DAIRY = "dairy"
    GRAINS = "grains"
    OILS_SPICES = "oils_spices"
    FROZEN = "frozen"
    CANNED = "canned"
    BEVERAGES = "beverages"
    OTHER = "other"


class GroceryItem(BaseModel):
    """Single item on grocery list."""
    
    item_name: str = Field(..., description="Item name")
    category: GroceryCategory = Field(..., description="Store section")
    
    # Quantity
    quantity: float = Field(..., gt=0, description="Amount needed")
    unit: str = Field(..., description="Unit (g, lb, units, etc.)")
    
    # Shopping info
    estimated_cost_usd: Optional[float] = Field(None, ge=0, description="Estimated cost")
    brand_recommendations: Optional[List[str]] = Field(None, description="Suggested brands")
    
    # Frequency
    days_used: int = Field(..., ge=1, le=14, description="Days this item appears")
    total_servings: int = Field(..., ge=1, description="Total servings needed")
    
    # Bulk buying
    bulk_option: Optional[str] = Field(None, description="Bulk buying suggestion")


class GroceryList(BaseModel):
    """Complete shopping list."""
    
    list_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Grocery list UUID")
    
    # Items by category
    items_by_category: Dict[GroceryCategory, List[GroceryItem]] = Field(
        ...,
        description="Items organized by store section"
    )
    
    # Summary
    total_items: int = Field(..., ge=0, description="Total unique items")
    total_estimated_cost_usd: Optional[float] = Field(None, ge=0, description="Total estimated cost")
    cost_per_day_usd: Optional[float] = Field(None, ge=0, description="Daily cost")
    
    # Time period
    covers_days: int = Field(default=14, ge=1, description="Days this list covers")
    
    # Notes
    budget_tips: Optional[List[str]] = Field(None, description="Cost-saving suggestions")
    shopping_tips: Optional[str] = Field(None, description="Shopping advice")


# ============================================================================
# VALIDATION RESULTS
# ============================================================================

class SafetyIssue(BaseModel):
    """Single safety concern."""
    
    level: str = Field(..., description="Severity: blocked, warning, info")
    category: str = Field(..., description="Category: medical, age, goal, etc.")
    message: str = Field(..., description="Human-readable explanation")
    recommendation: Optional[str] = Field(None, description="Suggested action")


class SafetyReport(BaseModel):
    """Safety validation results."""
    
    passed: bool = Field(..., description="Whether safety validation passed")
    level: str = Field(..., description="Overall level: cleared, warning, blocked")
    
    # Issues found
    issues: List[SafetyIssue] = Field(default_factory=list, description="Safety concerns")
    
    # Modifications applied
    modifications_applied: Optional[List[str]] = Field(
        None,
        description="Automatic modifications made to ensure safety"
    )
    
    # Clearance requirements
    requires_medical_clearance: bool = Field(default=False, description="Needs doctor approval")
    requires_trainer_supervision: bool = Field(default=False, description="Needs professional supervision")
    
    # Validation metadata
    validated_at: datetime = Field(default_factory=datetime.now, description="Validation timestamp")


class FeasibilityReport(BaseModel):
    """Constraint solver results."""
    
    feasible: bool = Field(..., description="Whether goals are achievable")
    status: str = Field(..., description="Solver status: feasible, infeasible, timeout")
    
    # Solver metrics
    runtime_ms: int = Field(..., ge=0, description="Solver runtime")
    iterations: Optional[int] = Field(None, ge=0, description="Solver iterations")
    
    # If feasible
    optimal_params: Optional[Dict[str, Any]] = Field(None, description="Optimal solution parameters")
    
    # If infeasible
    diagnostics: Optional[List[Dict[str, Any]]] = Field(None, description="Why infeasible")
    trade_off_options: Optional[List[Dict[str, Any]]] = Field(None, description="Alternative options (A/B/C)")
    
    # Validation metadata
    validated_at: datetime = Field(default_factory=datetime.now, description="Validation timestamp")


# ============================================================================
# COMPLETE PROGRAM BUNDLE
# ============================================================================

class TDEEResult(BaseModel):
    """Energy expenditure calculation."""
    
    tdee_mean: int = Field(..., ge=1000, le=6000, description="Mean TDEE estimate")
    tdee_ci_lower: int = Field(..., description="Lower confidence bound")
    tdee_ci_upper: int = Field(..., description="Upper confidence bound")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    
    # Source data
    equations_used: List[str] = Field(..., description="TDEE equations applied")
    activity_factor: float = Field(..., ge=1.0, le=2.5, description="Activity multiplier")
    
    # Notes
    notes: List[str] = Field(default_factory=list, description="Calculation notes")


class MacroTargets(BaseModel):
    """Macronutrient targets."""
    
    calories: int = Field(..., ge=1000, le=6000, description="Daily calories")
    protein_g: int = Field(..., ge=50, le=500, description="Daily protein")
    carbs_g: int = Field(..., ge=0, le=1000, description="Daily carbs")
    fat_g: int = Field(..., ge=20, le=300, description="Daily fat")
    
    # Rationale
    protein_g_per_kg: float = Field(..., description="Protein per kg body weight")
    rationale: List[str] = Field(..., description="Reasoning for macro split")


class ProgramBundle(BaseModel):
    """
    Complete generated program.
    
    This is the primary output from program generation.
    Contains training plan, nutrition plan, and all metadata.
    """
    
    # Identity
    program_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Program UUID")
    version: str = Field(default="1.0.0", description="Semantic version (major.minor.patch)")
    
    # User context
    user_id: str = Field(..., description="User UUID")
    session_id: Optional[str] = Field(None, description="Consultation session UUID")
    
    # Goals
    primary_goal: str = Field(..., description="Primary goal (muscle_gain, fat_loss, etc.)")
    goal_description: Optional[str] = Field(None, description="Detailed goal description")
    
    # Timeline
    program_start_date: date = Field(default_factory=date.today, description="Program start date")
    program_duration_weeks: int = Field(..., ge=4, le=52, description="Total program duration")
    next_reassessment_date: Optional[date] = Field(None, description="Next check-in date")
    
    # Generated plans
    training_plan: TrainingPlan = Field(..., description="Complete training program")
    nutrition_plan: NutritionPlan = Field(..., description="Complete nutrition program")
    grocery_list: Optional[GroceryList] = Field(None, description="Shopping list")
    multimodal_sessions_weekly: Optional[List[MultimodalSession]] = Field(
        default=None,
        description="Optional weekly schedule of endurance/HIIT/sport sessions"
    )
    
    # Validation results
    tdee_result: TDEEResult = Field(..., description="Energy expenditure calculation")
    macro_targets: MacroTargets = Field(..., description="Macro targets")
    safety_report: SafetyReport = Field(..., description="Safety validation")
    feasibility_report: FeasibilityReport = Field(..., description="Constraint validation")
    
    # Expected outcomes
    expected_rate_of_change_kg_per_week: float = Field(
        ...,
        description="Expected weight change per week (positive=gain, negative=loss)"
    )
    expected_outcome_timeline: Optional[str] = Field(
        None,
        description="Timeline for expected results"
    )
    
    # Provenance (metadata about how this was generated)
    provenance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Generation metadata (models, parameters, timestamps)"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    # Schema version for backward compatibility
    schema_version: str = Field(default="1.0.0", description="Schema version")
    
    def to_json(self) -> Dict[str, Any]:
        """
        Serialize to JSON-safe dictionary.
        
        Returns dict suitable for database storage or API responses.
        """
        data = self.model_dump(mode='json')
        
        # Ensure dates are ISO format strings
        if isinstance(data.get('program_start_date'), date):
            data['program_start_date'] = data['program_start_date'].isoformat()
        if isinstance(data.get('next_reassessment_date'), date):
            data['next_reassessment_date'] = data['next_reassessment_date'].isoformat()
        if isinstance(data.get('created_at'), datetime):
            data['created_at'] = data['created_at'].isoformat()
        if isinstance(data.get('updated_at'), datetime):
            data['updated_at'] = data['updated_at'].isoformat()
            
        return data
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "ProgramBundle":
        """
        Deserialize from JSON dictionary.
        
        Handles version migrations if schema_version differs.
        """
        schema_version = data.get('schema_version', '1.0.0')
        
        # Handle version migrations here if needed in future
        if schema_version != '1.0.0':
            # Future: Implement migration logic
            pass
        
        # Parse datetime strings back to objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
        return cls(**data)
    
    class Config:
        json_schema_extra = {
            "example": {
                "program_id": "550e8400-e29b-41d4-a716-446655440000",
                "version": "1.0.0",
                "user_id": "user-uuid-123",
                "primary_goal": "muscle_gain",
                "program_duration_weeks": 12,
                "expected_rate_of_change_kg_per_week": 0.35,
                "tdee_result": {
                    "tdee_mean": 2700,
                    "tdee_ci_lower": 2550,
                    "tdee_ci_upper": 2850,
                    "confidence": 0.85,
                    "equations_used": ["Mifflin-St Jeor", "Harris-Benedict"],
                    "activity_factor": 1.55
                }
            }
        }


__all__ = [
    # Training outputs
    "ExerciseInstruction",
    "TrainingSession",
    "TrainingPlan",
    # Nutrition outputs
    "FoodItem",
    "Meal",
    "DailyMealPlan",
    "NutritionPlan",
    # Grocery
    "GroceryCategory",
    "GroceryItem",
    "GroceryList",
    # Validation
    "SafetyIssue",
    "SafetyReport",
    "FeasibilityReport",
    # Supporting
    "TDEEResult",
    "MacroTargets",
    # Main output
    "ProgramBundle",
]
