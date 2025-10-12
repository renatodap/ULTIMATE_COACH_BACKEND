"""
Pydantic models for First Consultation system.

All consultation models follow relational structure - user answers reference
database entries (foreign keys) rather than free text.
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ProficiencyLevel(str, Enum):
    """Proficiency level for training modalities and exercises."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class FrequencyType(str, Enum):
    """How often user does something."""
    NEVER_DONE = "never_done"
    RARELY = "rarely"
    OCCASIONALLY = "occasionally"
    REGULARLY = "regularly"
    FREQUENTLY = "frequently"


class MealFrequency(str, Enum):
    """How often user eats a food."""
    DAILY = "daily"
    SEVERAL_TIMES_WEEK = "several_times_week"
    WEEKLY = "weekly"
    OCCASIONALLY = "occasionally"


class PortionSize(str, Enum):
    """Typical meal portion size."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class TimeOfDay(str, Enum):
    """Times of day for training or meals."""
    EARLY_MORNING = "early_morning"
    MORNING = "morning"
    MIDDAY = "midday"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


class LocationType(str, Enum):
    """Where user trains."""
    HOME = "home"
    GYM = "gym"
    OUTDOOR = "outdoor"
    OFFICE = "office"
    FLEXIBLE = "flexible"


class GoalType(str, Enum):
    """Types of improvement goals."""
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    SKILL = "skill"
    AESTHETIC = "aesthetic"
    BODY_COMPOSITION = "body_composition"
    MOBILITY = "mobility"
    PERFORMANCE = "performance"
    HEALTH = "health"


class DifficultyCategory(str, Enum):
    """Categories of difficulties user faces."""
    MOTIVATION = "motivation"
    TIME_MANAGEMENT = "time_management"
    INJURY = "injury"
    NUTRITION = "nutrition"
    KNOWLEDGE = "knowledge"
    CONSISTENCY = "consistency"
    ENERGY = "energy"
    SOCIAL_SUPPORT = "social_support"
    EQUIPMENT_ACCESS = "equipment_access"
    TRAVEL = "travel"
    OTHER = "other"


class ConstraintType(str, Enum):
    """Types of non-negotiable constraints."""
    REST_DAYS = "rest_days"
    MEAL_TIMING = "meal_timing"
    EQUIPMENT = "equipment"
    EXERCISES_EXCLUDED = "exercises_excluded"
    FOODS_EXCLUDED = "foods_excluded"
    TIME_BLOCKS = "time_blocks"
    SOCIAL = "social"
    RELIGIOUS = "religious"
    MEDICAL = "medical"
    OTHER = "other"


class ConsultationSection(str, Enum):
    """Sections of the consultation flow."""
    TRAINING_MODALITIES = "training_modalities"
    EXERCISE_FAMILIARITY = "exercise_familiarity"
    TRAINING_SCHEDULE = "training_schedule"
    MEAL_TIMING = "meal_timing"
    TYPICAL_FOODS = "typical_foods"
    GOALS_EVENTS = "goals_events"
    CHALLENGES = "challenges"
    REVIEW = "review"


# ============================================================================
# REFERENCE TABLE RESPONSES (Read-only)
# ============================================================================

class TrainingModalityResponse(BaseModel):
    """Training modality from database."""
    id: str
    name: str
    description: Optional[str] = None
    typical_frequency_per_week: Optional[int] = None
    equipment_required: List[str] = []
    icon: Optional[str] = None


class ExerciseResponse(BaseModel):
    """Exercise from database."""
    id: str
    name: str
    description: Optional[str] = None
    category: str
    primary_muscle_groups: List[str] = []
    secondary_muscle_groups: List[str] = []
    equipment_needed: List[str] = []
    difficulty_level: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    primary_modalities: List[str] = []


class MealTimeResponse(BaseModel):
    """Meal time from database."""
    id: str
    time_of_day: str
    label: str
    typical_hour: Optional[int] = None
    description: Optional[str] = None


class EventTypeResponse(BaseModel):
    """Event type from database."""
    id: str
    name: str
    category: str
    typical_duration_weeks: Optional[int] = None
    description: Optional[str] = None


# ============================================================================
# USER CONSULTATION LINK TABLE REQUESTS (Create/Update)
# ============================================================================

class UserTrainingModalityCreate(BaseModel):
    """Add training modality to user's profile."""
    modality_id: str = Field(..., description="UUID of training_modalities entry")
    is_primary: bool = Field(False, description="Is this the user's primary modality?")
    proficiency_level: ProficiencyLevel
    years_experience: Optional[int] = Field(None, ge=0, le=50)
    enjoys_it: Optional[bool] = None
    willing_to_continue: bool = True


