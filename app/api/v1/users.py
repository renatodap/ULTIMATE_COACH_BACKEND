"""
User profile API endpoints.

Handles user profile operations (requires authentication).
"""

import structlog
from fastapi import APIRouter, HTTPException, status, Depends, Form
from fastapi.responses import JSONResponse
from typing import Optional

from app.api.dependencies import get_current_user
from app.services.supabase_service import supabase_service
from uuid import UUID

logger = structlog.get_logger()

router = APIRouter()


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Get the authenticated user's complete profile data",
)
async def get_my_profile(user: dict = Depends(get_current_user)) -> JSONResponse:
    """
    Get current authenticated user's complete profile.

    Returns ALL profile data including onboarding responses, macro targets,
    and consultation status.

    Args:
        user: Current authenticated user (injected by dependency)

    Returns:
        Complete user profile data
    """
    try:
        user_id = UUID(user["id"])
        profile = await supabase_service.get_profile(user_id)

        if not profile:
            logger.error("profile_not_found", user_id=str(user_id))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        # Resolve latest body metrics for display
        latest_metric = await supabase_service.get_latest_body_metric(user_id)
        resolved_weight = latest_metric.get('weight_kg') if latest_metric else profile.get("current_weight_kg")
        resolved_height = latest_metric.get('height_cm') if latest_metric else profile.get("height_cm")

        logger.info("profile_retrieved", user_id=str(user_id))

        # Return complete profile with all fields
        return JSONResponse(content={
            # Basic info
            "id": user["id"],
            "email": user["email"],
            "full_name": profile.get("full_name"),
            "created_at": profile.get("created_at"),
            "updated_at": profile.get("updated_at"),

            # Onboarding status
            "onboarding_completed": profile.get("onboarding_completed", False),
            "onboarding_completed_at": profile.get("onboarding_completed_at"),

            # Physical stats
            "age": profile.get("age"),
            "biological_sex": profile.get("biological_sex"),
            "height_cm": resolved_height,
            "current_weight_kg": resolved_weight,
            "goal_weight_kg": profile.get("goal_weight_kg"),

            # Goals & Training
            "primary_goal": profile.get("primary_goal"),
            "experience_level": profile.get("experience_level"),
            "activity_level": profile.get("activity_level"),
            "workout_frequency": profile.get("workout_frequency"),

            # Dietary
            "dietary_preference": profile.get("dietary_preference"),
            "food_allergies": profile.get("food_allergies", []),
            "foods_to_avoid": profile.get("foods_to_avoid", []),
            "meals_per_day": profile.get("meals_per_day"),
            "cooks_regularly": profile.get("cooks_regularly"),

            # Lifestyle
            "sleep_hours": profile.get("sleep_hours"),
            "stress_level": profile.get("stress_level"),

            # Macro targets
            "estimated_tdee": profile.get("estimated_tdee"),
            "daily_calorie_goal": profile.get("daily_calorie_goal"),
            "daily_protein_goal": profile.get("daily_protein_goal"),
            "daily_carbs_goal": profile.get("daily_carbs_goal"),
            "daily_fat_goal": profile.get("daily_fat_goal"),
            "macros_last_calculated_at": profile.get("macros_last_calculated_at"),

            # Preferences
            "unit_system": profile.get("unit_system", "imperial"),
            "timezone": profile.get("timezone", "America/New_York"),

            # Consultation
            "consultation_completed": profile.get("consultation_completed", False),
            "consultation_completed_at": profile.get("consultation_completed_at"),
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error("profile_retrieval_error", user_id=user["id"], error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile",
        )


@router.patch(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Update the authenticated user's profile data with automatic macro recalculation",
)
async def update_my_profile(
    full_name: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    height_cm: Optional[float] = Form(None),
    current_weight_kg: Optional[float] = Form(None),
    goal_weight_kg: Optional[float] = Form(None),
    primary_goal: Optional[str] = Form(None),
    experience_level: Optional[str] = Form(None),
    activity_level: Optional[str] = Form(None),
    workout_frequency: Optional[int] = Form(None),
    dietary_preference: Optional[str] = Form(None),
    food_allergies: Optional[str] = Form(None),  # Accepts JSON string from form data
    foods_to_avoid: Optional[str] = Form(None),  # Accepts JSON string from form data
    meals_per_day: Optional[int] = Form(None),
    cooks_regularly: Optional[bool] = Form(None),
    sleep_hours: Optional[float] = Form(None),
    stress_level: Optional[str] = Form(None),
    unit_system: Optional[str] = Form(None),
    timezone: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
) -> JSONResponse:
    """
    Update current authenticated user's profile.

    If physical stats or activity level changes, macros are automatically recalculated.

    Args:
        full_name: New full name
        age: Age in years
        height_cm: Height in cm
        current_weight_kg: Current weight in kg
        goal_weight_kg: Goal weight in kg
        primary_goal: Primary fitness goal
        experience_level: Training experience
        activity_level: Daily activity level
        workout_frequency: Workouts per week
        dietary_preference: Dietary restrictions
        food_allergies: List of food allergies
        foods_to_avoid: List of foods to avoid
        meals_per_day: Meals per day
        cooks_regularly: Whether user cooks regularly
        sleep_hours: Sleep hours per night
        stress_level: Stress level
        unit_system: Preferred unit system
        timezone: User timezone
        user: Current authenticated user

    Returns:
        Updated profile with recalculated macros if applicable
    """
    try:
        import json
        from app.services.macro_calculator import calculate_targets
        from datetime import datetime

        user_id = UUID(user["id"])

        # Get current profile to check for changes
        current_profile = await supabase_service.get_profile(user_id)
        if not current_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        # Parse JSON arrays from form data
        parsed_food_allergies = None
        parsed_foods_to_avoid = None

        if food_allergies is not None:
            try:
                parsed_food_allergies = json.loads(food_allergies)
                if not isinstance(parsed_food_allergies, list):
                    raise ValueError("food_allergies must be a list")
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning("invalid_food_allergies_format", error=str(e), value=food_allergies)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid format for food_allergies. Expected JSON array."
                )

        if foods_to_avoid is not None:
            try:
                parsed_foods_to_avoid = json.loads(foods_to_avoid)
                if not isinstance(parsed_foods_to_avoid, list):
                    raise ValueError("foods_to_avoid must be a list")
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning("invalid_foods_to_avoid_format", error=str(e), value=foods_to_avoid)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid format for foods_to_avoid. Expected JSON array."
                )

        # Build update data
        update_data = {}
        if full_name is not None:
            update_data["full_name"] = full_name
        if age is not None:
            update_data["age"] = age
        if height_cm is not None:
            update_data["height_cm"] = height_cm
        if current_weight_kg is not None:
            update_data["current_weight_kg"] = current_weight_kg
        if goal_weight_kg is not None:
            update_data["goal_weight_kg"] = goal_weight_kg
        if primary_goal is not None:
            update_data["primary_goal"] = primary_goal
        if experience_level is not None:
            update_data["experience_level"] = experience_level
        if activity_level is not None:
            update_data["activity_level"] = activity_level
        if workout_frequency is not None:
            update_data["workout_frequency"] = workout_frequency
        if dietary_preference is not None:
            update_data["dietary_preference"] = dietary_preference
        if parsed_food_allergies is not None:
            update_data["food_allergies"] = parsed_food_allergies
        if parsed_foods_to_avoid is not None:
            update_data["foods_to_avoid"] = parsed_foods_to_avoid
        if meals_per_day is not None:
            update_data["meals_per_day"] = meals_per_day
        if cooks_regularly is not None:
            update_data["cooks_regularly"] = cooks_regularly
        if sleep_hours is not None:
            update_data["sleep_hours"] = sleep_hours
        if stress_level is not None:
            update_data["stress_level"] = stress_level
        if unit_system is not None:
            update_data["unit_system"] = unit_system
        if timezone is not None:
            update_data["timezone"] = timezone

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        # Check if we need to recalculate macros
        macro_affecting_fields = {'age', 'height_cm', 'current_weight_kg', 'goal_weight_kg',
                                   'primary_goal', 'activity_level', 'experience_level'}
        needs_macro_recalc = any(field in update_data for field in macro_affecting_fields)

        if needs_macro_recalc:
            # Get values (updated or current)
            calc_age = update_data.get('age', current_profile.get('age'))
            calc_sex = current_profile.get('biological_sex')
            calc_height = update_data.get('height_cm', current_profile.get('height_cm'))
            calc_current_weight = update_data.get('current_weight_kg', current_profile.get('current_weight_kg'))
            calc_goal_weight = update_data.get('goal_weight_kg', current_profile.get('goal_weight_kg'))
            calc_activity = update_data.get('activity_level', current_profile.get('activity_level'))
            calc_goal = update_data.get('primary_goal', current_profile.get('primary_goal'))
            calc_experience = update_data.get('experience_level', current_profile.get('experience_level'))

            # Validate required fields
            if not all([calc_age, calc_sex, calc_height, calc_current_weight,
                       calc_goal_weight, calc_activity, calc_goal]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing required fields for macro calculation",
                )

            # Recalculate macros
            targets = calculate_targets(
                age=calc_age,
                sex=calc_sex,
                height_cm=calc_height,
                current_weight_kg=calc_current_weight,
                goal_weight_kg=calc_goal_weight,
                activity_level=calc_activity,
                primary_goal=calc_goal,
                experience_level=calc_experience
            )

            # Add macro targets to update
            update_data["estimated_tdee"] = targets.tdee
            update_data["daily_calorie_goal"] = targets.daily_calories
            update_data["daily_protein_goal"] = targets.daily_protein_g
            update_data["daily_carbs_goal"] = targets.daily_carbs_g
            update_data["daily_fat_goal"] = targets.daily_fat_g
            update_data["macros_last_calculated_at"] = datetime.utcnow().isoformat()
            update_data["macros_calculation_reason"] = "profile_update"

            logger.info("macros_recalculated", user_id=str(user_id),
                       calories=targets.daily_calories, protein=targets.daily_protein_g)

        # Update profile
        updated_profile = await supabase_service.update_profile(user_id, update_data)

        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        logger.info("profile_updated", user_id=str(user_id),
                   fields=list(update_data.keys()), macro_recalc=needs_macro_recalc)

        # If weight and/or height were provided, create a new body metrics log (weight required for schema)
        try:
            metric: dict = {
                'user_id': str(user_id),
                'recorded_at': datetime.utcnow().isoformat(),
                'notes': 'Profile edit',
            }
            provided_weight = False
            if 'current_weight_kg' in update_data and update_data['current_weight_kg'] is not None:
                metric['weight_kg'] = float(update_data['current_weight_kg'])
                provided_weight = True
            if 'height_cm' in update_data and update_data['height_cm'] is not None:
                metric['height_cm'] = float(update_data['height_cm'])
            if provided_weight:
                await supabase_service.create_body_metric(metric)
                logger.info("body_metric_logged_from_profile_edit", user_id=str(user_id), fields=list(metric.keys()))
        except Exception as e:
            logger.warning("body_metric_log_failed", user_id=str(user_id), error=str(e))

        # Return complete updated profile
        return JSONResponse(content={
            "id": user["id"],
            "email": user["email"],
            "full_name": updated_profile.get("full_name"),
            "age": updated_profile.get("age"),
            "biological_sex": updated_profile.get("biological_sex"),
            "height_cm": updated_profile.get("height_cm"),
            "current_weight_kg": updated_profile.get("current_weight_kg"),
            "goal_weight_kg": updated_profile.get("goal_weight_kg"),
            "primary_goal": updated_profile.get("primary_goal"),
            "experience_level": updated_profile.get("experience_level"),
            "activity_level": updated_profile.get("activity_level"),
            "workout_frequency": updated_profile.get("workout_frequency"),
            "dietary_preference": updated_profile.get("dietary_preference"),
            "food_allergies": updated_profile.get("food_allergies", []),
            "foods_to_avoid": updated_profile.get("foods_to_avoid", []),
            "meals_per_day": updated_profile.get("meals_per_day"),
            "cooks_regularly": updated_profile.get("cooks_regularly"),
            "sleep_hours": updated_profile.get("sleep_hours"),
            "stress_level": updated_profile.get("stress_level"),
            "estimated_tdee": updated_profile.get("estimated_tdee"),
            "daily_calorie_goal": updated_profile.get("daily_calorie_goal"),
            "daily_protein_goal": updated_profile.get("daily_protein_goal"),
            "daily_carbs_goal": updated_profile.get("daily_carbs_goal"),
            "daily_fat_goal": updated_profile.get("daily_fat_goal"),
            "macros_last_calculated_at": updated_profile.get("macros_last_calculated_at"),
            "unit_system": updated_profile.get("unit_system", "imperial"),
            "timezone": updated_profile.get("timezone", "America/New_York"),
            "updated_at": updated_profile.get("updated_at"),
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error("profile_update_error", user_id=user["id"], error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )
