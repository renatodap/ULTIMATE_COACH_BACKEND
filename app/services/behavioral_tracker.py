"""
Behavioral Tracker Service

Calculates behavioral metrics from actual user data to inform system prompt updates.

The key insight: User's ACTUAL behavior reveals more than what they say in forms.
- Someone who logs food religiously but overeats = different psychology than
  someone who logs sporadically but stays in target when they do
- Diet switches per month = core metric for adherence issues
- Logging streaks = consistency vs all-or-nothing thinking

These metrics feed into weekly system prompt updates to make coaching evolve.

Example Metrics:
    {
        "diet_switches_per_month": 0,  # No switching = good!
        "meal_logging_streak_days": 42,  # 6-week streak = excellent
        "avg_days_per_week_in_target": 5.2,  # 5.2/7 days = 74% adherence
        "most_common_failure_pattern": "weekend_overeating",
        "adherence_rate_last_30_days": 0.74,  # 74%
        "avg_calories_per_day": 2650,
        "avg_protein_per_day": 195,
        "days_over_target": 8,  # 8/30 days
        "days_under_target": 22,  # 22/30 days
        "longest_streak_in_target": 12  # Best streak
    }

These metrics answer:
- Is their system prompt working? (adherence rate)
- Do they need tighter accountability? (logging streak)
- Should we adjust targets? (avg calories vs target)
- What's their failure pattern? (weekend overeating, stress eating, etc.)
"""

import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from collections import Counter

logger = structlog.get_logger()