class UserFamiliarExerciseCreate(BaseModel):
    """Add exercise to user's familiar exercises."""
    exercise_id: str = Field(..., description="UUID of exercises entry")
    comfort_level: int = Field(..., ge=1, le=5, description="1=uncomfortable, 5=mastered")
    last_performed_date: Optional[date] = None
    frequency: FrequencyType
    typical_weight_kg: Optional[float] = Field(None, ge=0)
    typical_reps: Optional[int] = Field(None, ge=1)
    typical_duration_minutes: Optional[int] = Field(None, ge=1)
    enjoys_it: Optional[bool] = None
    willing_to_do: bool = True
    notes: Optional[str] = None


class UserPreferredMealTimeCreate(BaseModel):
    """Add meal time to user's schedule."""
    meal_time_id: str = Field(..., description="UUID of meal_times entry")
    typical_portion_size: PortionSize
    flexibility_minutes: int = Field(30, ge=0, le=180)
    is_non_negotiable: bool = False
    notes: Optional[str] = None


class UserTypicalMealFoodCreate(BaseModel):
    """Add food to user's typical meals."""
    food_id: str = Field(..., description="UUID of foods entry")
    meal_time_id: Optional[str] = Field(None, description="UUID of meal_times entry (optional)")
    frequency: MealFrequency
    typical_quantity_grams: Optional[float] = Field(None, ge=0)
    typical_serving_id: Optional[str] = Field(None, description="UUID of food_servings entry")
    enjoys_it: bool = True
    willing_to_continue: bool = True


class UserUpcomingEventCreate(BaseModel):
    """Add event/goal to user's timeline."""
    event_type_id: Optional[str] = Field(None, description="UUID of event_types entry (optional)")
    event_name: str = Field(..., description="Custom event name")
    event_date: Optional[date] = None
    priority: int = Field(3, ge=1, le=5, description="1=low, 5=critical")
    specific_goals: List[str] = []
    notes: Optional[str] = None


class UserTrainingAvailabilityCreate(BaseModel):
    """Add training time to user's schedule."""
    day_of_week: int = Field(..., ge=1, le=7, description="1=Monday, 7=Sunday")
    time_of_day: TimeOfDay
    typical_duration_minutes: int = Field(..., ge=15, le=240)
    min_duration_minutes: Optional[int] = Field(None, ge=15)
    max_duration_minutes: Optional[int] = Field(None, le=240)
    location_type: LocationType
    is_flexible: bool = True
    is_preferred: bool = False
    notes: Optional[str] = None


class UserImprovementGoalCreate(BaseModel):
    """Add improvement goal to user's profile."""
    goal_type: GoalType
    target_description: str
    measurement_metric: Optional[str] = None
    current_value: Optional[float] = None
    target_value: Optional[float] = None
    target_date: Optional[date] = None
    priority: int = Field(3, ge=1, le=5)
    exercise_id: Optional[str] = Field(None, description="UUID of exercises entry (optional)")
    notes: Optional[str] = None


class UserDifficultyCreate(BaseModel):
    """Add difficulty/challenge to user's profile."""
    difficulty_category: DifficultyCategory
    description: str
    severity: int = Field(3, ge=1, le=5, description="1=minor, 5=major blocker")
    frequency: Optional[str] = None
    triggers: List[str] = []
    attempted_solutions: List[str] = []
    what_worked: Optional[str] = None
    what_didnt_work: Optional[str] = None


class UserNonNegotiableCreate(BaseModel):
    """Add non-negotiable constraint to user's profile."""
    constraint_type: ConstraintType
    description: str
    reason: Optional[str] = None
    excluded_exercise_ids: List[str] = []
    excluded_food_ids: List[str] = []
    is_permanent: bool = True
    end_date: Optional[date] = None


# ============================================================================
# RESPONSES WITH IDS (After creation)
# ============================================================================

class UserTrainingModalityResponse(UserTrainingModalityCreate):
    """Training modality with ID."""
    id: str
    user_id: str
    created_at: datetime


