"""
Onboarding API endpoints.

Handles comprehensive user onboarding flow including:
- Physical stats collection
- Dietary preferences
- Lifestyle data
- Macro calculation and target setting
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from app.api.dependencies import get_current_user
from app.services.macro_calculator import calculate_targets, MacroTargets
from app.services.supabase_service import supabase_service
from app.utils.logger import log_event

router = APIRouter()


# ============================================================================
# REQUEST MODELS
# ============================================================================

class OnboardingData(BaseModel):
    """Complete onboarding data from all 6 steps."""

    # Step 1: Goals & Experience
    primary_goal: str = Field(..., description="lose_weight, build_muscle, maintain, improve_performance")
    experience_level: str = Field(..., description="beginner, intermediate, advanced")
    workout_frequency: int = Field(..., ge=0, le=7, description="Workouts per week")

    # Step 2: Physical Stats (ALWAYS IN METRIC - frontend converts if needed)
    age: int = Field(..., ge=13, le=120)
    biological_sex: str = Field(..., description="male or female")
    height_cm: float = Field(..., ge=100, le=300)
    current_weight_kg: float = Field(..., ge=30, le=300)
    goal_weight_kg: float = Field(..., ge=30, le=300)

    # Step 3: Activity Level
    activity_level: str = Field(..., description="sedentary, lightly_active, moderately_active, very_active, extremely_active")

    # Step 4: Dietary Profile
    dietary_preference: str = Field(
        default="none",
        description="none, vegetarian, vegan, pescatarian, keto, paleo"
    )
    food_allergies: List[str] = Field(default_factory=list)
    foods_to_avoid: List[str] = Field(default_factory=list)
    meals_per_day: int = Field(default=3, ge=1, le=8)

    # Step 5: Lifestyle
    sleep_hours: float = Field(..., ge=4, le=12)
    stress_level: str = Field(default="medium", description="low, medium, high")
    cooks_regularly: bool = Field(default=True)

    # User Preferences
    unit_system: str = Field(default="imperial", description="metric or imperial")
    timezone: str = Field(default="America/New_York")

    @validator('primary_goal')
    def validate_primary_goal(cls, v):
        valid = ['lose_weight', 'build_muscle', 'maintain', 'improve_performance']
        if v not in valid:
            raise ValueError(f'primary_goal must be one of: {valid}')
        return v

    @validator('experience_level')
    def validate_experience_level(cls, v):
        valid = ['beginner', 'intermediate', 'advanced']
        if v not in valid:
            raise ValueError(f'experience_level must be one of: {valid}')
        return v

    @validator('biological_sex')
    def validate_biological_sex(cls, v):
        valid = ['male', 'female']
        if v not in valid:
            raise ValueError(f'biological_sex must be one of: {valid}')
        return v

    @validator('activity_level')
    def validate_activity_level(cls, v):
        valid = ['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active']
        if v not in valid:
            raise ValueError(f'activity_level must be one of: {valid}')
        return v

    @validator('dietary_preference')
    def validate_dietary_preference(cls, v):
        valid = ['none', 'vegetarian', 'vegan', 'pescatarian', 'keto', 'paleo']
        if v not in valid:
            raise ValueError(f'dietary_preference must be one of: {valid}')
        return v

    @validator('stress_level')
    def validate_stress_level(cls, v):
        valid = ['low', 'medium', 'high']
        if v not in valid:
            raise ValueError(f'stress_level must be one of: {valid}')
        return v

    @validator('unit_system')
    def validate_unit_system(cls, v):
        valid = ['metric', 'imperial']
        if v not in valid:
            raise ValueError(f'unit_system must be one of: {valid}')
        return v

    @validator('goal_weight_kg')
    def validate_goal_weight(cls, v, values):
        """Ensure goal weight is reasonable relative to current weight."""
        if 'current_weight_kg' in values:
            current = values['current_weight_kg']
            # Goal can't be more than 50% different from current (safety check)
            if abs(v - current) > current * 0.5:
                raise ValueError('goal_weight_kg must be within 50% of current_weight_kg')
        return v


class OnboardingResponse(BaseModel):
    """Response after completing onboarding."""

    profile: dict
    targets: MacroTargets
    message: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/complete",
    response_model=OnboardingResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete onboarding",
    description="Complete onboarding process and calculate macro targets",
)
async def complete_onboarding(
    data: OnboardingData,
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
        # Step 1: Calculate macro targets
        log_event(
            "onboarding_macro_calculation_started",
            user_id=str(user_id),
            primary_goal=data.primary_goal,
            activity_level=data.activity_level
        )

        targets = calculate_targets(
            age=data.age,
            sex=data.biological_sex,
            height_cm=data.height_cm,
            current_weight_kg=data.current_weight_kg,
            goal_weight_kg=data.goal_weight_kg,
            activity_level=data.activity_level,
            primary_goal=data.primary_goal,
            experience_level=data.experience_level
        )

        log_event(
            "onboarding_macro_calculation_completed",
            user_id=str(user_id),
            bmr=targets.bmr,
            tdee=targets.tdee,
            calories=targets.daily_calories,
            protein=targets.daily_protein_g
        )

        # Step 2: Prepare profile update
        profile_update = {
            # Physical stats
            'age': data.age,
            'biological_sex': data.biological_sex,
            'height_cm': data.height_cm,
            'current_weight_kg': data.current_weight_kg,
            'goal_weight_kg': data.goal_weight_kg,

            # Goals
            'primary_goal': data.primary_goal,
            'experience_level': data.experience_level,

            # Activity & Lifestyle
            'activity_level': data.activity_level,
            'workout_frequency': data.workout_frequency,
            'sleep_hours': data.sleep_hours,
            'stress_level': data.stress_level,

            # Dietary
            'dietary_preference': data.dietary_preference,
            'food_allergies': data.food_allergies,
            'foods_to_avoid': data.foods_to_avoid,
            'meals_per_day': data.meals_per_day,
            'cooks_regularly': data.cooks_regularly,

            # Calculated targets
            'estimated_tdee': targets.tdee,
            'daily_calorie_goal': targets.daily_calories,
            'daily_protein_goal': targets.daily_protein_g,
            'daily_carbs_goal': targets.daily_carbs_g,
            'daily_fat_goal': targets.daily_fat_g,

            # Preferences
            'unit_system': data.unit_system,
            'timezone': data.timezone,

            # Onboarding status
            'onboarding_completed': True,
            'onboarding_completed_at': datetime.utcnow().isoformat(),

            # Macro metadata
            'macros_last_calculated_at': datetime.utcnow().isoformat(),
            'macros_calculation_reason': 'initial_onboarding',
        }

        # Step 3: Update profile
        updated_profile = await supabase_service.update_profile(user_id, profile_update)

        if not updated_profile:
            log_event("onboarding_profile_update_failed", user_id=str(user_id))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )

        log_event(
            "onboarding_completed",
            user_id=str(user_id),
            primary_goal=data.primary_goal,
            daily_calories=targets.daily_calories
        )

        # Step 4: Return response
        return OnboardingResponse(
            profile=updated_profile,
            targets=targets,
            message="Onboarding completed successfully! Your personalized targets are ready."
        )

    except ValueError as e:
        log_event("onboarding_validation_error", user_id=str(user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        log_event("onboarding_error", user_id=str(user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete onboarding. Please try again."
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