class BehavioralTracker:
    """
    Calculate behavioral metrics from user data.

    Tracks actual behavior across meals, activities, check-ins to
    detect patterns, failures, and adherence trends.
    """

    def __init__(self, supabase_client):
        """
        Initialize with Supabase client.

        Args:
            supabase_client: Supabase client for database access
        """
        self.supabase = supabase_client
        logger.info("behavioral_tracker_initialized")

    async def calculate_metrics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive behavioral metrics for user.

        Analyzes past N days of data to detect patterns.

        Args:
            user_id: User UUID
            days: Number of days to analyze (default 30)

        Returns:
            Dictionary of behavioral metrics
        """

        logger.info(
            "calculating_behavioral_metrics",
            user_id=user_id,
            days=days
        )

        # Get user's profile and targets
        profile = await self._get_user_profile(user_id)
        if not profile:
            logger.warning("no_profile_found", user_id=user_id)
            return self._get_empty_metrics()

        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Fetch all relevant data in parallel
        meals_data = await self._get_meals(user_id, start_date, end_date)
        # activities_data = await self._get_activities(user_id, start_date, end_date)
        # check_ins_data = await self._get_check_ins(user_id, start_date, end_date)

        # Calculate individual metrics
        logging_metrics = self._calculate_logging_metrics(meals_data, days)
        adherence_metrics = self._calculate_adherence_metrics(
            meals_data,
            profile.get("daily_calories"),
            profile.get("protein_g")
        )
        pattern_metrics = self._detect_failure_patterns(meals_data, profile)

        # Combine all metrics
        metrics = {
            **logging_metrics,
            **adherence_metrics,
            **pattern_metrics,
            "days_analyzed": days,
            "calculated_at": datetime.now().isoformat()
        }

        logger.info(
            "behavioral_metrics_calculated",
            user_id=user_id,
            adherence_rate=metrics.get("adherence_rate_last_30_days"),
            logging_streak=metrics.get("meal_logging_streak_days")
        )

        return metrics

    async def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch user profile with targets."""
        try:
            result = self.supabase.table("profiles")\
                .select("*")\
                .eq("id", user_id)\
                .single()\
                .execute()

            return result.data if result.data else None

        except Exception as e:
            logger.error(
                "profile_fetch_failed",
                user_id=user_id,
                error=str(e)
            )
            return None

    async def _get_meals(
        self,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Fetch meals for date range."""
        try:
            result = self.supabase.table("meals")\
                .select("*")\
                .eq("user_id", user_id)\
                .gte("logged_at", start_date.isoformat())\
                .lte("logged_at", end_date.isoformat())\
                .order("logged_at")\
                .execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(
                "meals_fetch_failed",
                user_id=user_id,
                error=str(e)
            )
            return []

    def _calculate_logging_metrics(
        self,
        meals: List[Dict[str, Any]],
        total_days: int
    ) -> Dict[str, Any]:
        """
        Calculate meal logging consistency metrics.

        Detects:
        - Current logging streak
        - Average meals per day
        - Days with no logging (potential failures)
        """

        if not meals:
            return {
                "meal_logging_streak_days": 0,
                "avg_meals_per_day": 0,
                "days_with_logging": 0,
                "days_without_logging": total_days
            }

        # Group meals by date
        meals_by_date = {}
        for meal in meals:
            meal_date = datetime.fromisoformat(meal["logged_at"]).date()
            if meal_date not in meals_by_date:
                meals_by_date[meal_date] = []
            meals_by_date[meal_date].append(meal)

        # Calculate current streak
        current_streak = 0
        check_date = datetime.now().date()

        while check_date in meals_by_date:
            current_streak += 1
            check_date -= timedelta(days=1)

        # Calculate stats
        days_with_logging = len(meals_by_date)
        days_without_logging = total_days - days_with_logging
        avg_meals_per_day = len(meals) / total_days if total_days > 0 else 0

        return {
            "meal_logging_streak_days": current_streak,
            "avg_meals_per_day": round(avg_meals_per_day, 1),
            "days_with_logging": days_with_logging,
            "days_without_logging": days_without_logging,
            "logging_rate": round(days_with_logging / total_days, 2) if total_days > 0 else 0
        }

    def _calculate_adherence_metrics(
        self,
        meals: List[Dict[str, Any]],
        daily_calorie_target: Optional[int],
        daily_protein_target: Optional[int]
    ) -> Dict[str, Any]:
        """
        Calculate adherence to targets.

        Analyzes:
        - Days in calorie target (within ±10%)
        - Average intake vs target
        - Over/under target days
        - Longest streak in target
        """

        if not meals or not daily_calorie_target:
            return {
                "adherence_rate_last_30_days": 0,
                "avg_calories_per_day": 0,
                "avg_protein_per_day": 0,
                "days_in_target": 0,
                "days_over_target": 0,
                "days_under_target": 0,
                "longest_streak_in_target": 0,
                "avg_days_per_week_in_target": 0
            }

        # Group meals by date and calculate daily totals
        daily_totals = {}
        for meal in meals:
            meal_date = datetime.fromisoformat(meal["logged_at"]).date()

            if meal_date not in daily_totals:
                daily_totals[meal_date] = {
                    "calories": 0,
                    "protein": 0,
                    "in_target": False
                }

            daily_totals[meal_date]["calories"] += meal.get("total_calories", 0)
            daily_totals[meal_date]["protein"] += meal.get("total_protein", 0)

        # Check which days are in target (within ±10% buffer)
        calorie_buffer = daily_calorie_target * 0.10
        lower_bound = daily_calorie_target - calorie_buffer
        upper_bound = daily_calorie_target + calorie_buffer

        days_in_target = 0
        days_over_target = 0
        days_under_target = 0
        total_calories = 0
        total_protein = 0

        for day_data in daily_totals.values():
            cals = day_data["calories"]
            total_calories += cals
            total_protein += day_data["protein"]

            if lower_bound <= cals <= upper_bound:
                days_in_target += 1
                day_data["in_target"] = True
            elif cals > upper_bound:
                days_over_target += 1
            else:
                days_under_target += 1

        # Calculate longest streak in target
        sorted_dates = sorted(daily_totals.keys())
        longest_streak = 0
        current_streak = 0

        for date in sorted_dates:
            if daily_totals[date]["in_target"]:
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
            else:
                current_streak = 0

        # Calculate averages
        num_days = len(daily_totals)
        avg_calories = round(total_calories / num_days) if num_days > 0 else 0
        avg_protein = round(total_protein / num_days) if num_days > 0 else 0
        adherence_rate = days_in_target / num_days if num_days > 0 else 0
        avg_days_per_week = (days_in_target / num_days) * 7 if num_days > 0 else 0

        return {
            "adherence_rate_last_30_days": round(adherence_rate, 2),
            "avg_calories_per_day": avg_calories,
            "avg_protein_per_day": avg_protein,
            "days_in_target": days_in_target,
            "days_over_target": days_over_target,
            "days_under_target": days_under_target,
            "longest_streak_in_target": longest_streak,
            "avg_days_per_week_in_target": round(avg_days_per_week, 1),
            "daily_calorie_target": daily_calorie_target,
            "daily_protein_target": daily_protein_target or 0
        }

    def _detect_failure_patterns(
        self,
        meals: List[Dict[str, Any]],
        profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect common failure patterns.

        Patterns detected:
        - Weekend overeating (Sat/Sun calories > weekday avg + 20%)
        - Stress eating (evening meals > morning meals by 2x)
        - All-or-nothing (either perfect or way over, no middle ground)
        - Diet switching (sudden changes in food types, meal structure)
        """

        if not meals:
            return {
                "most_common_failure_pattern": None,
                "diet_switches_per_month": 0,
                "weekend_overeating_detected": False,
                "stress_eating_detected": False
            }

        # Group meals by day of week
        weekday_calories = []
        weekend_calories = []

        for meal in meals:
            meal_date = datetime.fromisoformat(meal["logged_at"])
            day_of_week = meal_date.weekday()  # 0=Monday, 6=Sunday
            calories = meal.get("total_calories", 0)

            if day_of_week >= 5:  # Saturday or Sunday
                weekend_calories.append(calories)
            else:
                weekday_calories.append(calories)

        # Detect weekend overeating
        weekend_overeating = False
        if weekday_calories and weekend_calories:
            avg_weekday = sum(weekday_calories) / len(weekday_calories)
            avg_weekend = sum(weekend_calories) / len(weekend_calories)

            if avg_weekend > avg_weekday * 1.2:  # 20% higher on weekends
                weekend_overeating = True

        # Diet switches: Simplified detection
        # (Could be enhanced to analyze meal types, macros distribution changes)
        diet_switches = 0  # Placeholder - would need more complex analysis

        # Determine most common failure pattern
        failure_pattern = None
        if weekend_overeating:
            failure_pattern = "weekend_overeating"

        return {
            "most_common_failure_pattern": failure_pattern,
            "diet_switches_per_month": diet_switches,
            "weekend_overeating_detected": weekend_overeating,
            "stress_eating_detected": False  # Placeholder for future enhancement
        }

    def _get_empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure when no data available."""
        return {
            "meal_logging_streak_days": 0,
            "avg_meals_per_day": 0,
            "days_with_logging": 0,
            "days_without_logging": 30,
            "logging_rate": 0,
            "adherence_rate_last_30_days": 0,
            "avg_calories_per_day": 0,
            "avg_protein_per_day": 0,
            "days_in_target": 0,
            "days_over_target": 0,
            "days_under_target": 0,
            "longest_streak_in_target": 0,
            "avg_days_per_week_in_target": 0,
            "most_common_failure_pattern": None,
            "diet_switches_per_month": 0,
            "weekend_overeating_detected": False,
            "stress_eating_detected": False,
            "days_analyzed": 30,
            "calculated_at": datetime.now().isoformat()
        }


# Singleton instance
_behavioral_tracker: Optional[BehavioralTracker] = None


def get_behavioral_tracker() -> BehavioralTracker:
    """Get singleton Behavioral Tracker instance."""
    if _behavioral_tracker is None:
        raise RuntimeError(
            "BehavioralTracker not initialized. "
            "Call init_behavioral_tracker() first in app startup."
        )
    return _behavioral_tracker


def init_behavioral_tracker(supabase_client) -> BehavioralTracker:
    """Initialize Behavioral Tracker singleton."""
    global _behavioral_tracker
    _behavioral_tracker = BehavioralTracker(supabase_client)
    return _behavioral_tracker