class UserFamiliarExerciseResponse(UserFamiliarExerciseCreate):
    """Familiar exercise with ID."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class UserPreferredMealTimeResponse(UserPreferredMealTimeCreate):
    """Preferred meal time with ID."""
    id: str
    user_id: str
    created_at: datetime


class UserTypicalMealFoodResponse(UserTypicalMealFoodCreate):
    """Typical meal food with ID."""
    id: str
    user_id: str
    created_at: datetime


class UserUpcomingEventResponse(UserUpcomingEventCreate):
    """Upcoming event with ID."""
    id: str
    user_id: str
    is_completed: bool = False
    created_at: datetime
    updated_at: datetime


class UserTrainingAvailabilityResponse(UserTrainingAvailabilityCreate):
    """Training availability with ID."""
    id: str
    user_id: str
    created_at: datetime


class UserImprovementGoalResponse(UserImprovementGoalCreate):
    """Improvement goal with ID."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class UserDifficultyResponse(UserDifficultyCreate):
    """Difficulty with ID."""
    id: str
    user_id: str
    created_at: datetime


class UserNonNegotiableResponse(UserNonNegotiableCreate):
    """Non-negotiable with ID."""
    id: str
    user_id: str
    created_at: datetime


# ============================================================================
# CONSULTATION SESSION TRACKING
# ============================================================================

class ConsultationSessionResponse(BaseModel):
    """Consultation session status."""
    id: str
    user_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    current_section: Optional[ConsultationSection] = None
    progress_percentage: int = 0
    time_spent_minutes: int = 0
    created_at: datetime
    updated_at: datetime


class ConsultationSessionUpdate(BaseModel):
    """Update consultation session progress."""
    current_section: Optional[ConsultationSection] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    time_spent_minutes: Optional[int] = Field(None, ge=0)


# ============================================================================
# BULK CONSULTATION SUBMISSION
# ============================================================================

class CompleteConsultationRequest(BaseModel):
    """
    Complete consultation submission with all answers.

    This is used when user completes the entire consultation flow in one go.
    Each field is optional - user can skip sections they don't want to fill.
    """
    training_modalities: List[UserTrainingModalityCreate] = []
    familiar_exercises: List[UserFamiliarExerciseCreate] = []
    preferred_meal_times: List[UserPreferredMealTimeCreate] = []
    typical_meal_foods: List[UserTypicalMealFoodCreate] = []
    upcoming_events: List[UserUpcomingEventCreate] = []
    training_availability: List[UserTrainingAvailabilityCreate] = []
    improvement_goals: List[UserImprovementGoalCreate] = []
    difficulties: List[UserDifficultyCreate] = []
    non_negotiables: List[UserNonNegotiableCreate] = []


class CompleteConsultationResponse(BaseModel):
    """Response after completing consultation."""
    consultation_session_id: str
    completed_at: datetime
    message: str = "Consultation completed successfully"
    items_created: dict = Field(
        default_factory=dict,
        description="Count of items created in each category"
    )


# ============================================================================
# SEARCH & FILTER REQUESTS
# ============================================================================

class ExerciseSearchRequest(BaseModel):
    """Search exercises by various criteria."""
    query: Optional[str] = Field(None, description="Search term for name/description")
    category: Optional[str] = None
    difficulty_level: Optional[ProficiencyLevel] = None
    equipment_needed: List[str] = []
    primary_muscle_groups: List[str] = []
    modality: Optional[str] = None
    limit: int = Field(50, ge=1, le=200)


class FoodSearchRequest(BaseModel):
    """Search foods for typical meals."""
    query: str = Field(..., description="Search term for food name")
    food_type: Optional[str] = None
    limit: int = Field(50, ge=1, le=200)


# ============================================================================
# CONSULTATION SUMMARY (For Program Generation)
# ============================================================================

class ConsultationSummary(BaseModel):
    """
    Complete consultation data for AI program generation.

    This aggregates all consultation answers into a single structure
    that can be used as context for program generation.
    """
    user_id: str
    consultation_session_id: str

    # Training Profile
    training_modalities: List[UserTrainingModalityResponse] = []
    familiar_exercises: List[UserFamiliarExerciseResponse] = []
    training_availability: List[UserTrainingAvailabilityResponse] = []

    # Nutrition Profile
    preferred_meal_times: List[UserPreferredMealTimeResponse] = []
    typical_meal_foods: List[UserTypicalMealFoodResponse] = []

    # Goals & Context
    improvement_goals: List[UserImprovementGoalResponse] = []
    upcoming_events: List[UserUpcomingEventResponse] = []

    # Constraints
    difficulties: List[UserDifficultyResponse] = []
    non_negotiables: List[UserNonNegotiableResponse] = []

    # Metadata
    completed_at: datetime
    time_spent_minutes: int
