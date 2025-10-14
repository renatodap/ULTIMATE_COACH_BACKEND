"""
Programs API Router

DROP-IN FILE for ULTIMATE_COACH_BACKEND/app/api/v1/programs.py

Provides endpoints for:
- Generating initial programs from consultation data
- Retrieving active plans
- Getting today's specific plan
- Triggering reassessments
- Viewing progress

Installation:
1. Copy this file to: ULTIMATE_COACH_BACKEND/app/api/v1/programs.py
2. In ULTIMATE_COACH_BACKEND/app/main.py, add:
   from app.api.v1 import programs
   app.include_router(programs.router, prefix="/api/v1")
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging

# Import from standalone service
from ultimate_ai_consultation.services.program_generator import (
    PlanGenerator,
    UserProfile,
    ExperienceLevel,
    IntensityZone,
    DietaryPreference,
    GroceryListGenerator,
)
from ultimate_ai_consultation.libs.calculators.macros import Goal
from ultimate_ai_consultation.libs.calculators.tdee import ActivityFactor
from ultimate_ai_consultation.services.adaptive import ReassessmentOrchestrator

# Import from your existing backend
# Adjust these imports to match your actual backend structure
try:
    from app.core.deps import get_current_user, get_supabase_client
    from app.services.unified_coach_service import send_coach_message
    from app.core.notifications import send_push_notification
except ImportError:
    # Fallback for testing
    def get_current_user():
        return {"id": "test-user"}

    def get_supabase_client():
        return None

    async def send_coach_message(user_id: str, content: str):
        print(f"Would send to {user_id}: {content}")

    async def send_push_notification(user_id: str, title: str, body: str, data: dict):
        print(f"Would push to {user_id}: {title}")


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/programs", tags=["programs"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class GenerateProgramRequest(BaseModel):
    """Request body for program generation"""
    user_id: str
    consultation_data: Dict[str, Any] = Field(
        ...,
        description="Complete consultation data from ConsultationAIService"
    )


class ProgramSummary(BaseModel):
    """Summary of generated program"""
    plan_id: str
    version: int
    goal: str
    training_sessions_per_week: int
    daily_calorie_target: int
    macro_targets: Dict[str, int]
    warnings: List[str] = []


class TodayPlanResponse(BaseModel):
    """Today's specific workout and meals"""
    plan_version: int
    day_number: int
    day_of_week: int
    is_training_day: bool
    workout: Optional[Dict[str, Any]] = None
    meals: List[Dict[str, Any]]
    targets: Dict[str, int]


class ProgressResponse(BaseModel):
    """Progress summary"""
    period_days: int
    meal_adherence: float
    workout_adherence: float
    meals_logged: int
    workouts_completed: int
    weight_change_kg: float
    weight_data: List[Dict[str, Any]]
    avg_calories: float
    avg_protein: float
    avg_carbs: float
    avg_fat: float


# ============================================================================
# ENDPOINT 1: GENERATE INITIAL PROGRAM
# ============================================================================

