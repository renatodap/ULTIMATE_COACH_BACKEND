"""
Input schemas for program generation API.

These models define the contract for external systems calling this module.
All fields are validated and documented for clear integration.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class TrainingModalityInput(BaseModel):
    """Training modality from consultation."""
    
    modality: str = Field(..., description="Training type (e.g., 'bodybuilding', 'powerlifting', 'crossfit')")
    proficiency: str = Field(..., description="Skill level: beginner, intermediate, advanced, expert")
    years_experience: int = Field(..., ge=0, le=50, description="Years of experience in this modality")
    is_primary: bool = Field(default=False, description="Is this the primary training focus?")
    enjoys_it: Optional[bool] = Field(None, description="Does user enjoy this modality?")
    

class FamiliarExerciseInput(BaseModel):
    """Exercise familiarity from consultation."""
    
    exercise_id: Optional[str] = Field(None, description="UUID of exercise (if from database)")
    exercise_name: str = Field(..., description="Exercise name (e.g., 'Squat', 'Bench Press')")
    comfort_level: int = Field(..., ge=1, le=5, description="1=uncomfortable, 5=mastered")
    frequency: Optional[str] = Field(None, description="How often: never_done, rarely, occasionally, regularly, frequently")


class PreferredMealTimeInput(BaseModel):
    """Meal timing preference from consultation."""
    
    time_of_day: str = Field(..., description="Meal time: breakfast, lunch, dinner, etc.")
    typical_hour: Optional[int] = Field(None, ge=0, le=23, description="Typical hour (24h format)")
    is_flexible: bool = Field(default=True, description="Can meal time be adjusted?")


class TypicalMealFoodInput(BaseModel):
    """Typical foods user eats."""
    
    food_name: str = Field(..., description="Food name")
    meal_time: str = Field(..., description="When eaten: breakfast, lunch, dinner, snack")
    frequency: str = Field(..., description="How often: daily, weekly, occasionally")


class UpcomingEventInput(BaseModel):
    """Event or goal user is training for."""
    
    event_name: str = Field(..., description="Event name (e.g., 'Marathon', 'Wedding', 'Competition')")
    event_type: str = Field(..., description="Type: race, competition, aesthetic_goal, personal_milestone")
    event_date: Optional[datetime] = Field(None, description="When the event occurs")
    weeks_until: Optional[int] = Field(None, ge=0, description="Weeks until event")
    priority: int = Field(default=5, ge=1, le=10, description="Importance (1-10)")


class TrainingAvailabilityInput(BaseModel):
    """When user can train."""
    
    day_of_week: str = Field(..., description="monday, tuesday, wednesday, thursday, friday, saturday, sunday")
    time_of_day: List[str] = Field(default_factory=list, description="morning, afternoon, evening")
    duration_minutes: Optional[int] = Field(None, ge=15, le=300, description="Available duration")


class ImprovementGoalInput(BaseModel):
    """What user wants to improve."""
    
    goal_type: str = Field(..., description="Type: strength, muscle_gain, fat_loss, endurance, performance, health")
    description: str = Field(..., description="Detailed goal description")
    priority: int = Field(default=5, ge=1, le=10, description="Priority (1-10)")
    target_metric: Optional[str] = Field(None, description="Measurable target (e.g., '10% body fat', '2x bodyweight squat')")
    timeline_weeks: Optional[int] = Field(None, ge=1, description="Desired timeline")


class FacilityAccessInput(BaseModel):
    """Facilities the user can access for training (courts, tracks, bikes)."""

    facility_type: str = Field(..., description="court, track, pool, bike, rower, trainer, field")
    days_available: List[str] = Field(default_factory=list, description="monday..sunday available days")
    notes: Optional[str] = Field(None, description="Additional context about access")


class ModalityPreferenceInput(BaseModel):
    """User preference for additional modalities beyond resistance training."""

    modality: str = Field(..., description="running, cycling, tennis, hiit, rowing, swimming, mobility")
    priority: int = Field(default=5, ge=1, le=10, description="Importance (1-10)")
    target_sessions_per_week: Optional[int] = Field(None, ge=0, le=14, description="Desired weekly frequency")
    min_duration_minutes: Optional[int] = Field(None, ge=10, le=240, description="Minimum session length")
    max_duration_minutes: Optional[int] = Field(None, ge=10, le=300, description="Maximum session length")
    facility_needed: Optional[str] = Field(None, description="court, bike, pool, track, none")
    intensity_preference: Optional[str] = Field(None, description="low, moderate, high")


class DifficultyInput(BaseModel):
    """Challenges or barriers."""
    
    category: str = Field(..., description="Category: time, budget, equipment, social, motivation, injury")
    description: str = Field(..., description="Detailed description of difficulty")
    severity: int = Field(default=5, ge=1, le=10, description="How limiting (1-10)")


class NonNegotiableInput(BaseModel):
    """Hard constraints that cannot be violated."""
    
    constraint: str = Field(..., description="What cannot be changed")
    reason: str = Field(..., description="Why it's non-negotiable")


class UserDemographics(BaseModel):
    """Basic user information."""
    
    user_id: str = Field(..., description="User UUID")
    age: int = Field(..., ge=13, le=100, description="Age in years")
    sex_at_birth: str = Field(..., description="Biological sex: male or female")
    weight_kg: float = Field(..., gt=0, le=300, description="Current weight in kilograms")
    height_cm: float = Field(..., gt=0, le=300, description="Height in centimeters")
    body_fat_percentage: Optional[float] = Field(None, ge=1, le=60, description="Body fat % (optional)")
    
    @field_validator('sex_at_birth')
    @classmethod
    def validate_sex(cls, v: str) -> str:
        if v.lower() not in ['male', 'female']:
            raise ValueError("sex_at_birth must be 'male' or 'female'")
        return v.lower()


class ConsultationTranscript(BaseModel):
    """
    Complete consultation data for program generation.
    
    This is the primary input for generate_program_from_consultation().
    External systems should build this from their consultation database records.
    """
    
    # Session metadata
    user_id: str = Field(..., description="User UUID")
    session_id: str = Field(..., description="Consultation session UUID")
    completed_at: datetime = Field(default_factory=datetime.now, description="When consultation was completed")
    
    # User demographics (required)
    demographics: UserDemographics = Field(..., description="User demographics")
    
    # Training profile (from consultation)
    training_modalities: List[TrainingModalityInput] = Field(
        default_factory=list,
        description="Training styles user has experience with"
    )
    familiar_exercises: List[FamiliarExerciseInput] = Field(
        default_factory=list,
        description="Exercises user is comfortable with"
    )
    training_availability: List[TrainingAvailabilityInput] = Field(
        default_factory=list,
        description="When user can train"
    )
    
    # Nutrition profile
    preferred_meal_times: List[PreferredMealTimeInput] = Field(
        default_factory=list,
        description="When user prefers to eat"
    )
    typical_foods: List[TypicalMealFoodInput] = Field(
        default_factory=list,
        description="Foods user typically eats"
    )

    # Facilities and additional modalities
    facility_access: List[FacilityAccessInput] = Field(
        default_factory=list,
        description="Facilities the user can access (courts, tracks, bikes)"
    )
    modality_preferences: List[ModalityPreferenceInput] = Field(
        default_factory=list,
        description="Preferences for running/cycling/tennis/HIIT/etc."
    )
    
    # Goals and context
    improvement_goals: List[ImprovementGoalInput] = Field(
        default_factory=list,
        description="What user wants to achieve"
    )
    upcoming_events: List[UpcomingEventInput] = Field(
        default_factory=list,
        description="Events user is training for"
    )
    
    # Constraints
    difficulties: List[DifficultyInput] = Field(
        default_factory=list,
        description="Challenges or barriers"
    )
    non_negotiables: List[NonNegotiableInput] = Field(
        default_factory=list,
        description="Hard constraints"
    )
    
    # Conversation context (optional)
    conversation_summary: Optional[str] = Field(
        None,
        description="Summary of consultation conversation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "660e8400-e29b-41d4-a716-446655440001",
                "demographics": {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "age": 28,
                    "sex_at_birth": "male",
                    "weight_kg": 82.0,
                    "height_cm": 178.0,
                    "body_fat_percentage": 18.0
                },
                "training_modalities": [
                    {
                        "modality": "bodybuilding",
                        "proficiency": "intermediate",
                        "years_experience": 3,
                        "is_primary": True
                    }
                ],
                "improvement_goals": [
                    {
                        "goal_type": "muscle_gain",
                        "description": "Gain 5kg of lean muscle",
                        "priority": 10,
                        "target_metric": "87kg at 15% body fat",
                        "timeline_weeks": 16
                    }
                ]
            }
        }


class EquipmentAvailability(str, Enum):
    """Equipment availability options."""
    FULL_GYM = "full_gym"
    HOME_GYM_BASIC = "home_gym_basic"  # Dumbbells, bench
    HOME_GYM_ADVANCED = "home_gym_advanced"  # Barbell, rack, etc.
    BODYWEIGHT_ONLY = "bodyweight_only"
    MINIMAL = "minimal"  # Resistance bands, light equipment


class DietaryMode(str, Enum):
    """Dietary preferences."""
    OMNIVORE = "omnivore"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    FLEXIBLE = "flexible"


class GenerationOptions(BaseModel):
    """
    Optional parameters for program generation.
    
    Controls how programs are generated without changing the core logic.
    All parameters have sensible defaults.
    """
    
    # Program structure
    program_duration_weeks: int = Field(
        default=12,
        ge=4,
        le=52,
        description="Total program duration (default: 12 weeks)"
    )
    
    initial_plan_days: int = Field(
        default=14,
        ge=7,
        le=28,
        description="Days in initial plan (default: 14)"
    )
    
    # Training preferences
    equipment_available: EquipmentAvailability = Field(
        default=EquipmentAvailability.FULL_GYM,
        description="Available equipment"
    )
    
    intensity_preference: Optional[str] = Field(
        None,
        description="Prefer lower, moderate, or higher intensity"
    )
    
    # Nutrition preferences
    dietary_mode: DietaryMode = Field(
        default=DietaryMode.FLEXIBLE,
        description="Dietary preference"
    )
    
    meal_prep_level: str = Field(
        default="moderate",
        description="Meal prep complexity: minimal, moderate, advanced"
    )
    
    budget_per_week_usd: Optional[float] = Field(
        None,
        ge=0,
        description="Weekly food budget (optional constraint)"
    )
    
    # Safety overrides (use with caution)
    skip_safety_validation: bool = Field(
        default=False,
        description="⚠️ Skip safety checks (NOT RECOMMENDED)"
    )
    
    # Advanced options
    seed: Optional[int] = Field(
        None,
        description="Random seed for deterministic generation"
    )
    
    include_exercise_videos: bool = Field(
        default=True,
        description="Include exercise instruction links"
    )
    
    include_grocery_list: bool = Field(
        default=True,
        description="Generate grocery list"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "program_duration_weeks": 12,
                "equipment_available": "full_gym",
                "dietary_mode": "vegetarian",
                "budget_per_week_usd": 100.0,
                "seed": 42
            }
        }


class ProgressUpdate(BaseModel):
    """
    Progress data for adaptive adjustments (Phase 2).
    
    Used with adjust_program() to update an existing program.
    """
    
    # Time period
    assessment_period_days: int = Field(..., ge=1, description="Days since last assessment")
    
    # Body metrics
    weight_measurements: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Weight measurements: [{date, weight_kg, confidence}]"
    )
    
    # Adherence
    meal_logging_days: int = Field(default=0, ge=0, description="Days with meals logged")
    training_sessions_completed: int = Field(default=0, ge=0, description="Training sessions completed")
    training_sessions_planned: int = Field(default=0, ge=0, description="Training sessions planned")
    
    # Subjective feedback
    energy_level: Optional[int] = Field(None, ge=1, le=10, description="Average energy (1-10)")
    soreness_level: Optional[int] = Field(None, ge=1, le=10, description="Average soreness (1-10)")
    hunger_level: Optional[int] = Field(None, ge=1, le=10, description="Average hunger (1-10)")
    motivation: Optional[int] = Field(None, ge=1, le=10, description="Motivation level (1-10)")
    
    # Coach conversation signals (optional)
    recent_messages: List[str] = Field(
        default_factory=list,
        description="Recent coach conversation messages for sentiment analysis"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "assessment_period_days": 14,
                "weight_measurements": [
                    {"date": "2025-10-01", "weight_kg": 82.0, "confidence": 0.9},
                    {"date": "2025-10-07", "weight_kg": 82.3, "confidence": 0.9},
                    {"date": "2025-10-14", "weight_kg": 82.6, "confidence": 0.85}
                ],
                "meal_logging_days": 12,
                "training_sessions_completed": 6,
                "training_sessions_planned": 7,
                "energy_level": 7,
                "soreness_level": 4,
                "motivation": 8
            }
        }


__all__ = [
    # Consultation inputs
    "TrainingModalityInput",
    "FamiliarExerciseInput",
    "PreferredMealTimeInput",
    "TypicalMealFoodInput",
    "UpcomingEventInput",
    "TrainingAvailabilityInput",
    "ImprovementGoalInput",
    "DifficultyInput",
    "NonNegotiableInput",
    "UserDemographics",
    "ConsultationTranscript",
    # Generation options
    "EquipmentAvailability",
    "DietaryMode",
    "GenerationOptions",
    # Progress tracking
    "ProgressUpdate",
]
