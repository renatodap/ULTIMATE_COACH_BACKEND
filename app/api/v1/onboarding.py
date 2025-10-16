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

class OnboardingData(BaseModel):
    """Complete onboarding data from all 6 steps."""

    # Step 1: Goals & Experience
    primary_goal: Literal['lose_weight', 'build_muscle', 'maintain', 'improve_performance'] = Field(
        ...,
        description="Primary fitness goal"
    )
    experience_level: Literal['beginner', 'intermediate', 'advanced'] = Field(
        ...,
        description="Fitness experience level"
    )
    workout_frequency: int = Field(..., ge=0, le=7, description="Workouts per week")

    # Step 2: Physical Stats (ALWAYS IN METRIC - frontend converts if needed)
    birth_date: Optional[date] = Field(default=None, description="Birth date (YYYY-MM-DD)")
    age: Optional[int] = Field(default=None, ge=13, le=120)
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
    def validate_birth_or_age(cls, v: Optional[date], info) -> Optional[date]:
        bdate = v
        age = info.data.get('age')
        if bdate is None and age is None:
            raise ValueError('Either birth_date or age is required')
        if bdate is not None:
            today = date.today()
            derived = int((today - bdate).days // 365.25)
            if derived < 13 or derived > 120:
                raise ValueError('Derived age from birth_date must be between 13 and 120')
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

        # Log incoming payload summary (no sensitive tokens)
        log_event(
            "onboarding_request_received",
            user_id=user['id'],
            primary_goal=data.primary_goal,
            experience_level=data.experience_level,
            activity_level=data.activity_level,
            age=data.age,
            sex=data.biological_sex,
            height_cm=data.height_cm,
            current_weight_kg=data.current_weight_kg,
            goal_weight_kg=data.goal_weight_kg,
            meals_per_day=data.meals_per_day,
            unit_system=data.unit_system,
            timezone=data.timezone,
            content_type=content_type,
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
