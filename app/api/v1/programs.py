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
    Get today's planned training session and meals with full details.

    Returns:
        - date: Today's date (ISO string)
        - program: Basic program info (id, goal, start date)
        - training_session: Full workout details with exercises (or null if rest day)
        - meals: List of meals with food items and macros
        - daily_targets: Calorie and macro targets
    """
    from datetime import date

    logger.info("get_todays_plan", user_id=current_user['id'])

    storage_service = ProgramStorageService()

    try:
        client = storage_service.db.client
        today = date.today()

        # Get current active program
        program_result = (
            client.table("programs")
            .select("id, user_id, primary_goal, program_start_date, program_duration_weeks, tdee, macros")
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
        program_id = program["id"]
        start_date = date.fromisoformat(program["program_start_date"])

        # Calculate current week and day indices
        days_elapsed = (today - start_date).days
        if days_elapsed < 0:
            # Program hasn't started yet - show week 0, day 0
            week_index = 0
            day_index = 0
        else:
            week_index = days_elapsed // 7
            day_index = days_elapsed % 7

        logger.info(
            "calculated_day_indices",
            user_id=current_user['id'],
            week_index=week_index,
            day_index=day_index,
            days_elapsed=days_elapsed
        )

        # Fetch today's training session with exercises
        # Sessions repeat weekly, so we use week_index % total_weeks, but for MVP just use week 0
        session_result = (
            client.table("session_instances")
            .select("*, exercise_plan_items(*)")
            .eq("program_id", program_id)
            .eq("week_index", 0)  # Weekly repeating pattern
            .eq("day_index", day_index)
            .execute()
        )

        training_session = None
        if session_result.data and len(session_result.data) > 0:
            session = session_result.data[0]
            # Format exercises for frontend
            exercises = session.get("exercise_plan_items", [])
            training_session = {
                "id": session["id"],
                "session_kind": session.get("session_kind"),
                "session_name": session.get("session_name"),
                "time_of_day": session.get("time_of_day"),
                "estimated_duration_minutes": session.get("estimated_duration_minutes"),
                "notes": session.get("notes"),
                "state": session.get("state", "planned"),
                "completed_at": session.get("completed_at"),
                "exercises": [
                    {
                        "name": ex["name"],
                        "muscle_groups": ex.get("muscle_groups", []),
                        "sets": ex["sets"],
                        "rep_range": ex.get("rep_range"),
                        "rest_seconds": ex.get("rest_seconds", 120),
                        "rir": ex.get("rir"),
                        "notes": ex.get("notes"),
                    }
                    for ex in sorted(exercises, key=lambda e: e.get("order_index", 0))
                ],
            }

        # Fetch today's meals with food items
        # Meals also repeat weekly for MVP
        meals_result = (
            client.table("meal_instances")
            .select("*, meal_item_plan(*)")
            .eq("program_id", program_id)
            .eq("week_index", 0)  # Weekly repeating pattern
            .eq("day_index", day_index)
            .order("order_index")
            .execute()
        )

        meals = []
        for meal in meals_result.data:
            food_items = meal.get("meal_item_plan", [])
            meals.append({
                "id": meal["id"],
                "meal_type": meal.get("meal_type"),
                "meal_name": meal.get("meal_name"),
                "notes": meal.get("notes"),
                "completed_at": meal.get("completed_at"),
                "totals": meal.get("totals_json", {}),
                "items": [
                    {
                        "food_name": item.get("food_name"),
                        "serving_size": item.get("serving_size"),
                        "serving_unit": item.get("serving_unit"),
                        "calories": item.get("calories"),
                        "protein_g": item.get("protein_g"),
                        "carbs_g": item.get("carbs_g"),
                        "fat_g": item.get("fat_g"),
                    }
                    for item in sorted(food_items, key=lambda f: f.get("order_index", 0))
                ],
            })

        # Extract daily targets
        tdee_data = program.get("tdee", {})
        macros_data = program.get("macros", {})

        return {
            "date": today.isoformat(),
            "program": {
                "id": program_id,
                "primary_goal": program["primary_goal"],
                "program_start_date": program["program_start_date"],
                "duration_weeks": program["program_duration_weeks"],
            },
            "training_session": training_session,
            "meals": meals,
            "daily_targets": {
                "calories": tdee_data.get("tdee_kcal"),
                "protein_g": macros_data.get("protein_g"),
                "carbs_g": macros_data.get("carbs_g"),
                "fat_g": macros_data.get("fat_g"),
            },
            "week_info": {
                "week_index": week_index,
                "day_index": day_index,
                "days_elapsed": days_elapsed,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_todays_plan_failed", error=str(e), user_id=current_user['id'], exc_info=True)
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


@router.get("/programs/week")
async def get_week_schedule(
    current_user: dict = Depends(get_current_user),
):
    """
    Get the full weekly schedule for the current week.

    Returns a 7-day view (Monday-Sunday) with:
        - Training sessions with exercises
        - Meals with food items
        - Rest days indicated by null session
    """
    from datetime import date, timedelta

    logger.info("get_week_schedule", user_id=current_user['id'])

    storage_service = ProgramStorageService()

    try:
        client = storage_service.db.client
        today = date.today()

        # Get current active program
        program_result = (
            client.table("programs")
            .select("id, user_id, primary_goal, program_start_date, program_duration_weeks")
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
        program_id = program["id"]
        start_date = date.fromisoformat(program["program_start_date"])

        # Calculate current week index
        days_elapsed = (today - start_date).days
        if days_elapsed < 0:
            week_index = 0
            current_day_index = 0
        else:
            week_index = days_elapsed // 7
            current_day_index = days_elapsed % 7

        # Calculate week start date (Monday of current week)
        # Python's weekday(): Monday=0, Sunday=6
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)

        logger.info(
            "fetching_week_schedule",
            user_id=current_user['id'],
            week_index=week_index,
            week_start=week_start.isoformat()
        )

        # Fetch all sessions for the week (day_index 0-6)
        # Sessions repeat weekly, so we use week 0
        sessions_result = (
            client.table("session_instances")
            .select("*, exercise_plan_items(*)")
            .eq("program_id", program_id)
            .eq("week_index", 0)  # Weekly repeating pattern
            .execute()
        )

        # Fetch all meals for the week
        meals_result = (
            client.table("meal_instances")
            .select("*, meal_item_plan(*)")
            .eq("program_id", program_id)
            .eq("week_index", 0)  # Weekly repeating pattern
            .execute()
        )

        # Organize sessions by day_index
        sessions_by_day = {}
        for session in sessions_result.data:
            day_idx = session["day_index"]
            exercises = session.get("exercise_plan_items", [])
            sessions_by_day[day_idx] = {
                "id": session["id"],
                "session_kind": session.get("session_kind"),
                "session_name": session.get("session_name"),
                "time_of_day": session.get("time_of_day"),
                "estimated_duration_minutes": session.get("estimated_duration_minutes"),
                "notes": session.get("notes"),
                "state": session.get("state", "planned"),
                "completed_at": session.get("completed_at"),
                "exercise_count": len(exercises),
            }

        # Organize meals by day_index
        meals_by_day = {}
        for meal in meals_result.data:
            day_idx = meal["day_index"]
            if day_idx not in meals_by_day:
                meals_by_day[day_idx] = []
            meals_by_day[day_idx].append({
                "id": meal["id"],
                "meal_type": meal.get("meal_type"),
                "meal_name": meal.get("meal_name"),
                "totals": meal.get("totals_json", {}),
            })

        # Build 7-day schedule
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        schedule = []

        for day_idx in range(7):
            day_date = week_start + timedelta(days=day_idx)
            is_today = day_date == today

            schedule.append({
                "day_index": day_idx,
                "day_name": day_names[day_idx],
                "date": day_date.isoformat(),
                "is_today": is_today,
                "training_session": sessions_by_day.get(day_idx),  # None for rest days
                "meals": meals_by_day.get(day_idx, []),
                "is_rest_day": sessions_by_day.get(day_idx) is None,
            })

        return {
            "week_index": week_index,
            "week_start": week_start.isoformat(),
            "week_end": (week_start + timedelta(days=6)).isoformat(),
            "current_day_index": current_day_index,
            "program": {
                "id": program_id,
                "primary_goal": program["primary_goal"],
                "program_start_date": program["program_start_date"],
                "duration_weeks": program["program_duration_weeks"],
            },
            "schedule": schedule,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_week_schedule_failed", error=str(e), user_id=current_user['id'], exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch week schedule: {e}")


@router.patch("/programs/sessions/{session_id}/complete")
async def mark_session_complete(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Mark a training session as completed.

    Sets completed_at timestamp to current time.
    Once marked complete, the session will show as done in the UI.
    """
    from datetime import datetime

    logger.info("mark_session_complete", user_id=current_user['id'], session_id=session_id)

    storage_service = ProgramStorageService()

    try:
        client = storage_service.db.client

        # Verify ownership by joining with programs table
        session_result = (
            client.table("session_instances")
            .select("id, program_id, session_name, completed_at")
            .eq("id", session_id)
            .single()
            .execute()
        )

        if not session_result.data:
            raise HTTPException(
                status_code=404,
                detail="Session not found",
            )

        session = session_result.data

        # Verify user owns this program
        program_result = (
            client.table("programs")
            .select("id, user_id")
            .eq("id", session["program_id"])
            .eq("user_id", current_user['id'])
            .single()
            .execute()
        )

        if not program_result.data:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized to modify this session",
            )

        # Mark as complete
        update_result = (
            client.table("session_instances")
            .update({"completed_at": datetime.utcnow().isoformat()})
            .eq("id", session_id)
            .execute()
        )

        if not update_result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to mark session complete",
            )

        # Update calendar event status
        try:
            client.table("calendar_events").update({"status": "completed"}).eq("ref_id", session_id).eq("ref_table", "session_instances").execute()
            logger.info("calendar_event_updated", session_id=session_id, status="completed")
        except Exception as e:
            logger.warning("calendar_event_update_failed", error=str(e), session_id=session_id)
            # Don't fail the request if calendar update fails

        logger.info(
            "session_marked_complete",
            user_id=current_user['id'],
            session_id=session_id,
            session_name=session.get("session_name")
        )

        return {
            "success": True,
            "session_id": session_id,
            "completed_at": update_result.data[0]["completed_at"],
            "message": f"Session '{session.get('session_name')}' marked complete",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("mark_session_complete_failed", error=str(e), user_id=current_user['id'], session_id=session_id, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to mark session complete: {e}")


@router.patch("/programs/meals/{meal_id}/complete")
async def mark_meal_complete(
    meal_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Mark a meal as completed.

    Sets completed_at timestamp to current time.
    Once marked complete, the meal will show as done in the UI.
    """
    from datetime import datetime

    logger.info("mark_meal_complete", user_id=current_user['id'], meal_id=meal_id)

    storage_service = ProgramStorageService()

    try:
        client = storage_service.db.client

        # Verify ownership by joining with programs table
        meal_result = (
            client.table("meal_instances")
            .select("id, program_id, meal_name, meal_type, completed_at")
            .eq("id", meal_id)
            .single()
            .execute()
        )

        if not meal_result.data:
            raise HTTPException(
                status_code=404,
                detail="Meal not found",
            )

        meal = meal_result.data

        # Verify user owns this program
        program_result = (
            client.table("programs")
            .select("id, user_id")
            .eq("id", meal["program_id"])
            .eq("user_id", current_user['id'])
            .single()
            .execute()
        )

        if not program_result.data:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized to modify this meal",
            )

        # Mark as complete
        update_result = (
            client.table("meal_instances")
            .update({"completed_at": datetime.utcnow().isoformat()})
            .eq("id", meal_id)
            .execute()
        )

        if not update_result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to mark meal complete",
            )

        # Update calendar event status
        try:
            client.table("calendar_events").update({"status": "completed"}).eq("ref_id", meal_id).eq("ref_table", "meal_instances").execute()
            logger.info("calendar_event_updated", meal_id=meal_id, status="completed")
        except Exception as e:
            logger.warning("calendar_event_update_failed", error=str(e), meal_id=meal_id)
            # Don't fail the request if calendar update fails

        logger.info(
            "meal_marked_complete",
            user_id=current_user['id'],
            meal_id=meal_id,
            meal_name=meal.get("meal_name")
        )

        return {
            "success": True,
            "meal_id": meal_id,
            "completed_at": update_result.data[0]["completed_at"],
            "message": f"{meal.get('meal_type', 'Meal')} marked complete",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("mark_meal_complete_failed", error=str(e), user_id=current_user['id'], meal_id=meal_id, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to mark meal complete: {e}")
