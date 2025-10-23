"""
Onboarding API endpoints.

Handles comprehensive user onboarding flow including:
- Physical stats collection
- Dietary preferences
- Lifestyle data
- Macro calculation and target setting
"""

from datetime import datetime, date
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, ValidationError

from app.api.dependencies import get_current_user
from app.config import settings
from app.services.macro_calculator import calculate_targets, MacroTargets
from app.services.onboarding_service import onboarding_service
from app.services.supabase_service import supabase_service
from app.utils.logger import log_event

router = APIRouter()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _extract_user_jwt(request: Request, user_id: str) -> Optional[str]:
    """
    Extract user JWT from Authorization header or cookies for RLS.

    Args:
        request: FastAPI request object
        user_id: User ID for logging

    Returns:
        JWT token string or None if not found
    """
    # Try Authorization header first
    auth_header = request.headers.get('authorization') or request.headers.get('Authorization')
    if auth_header and auth_header.lower().startswith('bearer '):
        user_jwt = auth_header.split(' ', 1)[1]
        log_event(
            "onboarding_auth_from_header",
            user_id=user_id,
            token_prefix=user_jwt[:20] if user_jwt else None
        )
        return user_jwt

    # Fallback: derive JWT from cookies
    cookie_header = request.headers.get('cookie') or request.headers.get('Cookie')
    if cookie_header:
        import re, urllib.parse

        # Try backend's expected cookie name first
        m = re.search(r'access_token=([^;]+)', cookie_header)
        if m:
            try:
                user_jwt = urllib.parse.unquote(m.group(1))
                log_event(
                    "onboarding_auth_from_access_token_cookie",
                    user_id=user_id,
                    token_prefix=user_jwt[:20] if user_jwt else None
                )
                return user_jwt
            except Exception as e:
                log_event(
                    "onboarding_cookie_decode_error",
                    level="warning",
                    user_id=user_id,
                    error=str(e),
                    cookie_name="access_token"
                )
                return m.group(1)

        # Fallback to Supabase cookie name
        m = re.search(r'sb-access-token=([^;]+)', cookie_header)
        if m:
            try:
                user_jwt = urllib.parse.unquote(m.group(1))
                log_event(
                    "onboarding_auth_from_sb_cookie",
                    user_id=user_id,
                    token_prefix=user_jwt[:20] if user_jwt else None
                )
                return user_jwt
            except Exception as e:
                log_event(
                    "onboarding_cookie_decode_error",
                    level="warning",
                    user_id=user_id,
                    error=str(e),
                    cookie_name="sb-access-token"
                )
                return m.group(1)

    # Log if no JWT found
    log_event(
        "onboarding_no_jwt_found",
        level="warning",
        user_id=user_id,
        has_auth_header=bool(auth_header),
        has_cookie_header=bool(cookie_header)
    )
    return None


# ============================================================================
# REQUEST MODELS
# ============================================================================

class TrainingModalitySelection(BaseModel):
    """User's selected training modality with proficiency level."""
    modality_id: str = Field(..., description="UUID of selected training modality")
    proficiency_level: Literal['beginner', 'intermediate', 'advanced', 'expert'] = Field(
        ...,
        description="User's proficiency level in this modality"
    )
    is_primary: bool = Field(default=False, description="Whether this is the user's primary modality")


class ExerciseFamiliarityEntry(BaseModel):
    """User's familiarity with a specific exercise."""
    exercise_id: str = Field(..., description="UUID of exercise")
    comfort_level: int = Field(..., ge=1, le=5, description="Comfort level 1-5 (1=uncomfortable, 5=mastered)")
    typical_weight_kg: Optional[float] = Field(default=None, ge=0, description="Typical weight for strength exercises")
    typical_reps: Optional[int] = Field(default=None, ge=1, le=100, description="Typical reps per set")
    typical_duration_minutes: Optional[int] = Field(default=None, ge=1, le=180, description="Typical duration for cardio")
    frequency: Optional[Literal['rarely', 'occasionally', 'regularly', 'frequently']] = Field(
        default=None,
        description="How often they perform this exercise"
    )
    enjoys_it: Optional[bool] = Field(default=None, description="Whether they enjoy this exercise")