@router.post("/generate", response_model=ProgramSummary)
async def generate_initial_program(
    request: GenerateProgramRequest,
    supabase=Depends(get_supabase_client)
):
    """
    Generate complete 14-day program from consultation data.

    This is called automatically after consultation completion or manually.

    Steps:
    1. Convert consultation data to UserProfile
    2. Generate complete plan (Phase 1)
    3. Store in plan_versions table
    4. Generate grocery list
    5. Send welcome message via UnifiedCoach
    6. Return summary

    Raises:
        HTTPException 400: If plan is unsafe or infeasible
        HTTPException 500: If system error occurs
    """
    logger.info(f"Generating program for user {request.user_id}")

    try:
        # Step 1: Convert consultation data to UserProfile
        profile = _convert_consultation_to_profile(
            request.user_id,
            request.consultation_data
        )

        # Step 2: Generate complete plan
        generator = PlanGenerator()
        plan, warnings = generator.generate_complete_plan(profile)

        logger.info(f"Plan generated successfully for user {request.user_id}")

        # Step 3: Export to JSON
        plan_json = json.loads(generator.export_plan_to_json(plan))

        # Step 4: Store in database
        result = supabase.table("plan_versions").insert({
            "user_id": request.user_id,
            "version": 1,
            "plan_data": plan_json,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }).execute()

        logger.info(f"Plan stored in database for user {request.user_id}")

        # Step 5: Generate grocery list
        grocery_gen = GroceryListGenerator()
        grocery_list = grocery_gen.generate_grocery_list(plan.meal_plans)

        # Step 6: Send welcome message via UnifiedCoach
        await send_coach_message(
            user_id=request.user_id,
            content=f"""🎉 Your personalized program is ready!

**Your Plan:**
• Goal: {plan.goal.value.replace('_', ' ').title()}
• Training: {plan.training_sessions_per_week}x per week ({plan.training_program.split_type.value.replace('_', ' ').title()})
• Nutrition: {plan.daily_calorie_target} kcal/day ({plan.macro_targets.protein_g}P/{plan.macro_targets.carbs_g}C/{plan.macro_targets.fat_g}F)

**Grocery List:** ${grocery_list.total_estimated_cost_usd:.2f} for 2 weeks

**What's Next:**
1. Tap "My Program" to see today's plan
2. Review your grocery list
3. Start your first workout!

I'll check in with you every 2 weeks to adjust based on your progress. Let's do this! 💪"""
        )

        return ProgramSummary(
            plan_id=plan.plan_id,
            version=1,
            goal=plan.goal.value,
            training_sessions_per_week=plan.training_sessions_per_week,
            daily_calorie_target=plan.daily_calorie_target,
            macro_targets={
                "protein_g": plan.macro_targets.protein_g,
                "carbs_g": plan.macro_targets.carbs_g,
                "fat_g": plan.macro_targets.fat_g,
            },
            warnings=warnings
        )

    except ValueError as e:
        # Plan is unsafe or infeasible
        logger.warning(f"Plan generation failed for user {request.user_id}: {e}")

        # Send message to user explaining the issue
        await send_coach_message(
            user_id=request.user_id,
            content=f"""I need to clarify a few things before creating your plan:

{str(e)}

Let's adjust your goals to make sure we create a safe, effective program for you. What would you like to modify?"""
        )

        raise HTTPException(
            status_code=400,
            detail={
                "error": "plan_generation_failed",
                "message": str(e),
                "user_message": "We need to adjust your goals to create a safe plan. Check your coach messages."
            }
        )

    except Exception as e:
        logger.error(f"System error generating plan for user {request.user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "system_error",
                "message": "An unexpected error occurred. Our team has been notified."
            }
        )


# ============================================================================
# ENDPOINT 2: GET ACTIVE PLAN
# ============================================================================

@router.get("/{user_id}/active")
async def get_active_plan(
    user_id: str,
    supabase=Depends(get_supabase_client)
):
    """
    Get user's current active plan with all details.

    Returns complete plan JSON from plan_versions table.
    """
    try:
        result = supabase.table("plan_versions")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .maybe_single()\
            .execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="No active plan found. Complete consultation first."
            )

        return result.data

    except Exception as e:
        if "404" in str(e):
            raise
        logger.error(f"Error fetching active plan for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch plan")


# ============================================================================
# ENDPOINT 3: GET TODAY'S PLAN
# ============================================================================

