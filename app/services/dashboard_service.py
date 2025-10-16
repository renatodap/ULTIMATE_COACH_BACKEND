"""
Dashboard Service

Aggregates data from multiple services to build unified dashboard summary.
Separates business logic from route handlers for better testability.
"""

import structlog
import asyncio
from uuid import UUID
from datetime import date, datetime, timedelta
from typing import Optional

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

logger = structlog.get_logger()


class DashboardService:
    """Service for aggregating dashboard data from multiple sources"""

    def __init__(self):
        self.nutrition_service = nutrition_service
        self.activity_service = activity_service
        self.body_metrics_service = body_metrics_service
        self.supabase_service = supabase_service

    async def get_dashboard_summary(
        self,
        user_id: UUID,
        target_date: Optional[date] = None
    ) -> DashboardSummary:
        """
        Get unified dashboard summary for specified date (defaults to today).

        Aggregates:
        - Today's nutrition (calories, macros, meals)
        - Today's activities (calories burned, workouts)
        - Weight progress (current, trend, goal)
        - Weekly stats (consistency, averages)

        Args:
            user_id: User UUID
            target_date: Date for dashboard (defaults to today)

        Returns:
            Complete dashboard summary

        Raises:
            HTTPException: If data fetching fails
        """
        if target_date is None:
            target_date = date.today()

        logger.info(
            "fetching_dashboard_summary",
            user_id=str(user_id),
            date=str(target_date)
        )

        try:
            # Fetch all data in parallel for performance
            (
                profile,
                nutrition_stats,
                activity_summary,
                latest_weight,
                weight_trend,
                weekly_activities,
                weekly_meals
            ) = await self._fetch_all_data_parallel(user_id, target_date)

            # Process individual sections
            nutrition_summary = self._build_nutrition_summary(nutrition_stats)
            activity_summary_obj = TodayActivitySummary(**activity_summary)
            net_calories = self._calculate_net_calories(nutrition_stats, activity_summary)
            weight_summary = self._build_weight_summary(profile, latest_weight, weight_trend)
            weekly_stats = self._build_weekly_stats(weekly_activities, weekly_meals)
            display_name = self._extract_display_name(profile)

            # Assemble complete dashboard
            dashboard = DashboardSummary(
                user_id=str(user_id),
                display_name=display_name,
                nutrition=nutrition_summary,
                activity=activity_summary_obj,
                net_calories=net_calories,
                weight=weight_summary,
                weekly=weekly_stats,
                date=target_date.isoformat()
            )

            logger.info(
                "dashboard_summary_fetched",
                user_id=str(user_id),
                date=str(target_date),
                calories_consumed=int(nutrition_stats.calories_consumed),
                calories_burned=activity_summary["total_calories_burned"],
                net_calories=net_calories
            )

            return dashboard

        except Exception as e:
            logger.error(
                "fetch_dashboard_summary_error",
                user_id=str(user_id),
                date=str(target_date),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise

    async def _fetch_all_data_parallel(
        self,
        user_id: UUID,
        target_date: date
    ) -> tuple:
        """
        Fetch all required data in parallel for performance.

        Returns tuple of:
        (profile, nutrition_stats, activity_summary, latest_weight,
         weight_trend, weekly_activities, weekly_meals)
        """
        # Define all parallel tasks
        profile_task = self.supabase_service.get_profile(user_id)

        nutrition_task = self.nutrition_service.get_nutrition_stats(
            user_id=user_id,
            date=target_date.isoformat()
        )

        activity_task = self.activity_service.get_daily_summary(
            user_id=user_id,
            target_date=target_date
        )

        latest_weight_task = self.body_metrics_service.get_latest_body_metric(user_id)
        weight_trend_task = self.body_metrics_service.calculate_weight_trend(user_id, days=7)

        # Weekly data (last 7 days)
        week_start = target_date - timedelta(days=6)
        weekly_activities_task = self.activity_service.get_user_activities(
            user_id=user_id,
            start_date=week_start,
            end_date=target_date,
            limit=100
        )
        weekly_meals_task = self.nutrition_service.get_user_meals(
            user_id=user_id,
            start_date=datetime.combine(week_start, datetime.min.time()),
            end_date=datetime.combine(target_date, datetime.max.time().replace(microsecond=0)),
            limit=100
        )

        # Await all tasks
        try:
            results = await asyncio.gather(
                profile_task,
                nutrition_task,
                activity_task,
                latest_weight_task,
                weight_trend_task,
                weekly_activities_task,
                weekly_meals_task,
                return_exceptions=False
            )
            return results
        except Exception as gather_error:
            logger.error(
                "asyncio_gather_failed",
                user_id=str(user_id),
                error=str(gather_error),
                error_type=type(gather_error).__name__,
                exc_info=True
            )
            raise

    def _build_nutrition_summary(self, nutrition_stats) -> TodayNutritionSummary:
        """Build nutrition summary from stats"""
        calories_remaining = None
        if nutrition_stats.calories_goal:
            calories_remaining = int(
                nutrition_stats.calories_goal - nutrition_stats.calories_consumed
            )

        return TodayNutritionSummary(
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

    def _calculate_net_calories(self, nutrition_stats, activity_summary: dict) -> int:
        """Calculate net calories (consumed - burned)"""
        return int(nutrition_stats.calories_consumed) - activity_summary["total_calories_burned"]

    def _build_weight_summary(
        self,
        profile: Optional[dict],
        latest_weight: Optional[dict],
        weight_trend: dict
    ) -> WeightProgressSummary:
        """Build weight progress summary with goal calculations"""
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

        return WeightProgressSummary(
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

    def _build_weekly_stats(
        self,
        weekly_activities: list,
        weekly_meals: list
    ) -> WeeklyStats:
        """Build weekly statistics from activities and meals"""
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
        avg_calories_consumed = (
            int(total_calories_consumed_week / days_in_week)
            if total_calories_consumed_week > 0
            else None
        )

        days_with_activities = len(activity_dates) if activity_dates else 1
        avg_calories_burned = (
            int(total_calories_burned_week / days_with_activities)
            if total_calories_burned_week > 0
            else None
        )

        return WeeklyStats(
            days_active=len(activity_dates),
            days_with_meals=len(meal_dates),
            total_workouts=len(weekly_activities),
            total_meals=len(weekly_meals),
            avg_calories_consumed=avg_calories_consumed,
            avg_calories_burned=avg_calories_burned
        )

    def _extract_display_name(self, profile: Optional[dict]) -> Optional[str]:
        """Extract display name from profile (full_name or email)"""
        if not profile:
            return None
        return profile.get("full_name") or profile.get("email")


# Singleton instance
dashboard_service = DashboardService()