class TrainingAvailabilitySlot(BaseModel):
    """User's training availability for a specific day and time."""
    day_of_week: int = Field(..., ge=1, le=7, description="1=Monday, 7=Sunday")
    time_of_day: Literal['early_morning', 'morning', 'midday', 'afternoon', 'evening', 'night'] = Field(
        ...,
        description="Time of day for training"
    )
    typical_duration_minutes: int = Field(..., ge=15, le=240, description="Typical session duration")
    location_type: Literal['home', 'gym', 'outdoor', 'flexible'] = Field(
        ...,
        description="Where they train"
    )
    is_preferred: bool = Field(default=False, description="Preferred time vs just available")


class MealTimingPreference(BaseModel):
    """User's preferred meal timing."""
    meal_time_id: str = Field(..., description="UUID of meal time from meal_times table")
    typical_portion_size: Literal['small', 'medium', 'large'] = Field(
        ...,
        description="Typical portion size"
    )
    flexibility_minutes: int = Field(default=30, ge=0, le=180, description="How flexible is this meal time (± minutes)")
    is_non_negotiable: bool = Field(default=False, description="Must eat at this time")


class TypicalFoodEntry(BaseModel):
    """User's typically consumed food."""
    food_id: str = Field(..., description="UUID of food")
    meal_time_id: Optional[str] = Field(default=None, description="Optional: which meal this food is associated with")
    frequency: Literal['daily', 'several_times_week', 'weekly', 'occasionally'] = Field(
        ...,
        description="How often they eat this food"
    )
    typical_quantity_grams: Optional[float] = Field(default=None, ge=0, description="Typical quantity in grams")
    typical_serving_id: Optional[str] = Field(default=None, description="UUID of typical serving size")


class EventEntry(BaseModel):
    """User's upcoming event or goal."""
    event_type_id: Optional[str] = Field(default=None, description="UUID of event type (if applicable)")
    event_name: str = Field(..., min_length=1, max_length=200, description="Name of the event")
    event_date: Optional[date] = Field(default=None, description="Date of the event")
    priority: int = Field(default=3, ge=1, le=5, description="Priority 1-5 (1=low, 5=critical)")
    specific_goals: List[str] = Field(default_factory=list, description="Specific goals for this event")


class ImprovementGoalEntry(BaseModel):
    """User's improvement goal."""
    goal_type: Literal[
        'strength', 'endurance', 'skill', 'aesthetic',
        'body_composition', 'mobility', 'performance', 'health'
    ] = Field(..., description="Type of improvement goal")
    target_description: str = Field(..., min_length=1, max_length=500, description="Description of the goal")
    current_value: Optional[float] = Field(default=None, description="Current measurement value")
    target_value: Optional[float] = Field(default=None, description="Target measurement value")
    target_date: Optional[date] = Field(default=None, description="Target date to achieve goal")
    exercise_id: Optional[str] = Field(default=None, description="Optional: related exercise UUID")


class DifficultyEntry(BaseModel):
    """User's difficulty or challenge."""
    difficulty_category: Literal[
        'motivation', 'time_management', 'injury', 'nutrition',
        'knowledge', 'consistency', 'energy', 'social_support',
        'equipment_access', 'travel', 'other'
    ] = Field(..., description="Category of difficulty")
    description: str = Field(..., min_length=1, max_length=500, description="Description of the challenge")
    severity: int = Field(default=3, ge=1, le=5, description="Severity 1-5 (1=minor, 5=major blocker)")
    frequency: Optional[Literal['daily', 'weekly', 'monthly', 'occasionally']] = Field(
        default=None,
        description="How often this difficulty occurs"
    )


class NonNegotiableEntry(BaseModel):
    """User's non-negotiable constraint."""
    constraint_type: Literal[
        'rest_days', 'meal_timing', 'equipment', 'exercises_excluded',
        'foods_excluded', 'time_blocks', 'social', 'religious', 'medical', 'other'
    ] = Field(..., description="Type of constraint")
    description: str = Field(..., min_length=1, max_length=500, description="Description of the constraint")
    reason: Optional[str] = Field(default=None, max_length=500, description="Why is this non-negotiable")
    excluded_exercise_ids: List[str] = Field(default_factory=list, description="Exercise UUIDs to exclude")
    excluded_food_ids: List[str] = Field(default_factory=list, description="Food UUIDs to exclude")