@router.get("/{user_id}/today", response_model=TodayPlanResponse)
async def get_today_plan(
    user_id: str,
    supabase=Depends(get_supabase_client)
):
    """
    Get today's specific workout and meal plan.

    Determines:
    - Which day of 14-day cycle (1-14)
    - Which day of week (0-6)
    - If training day based on split
    - Today's workout session (if training day)
    - Today's meals

    This endpoint is optimized for daily app usage.
    """
    try:
        # Fetch active plan
        plan_result = supabase.table("plan_versions")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .maybe_single()\
            .execute()

        if not plan_result.data:
            raise HTTPException(status_code=404, detail="No active plan found")

        plan = plan_result.data
        plan_data = plan['plan_data']

        # Calculate which day of 14-day cycle
        plan_start = datetime.fromisoformat(plan['created_at'])
        days_elapsed = (datetime.now() - plan_start).days
        day_number = (days_elapsed % 14) + 1

        # Get day of week (0=Monday, 6=Sunday)
        day_of_week = datetime.now().weekday()

        # Determine if training day
        training_program = plan_data['training_program']
        sessions_per_week = training_program['sessions_per_week']

        # Map sessions/week to training days
        training_schedules = {
            2: {0, 3},  # Mon, Thu
            3: {0, 2, 4},  # Mon, Wed, Fri
            4: {0, 1, 3, 4},  # Mon, Tue, Thu, Fri
            5: {0, 1, 2, 4, 5},  # Mon-Wed, Fri-Sat
            6: {0, 1, 2, 3, 4, 5},  # Mon-Sat
        }

        training_days = training_schedules.get(sessions_per_week, {0, 2, 4})
        is_training_day = day_of_week in training_days

        # Get today's workout
        today_workout = None
        if is_training_day:
            sessions = training_program['weekly_sessions']
            session_index = day_of_week % len(sessions)
            today_workout = sessions[session_index]

        # Get today's meals
        meal_plans = plan_data['meal_plans']
        today_meals = next(
            (m for m in meal_plans if m['day_number'] == day_number),
            meal_plans[0]  # Fallback to day 1 if not found
        )

        return TodayPlanResponse(
            plan_version=plan['version'],
            day_number=day_number,
            day_of_week=day_of_week,
            is_training_day=is_training_day,
            workout=today_workout,
            meals=today_meals['meals'],
            targets={
                "calories": plan_data['daily_calorie_target'],
                "protein": plan_data['macro_targets']['protein_g'],
                "carbs": plan_data['macro_targets']['carbs_g'],
                "fat": plan_data['macro_targets']['fat_g'],
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching today's plan for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch today's plan")


# ============================================================================
# ENDPOINT 4: TRIGGER REASSESSMENT
# ============================================================================

@router.post("/{user_id}/reassess")
async def trigger_reassessment(
    user_id: str,
    background_tasks: BackgroundTasks,
    supabase=Depends(get_supabase_client)
):
    """
    Manually trigger bi-weekly reassessment.

    Runs in background to avoid timeout.
    Used for: admin panel, user request, testing.

    The actual reassessment happens asynchronously.
    """
    # Get current plan version
    plan_result = supabase.table("plan_versions")\
        .select("version")\
        .eq("user_id", user_id)\
        .eq("status", "active")\
        .maybe_single()\
        .execute()

    if not plan_result.data:
        raise HTTPException(status_code=404, detail="No active plan found")

    current_version = plan_result.data['version']

    # Schedule reassessment in background
    background_tasks.add_task(
        run_reassessment_task,
        user_id=user_id,
        plan_version=current_version,
        supabase=supabase
    )

    return {
        "status": "scheduled",
        "message": "Reassessment started. You'll be notified when complete.",
        "current_version": current_version
    }


async def run_reassessment_task(user_id: str, plan_version: int, supabase):
    """Background task for running reassessment"""
    try:
        logger.info(f"Running reassessment for user {user_id}, version {plan_version}")

        orchestrator = ReassessmentOrchestrator(supabase)
        result = await orchestrator.run_reassessment(
            user_id=user_id,
            plan_version=plan_version,
            manual_trigger=True
        )

        # Send notification
        await send_push_notification(
            user_id=user_id,
            title="Your Plan Has Been Updated!",
            body="Check your progress and new targets.",
            data={"screen": "Progress", "plan_version": result.new_plan_version}
        )

        # Send coach message with results
        await send_coach_message(
            user_id=user_id,
            content=result.user_message
        )

        logger.info(f"Reassessment completed for user {user_id}")

    except Exception as e:
        logger.error(f"Reassessment failed for user {user_id}: {e}", exc_info=True)

        # Notify user of failure
        await send_coach_message(
            user_id=user_id,
            content="I had trouble updating your plan. Let me try again later, or you can contact support if this persists."
        )


# ============================================================================
# ENDPOINT 5: GET PROGRESS
# ============================================================================

@router.get("/{user_id}/progress", response_model=ProgressResponse)
async def get_progress_summary(
    user_id: str,
    days: int = 14,
    supabase=Depends(get_supabase_client)
):
    """
    Get progress metrics for last N days.

    Aggregates:
    - Meal logging adherence
    - Workout completion rate
    - Weight change
    - Average daily macros
    """
    try:
        start_date = datetime.now() - timedelta(days=days)

        # Query logged data
        meals = supabase.table("meals")\
            .select("*")\
            .eq("user_id", user_id)\
            .gte("created_at", start_date.isoformat())\
            .execute()

        activities = supabase.table("activities")\
            .select("*")\
            .eq("user_id", user_id)\
            .gte("created_at", start_date.isoformat())\
            .execute()

        body_metrics = supabase.table("body_metrics")\
            .select("*")\
            .eq("user_id", user_id)\
            .gte("recorded_at", start_date.isoformat())\
            .order("recorded_at")\
            .execute()

        # Calculate meal adherence
        unique_meal_days = len(set(m['created_at'][:10] for m in meals.data)) if meals.data else 0
        meal_adherence = unique_meal_days / days if days > 0 else 0

        # Calculate workout adherence
        workout_days = len(set(a['created_at'][:10] for a in activities.data if a.get('activity_type') == 'workout')) if activities.data else 0
        expected_workouts = days * 5 / 7  # Assume 5x/week
        workout_adherence = min(workout_days / expected_workouts, 1.0) if expected_workouts > 0 else 0

        # Calculate weight change
        weights = [(m['recorded_at'], m.get('weight_kg', 0)) for m in body_metrics.data if m.get('weight_kg')]
        weight_change = weights[-1][1] - weights[0][1] if len(weights) >= 2 else 0

        # Calculate average macros
        total_calories = sum(m.get('calories', 0) for m in meals.data)
        total_protein = sum(m.get('protein_g', 0) for m in meals.data)
        total_carbs = sum(m.get('carbs_g', 0) for m in meals.data)
        total_fat = sum(m.get('fat_g', 0) for m in meals.data)

        meal_count = len(meals.data) if meals.data else 1

        return ProgressResponse(
            period_days=days,
            meal_adherence=meal_adherence,
            workout_adherence=workout_adherence,
            meals_logged=len(meals.data),
            workouts_completed=len([a for a in activities.data if a.get('activity_type') == 'workout']),
            weight_change_kg=weight_change,
            weight_data=[{"date": w[0], "weight_kg": w[1]} for w in weights],
            avg_calories=total_calories / meal_count,
            avg_protein=total_protein / meal_count,
            avg_carbs=total_carbs / meal_count,
            avg_fat=total_fat / meal_count
        )

    except Exception as e:
        logger.error(f"Error fetching progress for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch progress")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _convert_consultation_to_profile(user_id: str, data: Dict[str, Any]) -> UserProfile:
    """Convert consultation data to UserProfile for plan generation"""

    # Map string values to enums
    goal_map = {
        "fat_loss": Goal.FAT_LOSS,
        "muscle_gain": Goal.MUSCLE_GAIN,
        "recomp": Goal.RECOMP,
        "maintenance": Goal.MAINTENANCE,
    }

    activity_map = {
        "sedentary": ActivityFactor.SEDENTARY,
        "lightly_active": ActivityFactor.LIGHTLY_ACTIVE,
        "moderately_active": ActivityFactor.MODERATELY_ACTIVE,
        "very_active": ActivityFactor.VERY_ACTIVE,
        "extra_active": ActivityFactor.EXTRA_ACTIVE,
    }

    experience_map = {
        "beginner": ExperienceLevel.BEGINNER,
        "intermediate": ExperienceLevel.INTERMEDIATE,
        "advanced": ExperienceLevel.ADVANCED,
    }

    intensity_map = {
        "strength": IntensityZone.STRENGTH,
        "hypertrophy": IntensityZone.HYPERTROPHY,
        "endurance": IntensityZone.ENDURANCE,
    }

    diet_map = {
        "none": DietaryPreference.NONE,
        "vegetarian": DietaryPreference.VEGETARIAN,
        "vegan": DietaryPreference.VEGAN,
        "pescatarian": DietaryPreference.PESCATARIAN,
    }

    return UserProfile(
        user_id=user_id,
        age=data['age'],
        sex_at_birth=data['sex'],
        weight_kg=data['weight'],
        height_cm=data['height'],
        body_fat_percentage=data.get('body_fat'),

        # Goals
        primary_goal=goal_map.get(data['goal'].lower(), Goal.MAINTENANCE),
        target_weight_kg=data.get('target_weight'),
        timeline_weeks=data.get('timeline', 12),

        # Training
        sessions_per_week=data['training_frequency'],
        experience_level=experience_map.get(data['experience'].lower(), ExperienceLevel.INTERMEDIATE),
        training_focus=intensity_map.get(data.get('focus', 'hypertrophy').lower(), IntensityZone.HYPERTROPHY),
        available_days=data.get('available_days', ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']),

        # Nutrition
        dietary_preference=diet_map.get(data.get('diet_type', 'none').lower(), DietaryPreference.NONE),
        food_allergies=data.get('allergies', []),
        activity_factor=activity_map.get(data.get('activity_level', 'moderately_active').lower(), ActivityFactor.MODERATELY_ACTIVE),

        # Medical
        medical_conditions=data.get('medical_conditions', []),
        medications=data.get('medications', []),
        injuries=data.get('injuries', []),
        doctor_clearance=data.get('has_doctor_clearance', False)
    )


# ============================================================================
# ADDITIONAL ENDPOINTS (Optional but useful)
# ============================================================================

@router.get("/{user_id}/grocery-list")
async def get_grocery_list(
    user_id: str,
    supabase=Depends(get_supabase_client)
):
    """
    Get grocery list for user's current plan.

    The grocery list is generated and stored during plan creation.
    This endpoint retrieves it from the database.
    """
    plan = await get_active_plan(user_id, supabase)

    # Grocery list is stored in plan_data during generation
    grocery_data = plan['plan_data'].get('grocery_list')

    if not grocery_data:
        raise HTTPException(
            status_code=404,
            detail="Grocery list not found. This may be an older plan. Try regenerating your program."
        )

    return grocery_data


@router.get("/{user_id}/plan-history")
async def get_plan_history(
    user_id: str,
    supabase=Depends(get_supabase_client)
):
    """Get all plan versions and adjustments for user"""
    # Get all plan versions for this user
    versions = supabase.table("plan_versions")\
        .select("id, version, created_at, status")\
        .eq("user_id", user_id)\
        .order("version", desc=True)\
        .execute()

    # Get plan IDs to query adjustments
    plan_ids = [v['id'] for v in versions.data] if versions.data else []

    # Get adjustments for all user's plans
    if plan_ids:
        adjustments = supabase.table("plan_adjustments")\
            .select("*")\
            .in_("plan_id", plan_ids)\
            .order("created_at", desc=True)\
            .execute()
    else:
        adjustments = type('obj', (object,), {'data': []})()  # Empty result

    return {
        "versions": versions.data,
        "adjustments": adjustments.data
    }
