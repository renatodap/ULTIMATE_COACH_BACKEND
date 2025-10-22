"""
Programs API

Endpoints for generating and managing fitness programs.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import structlog

from app.api.dependencies import get_current_user
from app.services.program_storage_service import ProgramStorageService

logger = structlog.get_logger()
router = APIRouter()


class GenerateProgramRequest(BaseModel):
    """Request to generate a new program from user profile"""

    program_duration_weeks: Optional[int] = 12
    meals_per_day: Optional[int] = 3
    force_regenerate: Optional[bool] = False


class ProgramResponse(BaseModel):
    """Response with program details"""

    program_id: str
    user_id: str
    primary_goal: str
    program_start_date: str
    next_reassessment_date: str
    training_sessions_per_week: int
    daily_calorie_target: int
    macro_targets: dict
    message: str


@router.post("/programs/generate", response_model=ProgramResponse)
async def generate_program(
    request: GenerateProgramRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a complete fitness program for the current user.

    This endpoint:
    1. Fetches user profile data (onboarding, goals, preferences)
    2. Generates program using ultimate_ai_consultation generator
    3. Stores program in plan instance tables
    4. Returns program summary

    The program includes:
    - Training plan (weekly sessions, exercises, volume)
    - Nutrition plan (meals, macros, grocery list)
    - Safety and feasibility reports
    - 12-week calendar of planned sessions and meals
    """
    logger.info(
        "generate_program_request",
        user_id=current_user['id'],
        duration_weeks=request.program_duration_weeks,
    )

    storage_service = ProgramStorageService()

    try:
        # Import here to avoid circular dependency
        from ultimate_ai_consultation.api.generate_program import (
            generate_program_from_consultation,
        )
        from ultimate_ai_consultation.api.schemas.inputs import (
            ConsultationTranscript,
            GenerationOptions,
        )
        from datetime import date as date_type, timedelta

        # Fetch user's onboarding data from profile
        client = storage_service.db.client
        profile_result = (
            client.table("profiles")
            .select("*")
            .eq("id", current_user['id'])
            .single()
            .execute()
        )

        if not profile_result.data:
            raise HTTPException(
                status_code=404,
                detail="User profile not found. Please complete onboarding first.",
            )

        profile = profile_result.data

        # Check if onboarding is complete
        if not profile.get("onboarding_completed"):
            raise HTTPException(
                status_code=400,
                detail="Onboarding not completed. Please complete onboarding first.",
            )

        # Check if program already exists (unless force_regenerate)
        if not request.force_regenerate:
            existing_program = (
                client.table("programs")
                .select("id, created_at")
                .eq("user_id", current_user['id'])
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if existing_program.data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Program already exists (ID: {existing_program.data[0]['id']}). Use force_regenerate=true to create new program.",
                )

        logger.info(
            "converting_onboarding_to_consultation",
            user_id=current_user['id'],
            primary_goal=profile.get("primary_goal"),
        )

        # Convert onboarding data to ConsultationTranscript
        # This is a simplified conversion - ideally user would do full consultation
        from ultimate_ai_consultation.api.schemas.inputs import UserDemographics
        import uuid

        consultation = ConsultationTranscript(
            # Session metadata
            user_id=current_user['id'],
            session_id=str(uuid.uuid4()),  # Generate session ID for this program generation

            # Demographics (wrapped in UserDemographics object)
            # Use 'or' to handle None values from incomplete profiles
            demographics=UserDemographics(
                user_id=current_user['id'],
                age=profile.get("age") or 30,
                sex_at_birth=profile.get("biological_sex") or "male",
                weight_kg=profile.get("current_weight_kg") or 75.0,
                height_cm=profile.get("height_cm") or 175.0,
                body_fat_percentage=profile.get("body_fat_percentage"),  # Optional field
            ),

            # All other fields are optional Lists with default_factory
            # The program generator will work with just demographics
        )

        # Generation options
        options = GenerationOptions(
            program_duration_weeks=request.program_duration_weeks,
            meals_per_day=request.meals_per_day or profile.get("meals_per_day", 3),
        )

        logger.info(
            "generating_program",
            user_id=current_user['id'],
            duration_weeks=options.program_duration_weeks,
        )

        # Generate program
        program_bundle, warnings = generate_program_from_consultation(
            consultation, options
        )

        # Store program in database
        program_id = await storage_service.store_program_bundle(
            program_bundle=program_bundle.model_dump(),
            user_id=current_user['id'],
        )

        logger.info(
            "program_generated_successfully",
            program_id=program_id,
            user_id=current_user['id'],
            warnings_count=len(warnings),
        )

        return ProgramResponse(
            program_id=program_id,
            user_id=current_user['id'],
            primary_goal=program_bundle.primary_goal,
            program_start_date=program_bundle.created_at.date().isoformat(),
            next_reassessment_date=(
                program_bundle.created_at.date() + timedelta(days=14)
            ).isoformat(),
            training_sessions_per_week=program_bundle.training_plan.sessions_per_week,
            daily_calorie_target=program_bundle.target_calories_kcal,
            macro_targets=program_bundle.macro_targets,
            message=f"Program generated successfully! {len(warnings)} warnings." if warnings else "Program generated successfully!",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("generate_program_failed", error=str(e), user_id=current_user['id'], exc_info=True)
        raise HTTPException(status_code=500, detail=f"Program generation failed: {str(e)}")


@router.get("/programs/current")
async def get_current_program(
    current_user: dict = Depends(get_current_user),
):
    """
    Get the user's current active program.

    Returns:
        - Program summary (goals, targets, schedule)
        - Training plan (weekly sessions)
        - Nutrition plan (daily meals)
        - Next reassessment date
    """
    logger.info("get_current_program", user_id=current_user['id'])

    storage_service = ProgramStorageService()

    try:
        client = storage_service.db.client

        # Fetch current active program
        result = (
            client.table("programs")
            .select("*")
            .eq("user_id", current_user['id'])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="No program found. Generate a program first.",
            )

        program = result.data[0]

        # Fetch training sessions
        sessions_result = (
            client.table("session_instances")
            .select("*, exercise_plan_items(*)")
            .eq("program_id", program["id"])
            .eq("week_index", 0)  # Current week
            .order("day_index")
            .execute()
        )

        # Fetch meal plan for current week
        meals_result = (
            client.table("meal_instances")
            .select("*, meal_item_plan(*)")
            .eq("program_id", program["id"])
            .eq("week_index", 0)
            .order("day_index, order_index")
            .execute()
        )

        return {
            "program_id": program["id"],
            "primary_goal": program["primary_goal"],
            "program_start_date": program["program_start_date"],
            "next_reassessment_date": program["next_reassessment_date"],
            "tdee": program["tdee"],
            "macros": program["macros"],
            "training_sessions": sessions_result.data,
            "meals": meals_result.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_current_program_failed", error=str(e), user_id=current_user['id'])
        raise HTTPException(status_code=500, detail=f"Failed to fetch program: {e}")


@router.get("/programs/today")
async def get_todays_plan(
    current_user: dict = Depends(get_current_user),
):
    """
    Get today's planned sessions and meals.

    Returns:
        - Training session (if scheduled today)
        - Meals (breakfast, lunch, dinner, snacks)
        - Macro targets for today
        - Any day overrides (adjustments)
    """
    from datetime import date

    logger.info("get_todays_plan", user_id=current_user['id'])

    storage_service = ProgramStorageService()

    try:
        client = storage_service.db.client
        today = date.today()

        # Fetch today's calendar events
        events_result = (
            client.table("calendar_events")
            .select("*")
            .eq("user_id", current_user['id'])
            .eq("date", today.isoformat())
            .execute()
        )

        # Fetch any day overrides for today
        overrides_result = (
            client.table("day_overrides")
            .select("*")
            .eq("user_id", current_user['id'])
            .eq("date", today.isoformat())
            .execute()
        )

        return {
            "date": today.isoformat(),
            "events": events_result.data,
            "overrides": overrides_result.data,
        }

    except Exception as e:
        logger.error("get_todays_plan_failed", error=str(e), user_id=current_user['id'])
        raise HTTPException(status_code=500, detail=f"Failed to fetch today's plan: {e}")


@router.get("/programs/current-week")
async def get_current_program_week(
    current_user: dict = Depends(get_current_user),
):
    """
    Get current week and day index within the active program.

    Returns:
        - current_week: Week number (0-indexed)
        - current_day: Day of week (0-6, Monday=0)
        - total_weeks: Program duration
        - days_elapsed: Total days since program start
        - completion_percentage: Progress through program
    """
    from datetime import date

    logger.info("get_current_program_week", user_id=current_user['id'])

    storage_service = ProgramStorageService()

    try:
        client = storage_service.db.client

        # Get current active program
        program_result = (
            client.table("programs")
            .select("*")
            .eq("user_id", current_user['id'])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not program_result.data:
            raise HTTPException(
                status_code=404,
                detail="No program found. Generate a program first.",
            )

        program = program_result.data[0]
        start_date = date.fromisoformat(program["program_start_date"])
        total_weeks = program["program_duration_weeks"]

        # Calculate current position
        today = date.today()
        days_elapsed = (today - start_date).days

        # Handle negative days (program hasn't started yet)
        if days_elapsed < 0:
            current_week = 0
            current_day = 0
            completion_percentage = 0.0
        else:
            current_week = days_elapsed // 7
            current_day = days_elapsed % 7

            # Calculate completion percentage
            total_days = total_weeks * 7
            completion_percentage = min(100.0, (days_elapsed / total_days) * 100) if total_days > 0 else 0.0

        # Check if program is complete
        is_complete = days_elapsed >= (total_weeks * 7)

        return {
            "program_id": program["id"],
            "start_date": program["program_start_date"],
            "current_week": current_week,
            "current_day": current_day,
            "total_weeks": total_weeks,
            "days_elapsed": days_elapsed,
            "completion_percentage": round(completion_percentage, 1),
            "is_complete": is_complete,
            "status": "completed" if is_complete else "active",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_current_program_week_failed", error=str(e), user_id=current_user['id'])
        raise HTTPException(status_code=500, detail=f"Failed to get program week: {e}")