class OnboardingData(BaseModel):
    """Complete onboarding data from all 6 steps."""

    # Step 1: Goals & Experience
    primary_goal: Literal['lose_weight', 'build_muscle', 'maintain', 'improve_performance'] = Field(
        ...,
        description="Primary fitness goal"
    )
    secondary_goal: Optional[Literal['lose_weight', 'build_muscle', 'maintain', 'improve_performance']] = Field(
        default=None,
        description="Optional secondary fitness goal"
    )
    experience_level: Literal['beginner', 'intermediate', 'advanced'] = Field(
        ...,
        description="Fitness experience level"
    )
    workout_frequency: int = Field(..., ge=0, le=7, description="Workouts per week")

    # Training Modalities (Step 3.5)
    training_modalities: List[TrainingModalitySelection] = Field(
        default_factory=list,
        description="User's selected training modalities with proficiency levels"
    )

    # Fitness Notes (Step 4)
    fitness_notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Free-text fitness considerations (injuries, preferences, etc.)"
    )

    # Step 2: Physical Stats (ALWAYS IN METRIC - frontend converts if needed)
    # CRITICAL: birth_date is REQUIRED. age is IGNORED (derived from birth_date server-side)
    birth_date: date = Field(..., description="Birth date (YYYY-MM-DD) - REQUIRED for accurate age calculation")
    age: Optional[int] = Field(default=None, ge=13, le=120, description="IGNORED - age is derived from birth_date server-side")
    biological_sex: Literal['male', 'female'] = Field(..., description="Biological sex for BMR calculation")
    height_cm: float = Field(..., ge=100, le=300)
    current_weight_kg: float = Field(..., ge=30, le=300)
    goal_weight_kg: float = Field(..., ge=30, le=300)

    # Step 3: Activity Level
    activity_level: Literal['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active'] = Field(
        ...,
        description="Daily activity level"
    )

    # Step 4: Dietary Profile
    dietary_preference: Literal['none', 'vegetarian', 'vegan', 'pescatarian', 'keto', 'paleo'] = Field(
        default="none",
        description="Dietary preference or restriction"
    )
    food_allergies: List[str] = Field(default_factory=list)
    foods_to_avoid: List[str] = Field(default_factory=list)
    meals_per_day: int = Field(default=3, ge=1, le=8)

    # Step 5: Lifestyle
    sleep_hours: float = Field(..., ge=4, le=12)
    stress_level: Literal['low', 'medium', 'high'] = Field(
        default="medium",
        description="Daily stress level"
    )
    cooks_regularly: bool = Field(default=True)

    # User Preferences
    unit_system: Literal['metric', 'imperial'] = Field(
        default="imperial",
        description="Preferred measurement system"
    )
    timezone: str = Field(default="America/New_York")

    # ========================================================================
    # ENHANCED ONBOARDING - Consultation Data (ALL SKIPPABLE)
    # ========================================================================

    # Phase 2: Training Background
    exercise_familiarity: List[ExerciseFamiliarityEntry] = Field(
        default_factory=list,
        description="User's familiarity with specific exercises"
    )
    training_availability: List[TrainingAvailabilitySlot] = Field(
        default_factory=list,
        description="User's training schedule availability"
    )

    # Phase 3: Nutrition Profile
    meal_timing_preferences: List[MealTimingPreference] = Field(
        default_factory=list,
        description="User's preferred meal times"
    )
    typical_foods: List[TypicalFoodEntry] = Field(
        default_factory=list,
        description="Foods the user typically eats"
    )

    # Phase 4: Goals & Context
    upcoming_events: List[EventEntry] = Field(
        default_factory=list,
        description="User's upcoming events and goals"
    )
    improvement_goals: List[ImprovementGoalEntry] = Field(
        default_factory=list,
        description="User's specific improvement goals"
    )
    difficulties: List[DifficultyEntry] = Field(
        default_factory=list,
        description="User's challenges and difficulties"
    )
    non_negotiables: List[NonNegotiableEntry] = Field(
        default_factory=list,
        description="User's non-negotiable constraints"
    )

    @field_validator('secondary_goal')
    @classmethod
    def validate_secondary_goal(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure secondary_goal is different from primary_goal."""
        if v is not None and 'primary_goal' in info.data:
            if v == info.data['primary_goal']:
                raise ValueError('secondary_goal must be different from primary_goal')
        return v

    @field_validator('goal_weight_kg')
    @classmethod
    def validate_goal_weight(cls, v: float, info) -> float:
        """Ensure goal weight is reasonable relative to current weight."""
        if 'current_weight_kg' in info.data:
            current = info.data['current_weight_kg']
            # Goal can't be more than 50% different from current (safety check)
            if abs(v - current) > current * 0.5:
                raise ValueError('goal_weight_kg must be within 50% of current_weight_kg')
        return v

    @field_validator('birth_date')
    @classmethod
    def validate_birth_date(cls, v: date) -> date:
        """Validate birth_date produces reasonable age (13-120)."""
        today = date.today()
        derived_age = int((today - v).days // 365.25)
        if derived_age < 13:
            raise ValueError(f'You must be at least 13 years old to use this app (age: {derived_age})')
        if derived_age > 120:
            raise ValueError(f'Please enter a valid birth date (calculated age: {derived_age})')
        return v


class OnboardingResponse(BaseModel):
    """Response after completing onboarding."""

    profile: dict
    targets: MacroTargets
    message: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get(
    "/training-modalities/search",
    status_code=status.HTTP_200_OK,
    summary="Search training modalities",
    description="Search training modalities by name (case-insensitive, partial match)",
)
async def search_training_modalities(
    query: str,
    limit: int = 20,
    user: dict = Depends(get_current_user)
) -> list[dict]:
    """
    Search training modalities by name.

    Enables users to search for any sport or activity type during onboarding.
    Case-insensitive partial matching on modality name.

    Args:
        query: Search query (minimum 2 characters)
        limit: Maximum results to return (default 20, max 50)
        user: Current authenticated user (from dependency)

    Returns:
        List of matching training modalities ordered by display_order

    Raises:
        HTTPException 400: Query too short
        HTTPException 500: Database error
    """

    # Validate query
    if len(query.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must be at least 2 characters"
        )

    # Clamp limit
    limit = min(max(limit, 1), 50)

    try:
        log_event(
            "training_modality_search",
            user_id=user['id'],
            query=query,
            limit=limit
        )

        # Search modalities
        response = supabase_service.supabase.table('training_modalities')\
            .select('*')\
            .ilike('name', f'%{query}%')\
            .order('display_order')\
            .limit(limit)\
            .execute()

        log_event(
            "training_modality_search_success",
            user_id=user['id'],
            query=query,
            results_count=len(response.data)
        )

        return response.data

    except Exception as e:
        log_event(
            "training_modality_search_error",
            level="error",
            user_id=user['id'],
            query=query,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search training modalities"
        )


@router.post(
    "/complete",
    response_model=OnboardingResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete onboarding",
    description="Complete onboarding process and calculate macro targets",
)
async def complete_onboarding(
    request: Request,
    user: dict = Depends(get_current_user)
) -> OnboardingResponse:
    """
    Complete onboarding and calculate personalized macro targets.

    Process:
    1. Validate all input data
    2. Calculate BMR, TDEE, and macro targets using scientific formulas
    3. Update user profile with all onboarding data
    4. Mark onboarding as completed
    5. Return profile and calculated targets

    Args:
        data: Complete onboarding data from all 6 steps
        user: Current authenticated user (from dependency)

    Returns:
        OnboardingResponse with updated profile and macro targets

    Raises:
        HTTPException 400: Invalid input data
        HTTPException 500: Failed to update profile
    """

    user_id = UUID(user['id'])

    try:
        # Defensive JSON parsing to handle proxies sending bytes or wrong content-type
        content_type = request.headers.get("content-type", "")
        try:
            payload = await request.json()
        except Exception:
            raw = await request.body()
            try:
                import json as _json
                decoded = raw.decode("utf-8", errors="replace")
                payload = _json.loads(decoded)
            except Exception as parse_err:
                # Log raw decode failure and raise 422
                log_event(
                    "onboarding_payload_parse_error",
                    level="error",
                    user_id=user['id'],
                    content_type=content_type,
                    error=str(parse_err),
                )
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid JSON body")

        # Validate against schema
        try:
            data = OnboardingData.model_validate(payload)
        except ValidationError as ve:
            # Let global 422 handler format errors; also log summary here
            log_event(
                "onboarding_payload_validation_error",
                level="error",
                user_id=user['id'],
                content_type=content_type,
                errors=ve.errors(),
            )
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=ve.errors())

        # CRITICAL: Warn if age was provided (should only send birth_date)
        if data.age is not None:
            log_event(
                "onboarding_age_parameter_sent",
                level="warning",
                user_id=user['id'],
                age_sent=data.age,
                birth_date=str(data.birth_date),
                message="Frontend sent age parameter which will be IGNORED. Only birth_date is used."
            )

        # Log incoming payload summary (no sensitive tokens)
        log_event(
            "onboarding_request_received",
            user_id=user['id'],
            primary_goal=data.primary_goal,
            experience_level=data.experience_level,
            activity_level=data.activity_level,
            birth_date=str(data.birth_date),
            sex=data.biological_sex,
            height_cm=data.height_cm,
            current_weight_kg=data.current_weight_kg,
            goal_weight_kg=data.goal_weight_kg,
            meals_per_day=data.meals_per_day,
            unit_system=data.unit_system,
            timezone=data.timezone,
            content_type=content_type,
            has_training_modalities=len(data.training_modalities) > 0,
            has_fitness_notes=bool(data.fitness_notes)
        )

        # Extract user JWT for RLS-protected writes
        user_jwt = _extract_user_jwt(request, user['id'])

        # Complete onboarding using service
        updated_profile, targets = await onboarding_service.complete_onboarding(
            user_id=user_id,
            onboarding_data=data.model_dump(),
            user_token=user_jwt
        )

        # Return response
        response = OnboardingResponse(
            profile=updated_profile,
            targets=targets,
            message="Onboarding completed successfully! Your personalized targets are ready."
        )
        log_event(
            "onboarding_complete_success",
            user_id=str(user_id),
        )
        return response

    except ValueError as e:
        log_event(
            "onboarding_validation_error",
            user_id=str(user_id),
            error=str(e),
            error_type="ValueError",
            primary_goal=data.primary_goal,
            activity_level=data.activity_level
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is (from update_profile, etc.)
        raise
    except Exception as e:
        import traceback

        log_event(
            "onboarding_error",
            level="error",
            user_id=str(user_id),
            error=str(e),
            error_type=type(e).__name__,
            primary_goal=data.primary_goal,
            activity_level=data.activity_level,
            traceback_info=traceback.format_exc()
        )

        # In development, return detailed error message
        if settings.is_development:
            detail = {
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": str(user_id),
                "traceback": traceback.format_exc()
            }
        else:
            detail = "Failed to complete onboarding. Please try again."

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="Get onboarding status",
    description="Check if user has completed onboarding",
)
async def get_onboarding_status(
    user: dict = Depends(get_current_user)
) -> JSONResponse:
    """
    Get user's onboarding status.

    Returns:
        JSON with onboarding_completed boolean and timestamp if completed
    """

    return JSONResponse(content={
        'onboarding_completed': user.get('onboarding_completed', False),
        'onboarding_completed_at': user.get('onboarding_completed_at'),
    })


@router.get(
    "/preview-targets",
    response_model=MacroTargets,
    status_code=status.HTTP_200_OK,
    summary="Preview macro targets",
    description="Preview calculated targets before completing onboarding (Step 6)",
)
async def preview_targets(
    age: int,
    biological_sex: str,
    height_cm: float,
    current_weight_kg: float,
    goal_weight_kg: float,
    activity_level: str,
    primary_goal: str,
    experience_level: str = 'beginner',
    user: dict = Depends(get_current_user)
) -> MacroTargets:
    """
    Preview macro targets without saving (for Step 6 of onboarding).

    Allows user to see calculated targets before finalizing onboarding.

    Args:
        All physical and goal parameters needed for calculation
        user: Current authenticated user (from dependency)

    Returns:
        MacroTargets with calculations and explanations
    """

    try:
        targets = calculate_targets(
            age=age,
            sex=biological_sex,
            height_cm=height_cm,
            current_weight_kg=current_weight_kg,
            goal_weight_kg=goal_weight_kg,
            activity_level=activity_level,
            primary_goal=primary_goal,
            experience_level=experience_level
        )

        log_event(
            "onboarding_preview_targets",
            user_id=user['id'],
            calories=targets.daily_calories
        )

        return targets

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameters: {str(e)}"
        )
# NOTE: Router-scoped exception handlers are not supported across all FastAPI versions.
# If 422 logging is required, register a handler in app.main using app.add_exception_handler.
