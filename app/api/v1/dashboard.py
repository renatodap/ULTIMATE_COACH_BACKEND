"""
Dashboard API endpoint.

Provides unified dashboard summary aggregating nutrition, activities, and body metrics.
"""

import structlog
from fastapi import APIRouter, Depends, status
from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.models.dashboard import (
    DashboardSummary,
    TodayNutritionSummary,
    TodayActivitySummary,
    WeightProgressSummary,
    WeeklyStats
)
from app.services.nutrition_service import nutrition_service
from app.services.activity_service import activity_service
from app.services.body_metrics_service import body_metrics_service
from app.services.supabase_service import supabase_service
from app.api.dependencies import get_current_user

logger = structlog.get_logger()

router = APIRouter()


@router.get(
    "/dashboard/summary",
    response_model=DashboardSummary,
    status_code=status.HTTP_200_OK,
    summary="Get complete dashboard summary",
    description="Aggregate nutrition, activities, and body metrics for dashboard view"
)
async def get_dashboard_summary(
    current_user: dict = Depends(get_current_user)
):
    """
    Get unified dashboard summary for today.

    Aggregates:
    - Today's nutrition (calories, macros, meals)
    - Today's activities (calories burned, workouts)
    - Weight progress (current, trend, goal)
    - Weekly stats (consistency, averages)

    This single endpoint replaces 6+ separate API calls for better mobile performance.
    """
    try:
        user_id = UUID(current_user["id"])
        today = date.today()

        logger.info(
            "fetching_dashboard_summary",
            user_id=str(user_id),
            date=str(today)
        )

        # Fetch all data in parallel for performance
        import asyncio

        # Get user profile (for goals and display name)
        profile_task = supabase_service.get_profile(user_id)

        # Get today's nutrition stats
        nutrition_task = nutrition_service.get_nutrition_stats(
            user_id=user_id,
            date=today.isoformat()
        )

        # Get today's activity summary
        activity_task = activity_service.get_daily_summary(
            user_id=user_id,
            target_date=today
        )

        # Get weight data
        latest_weight_task = body_metrics_service.get_latest_body_metric(user_id)
        weight_trend_task = body_metrics_service.calculate_weight_trend(user_id, days=7)

        # Get weekly stats (last 7 days)
        week_start = today - timedelta(days=6)  # Today + 6 days back = 7 days total
        weekly_activities_task = activity_service.get_user_activities(
            user_id=user_id,
            start_date=week_start,
            end_date=today,
            limit=100
        )
        weekly_meals_task = nutrition_service.get_user_meals(
            user_id=user_id,
            start_date=datetime.combine(week_start, datetime.min.time()),
            end_date=datetime.combine(today, datetime.max.time().replace(microsecond=0)),
            limit=100
        )

        # Await all tasks
        profile, nutrition_stats, activity_summary, latest_weight, weight_trend, weekly_activities, weekly_meals = await asyncio.gather(
            profile_task,
            nutrition_task,
            activity_task,
            latest_weight_task,
            weight_trend_task,
            weekly_activities_task,
            weekly_meals_task
        )

        # Process nutrition summary
        calories_remaining = None
        if nutrition_stats.calories_goal:
            calories_remaining = int(nutrition_stats.calories_goal - nutrition_stats.calories_consumed)

        nutrition_summary = TodayNutritionSummary(
            calories_consumed=nutrition_stats.calories_consumed,
            calories_goal=nutrition_stats.calories_goal,
            calories_remaining=calories_remaining,
            protein_consumed=nutrition_stats.protein_consumed,
            protein_goal=nutrition_stats.protein_goal,
            carbs_consumed=nutrition_stats.carbs_consumed,
            carbs_goal=nutrition_stats.carbs_goal,
            fat_consumed=nutrition_stats.fat_consumed,
            fat_goal=nutrition_stats.fat_goal,
            meals_count=nutrition_stats.meals_count,
            meals_by_type=nutrition_stats.meals_by_type
        )

        # Process activity summary
        activity_summary_obj = TodayActivitySummary(**activity_summary)

        # Calculate net calories
        net_calories = int(nutrition_stats.calories_consumed) - activity_summary["total_calories_burned"]

        # Process weight progress
        current_weight_kg = None
        goal_weight_kg = profile.get("goal_weight_kg") if profile else None
        latest_recorded_at = None

        if latest_weight:
            current_weight_kg = latest_weight.get("weight_kg")
            latest_recorded_at = latest_weight.get("recorded_at")

        # Calculate progress to goal
        progress_percentage = None
        remaining_kg = None
        if current_weight_kg and goal_weight_kg and profile.get("current_weight_kg"):
            starting_weight = profile.get("current_weight_kg")
            total_to_lose = abs(starting_weight - goal_weight_kg)
            lost_so_far = abs(starting_weight - current_weight_kg)

            if total_to_lose > 0:
                progress_percentage = round((lost_so_far / total_to_lose) * 100, 1)

            remaining_kg = round(abs(current_weight_kg - goal_weight_kg), 1)

        weight_summary = WeightProgressSummary(
            current_weight=current_weight_kg,
            goal_weight=goal_weight_kg,
            latest_recorded_at=latest_recorded_at,
            previous_weight=weight_trend.get("previous_weight"),
            change_kg=weight_trend.get("change_kg", 0.0),
            change_percentage=weight_trend.get("change_percentage", 0.0),
            trend_direction=weight_trend.get("trend_direction", "stable"),
            avg_change_per_week=weight_trend.get("avg_change_per_week", 0.0),
            progress_percentage=progress_percentage,
            remaining_kg=remaining_kg
        )

        # Calculate weekly stats
        # Days with activities
        activity_dates = set()
        for activity in weekly_activities:
            activity_date = datetime.fromisoformat(str(activity["start_time"])).date()
            activity_dates.add(activity_date)

        # Days with meals
        meal_dates = set()
        for meal in weekly_meals:
            meal_date = datetime.fromisoformat(str(meal.logged_at)).date()
            meal_dates.add(meal_date)

        # Calculate averages
        total_calories_consumed_week = sum(
            float(meal.total_calories) for meal in weekly_meals
        )
        total_calories_burned_week = sum(
            activity.get("calories_burned", 0) for activity in weekly_activities
        )

        days_in_week = len(meal_dates) if meal_dates else 1  # Avoid division by zero
        avg_calories_consumed = int(total_calories_consumed_week / days_in_week) if total_calories_consumed_week > 0 else None

        days_with_activities = len(activity_dates) if activity_dates else 1
        avg_calories_burned = int(total_calories_burned_week / days_with_activities) if total_calories_burned_week > 0 else None

        weekly_stats = WeeklyStats(
            days_active=len(activity_dates),
            days_with_meals=len(meal_dates),
            total_workouts=len(weekly_activities),
            total_meals=len(weekly_meals),
            avg_calories_consumed=avg_calories_consumed,
            avg_calories_burned=avg_calories_burned
        )

        # Get display name
        display_name = None
        if profile:
            display_name = profile.get("full_name") or profile.get("email")

        # Build complete dashboard summary
        dashboard = DashboardSummary(
            user_id=str(user_id),
            display_name=display_name,
            nutrition=nutrition_summary,
            activity=activity_summary_obj,
            net_calories=net_calories,
            weight=weight_summary,
            weekly=weekly_stats,
            date=today.isoformat()
        )

        logger.info(
            "dashboard_summary_fetched",
            user_id=str(user_id),
            date=str(today),
            calories_consumed=int(nutrition_stats.calories_consumed),
            calories_burned=activity_summary["total_calories_burned"],
            net_calories=net_calories
        )

        return dashboard

    except Exception as e:
        logger.error(
            "fetch_dashboard_summary_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise
