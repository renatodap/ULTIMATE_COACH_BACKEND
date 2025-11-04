"""
Activity Repository

Handles all activity-related database operations.

Responsibilities:
- Activity CRUD operations
- Activity queries with metrics
- Daily activity summaries
- Recent activities queries
- Training volume calculations

Usage:
    repo = ActivityRepository(supabase)
    activities = await repo.get_recent_activities(user_id, days=7)
    summary = await repo.get_daily_summary(user_id, target_date)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, time, timedelta
from app.repositories.base_repository import BaseRepository
from app.database.query_patterns import QueryPatterns


class ActivityRepository(BaseRepository):
    """Repository for activity operations."""

    async def get_activity(
        self,
        activity_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get activity by ID.

        Args:
            activity_id: Activity UUID
            user_id: User UUID (for ownership verification)

        Returns:
            Activity with metrics
        """
        return await self.get_one(
            "activities",
            {"id": activity_id, "user_id": user_id, "deleted_at": None},
            select=QueryPatterns.activities_full()
        )

    async def get_recent_activities(
        self,
        user_id: str,
        days: int = 7,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent activities for user.

        Args:
            user_id: User UUID
            days: Number of days to look back
            limit: Maximum number of activities

        Returns:
            List of activities
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        query = self.supabase.table("activities")\
            .select(QueryPatterns.activities_full())\
            .eq("user_id", user_id)\
            .is_("deleted_at", None)\
            .gte("start_time", cutoff_date)\
            .order("start_time", desc=True)\
            .limit(limit)

        result = query.execute()
        return result.data if result.data else []

    async def get_activities_for_date(
        self,
        user_id: str,
        target_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get all activities for a specific date.

        Args:
            user_id: User UUID
            target_date: Date to query

        Returns:
            List of activities for that date
        """
        start_of_day = datetime.combine(target_date, time.min)
        end_of_day = datetime.combine(target_date, time.max)

        query = self.supabase.table("activities")\
            .select(QueryPatterns.activities_full())\
            .eq("user_id", user_id)\
            .is_("deleted_at", None)\
            .gte("start_time", start_of_day.isoformat())\
            .lte("start_time", end_of_day.isoformat())\
            .order("start_time", desc=False)

        result = query.execute()
        return result.data if result.data else []

    async def get_activities_by_category(
        self,
        user_id: str,
        category: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get activities filtered by category.

        Args:
            user_id: User UUID
            category: Activity category
            days: Number of days to look back

        Returns:
            List of activities in category
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        query = self.supabase.table("activities")\
            .select(QueryPatterns.activities_full())\
            .eq("user_id", user_id)\
            .eq("category", category)\
            .is_("deleted_at", None)\
            .gte("start_time", cutoff_date)\
            .order("start_time", desc=True)

        result = query.execute()
        return result.data if result.data else []

    async def create_activity(
        self,
        user_id: str,
        activity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new activity.

        Args:
            user_id: User UUID
            activity_data: Activity data

        Returns:
            Created activity
        """
        activity_data["user_id"] = user_id
        return await self.create("activities", activity_data)

    async def update_activity(
        self,
        activity_id: str,
        user_id: str,
        activity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an activity.

        Args:
            activity_id: Activity UUID
            user_id: User UUID (for ownership verification)
            activity_data: Update data

        Returns:
            Updated activity
        """
        return await self.update(
            "activities",
            {"id": activity_id, "user_id": user_id},
            activity_data
        )

    async def delete_activity(
        self,
        activity_id: str,
        user_id: str
    ) -> bool:
        """
        Soft delete an activity.

        Args:
            activity_id: Activity UUID
            user_id: User UUID (for ownership verification)

        Returns:
            True if successful
        """
        return await self.delete(
            "activities",
            {"id": activity_id, "user_id": user_id},
            soft=True
        )

    async def calculate_daily_summary(
        self,
        user_id: str,
        target_date: date
    ) -> Dict[str, Any]:
        """
        Calculate activity summary for a specific date.

        Args:
            user_id: User UUID
            target_date: Date to calculate

        Returns:
            Dict with total calories, duration, avg intensity
        """
        activities = await self.get_activities_for_date(user_id, target_date)

        total_calories = sum(int(a.get("calories_burned") or 0) for a in activities)
        total_duration = sum(int(a.get("duration_minutes") or 0) for a in activities)

        # Calculate average intensity (METs)
        intensities = [float(a.get("intensity_mets") or 0) for a in activities if a.get("intensity_mets")]
        avg_intensity = sum(intensities) / len(intensities) if intensities else 0

        return {
            "date": target_date.isoformat(),
            "activity_count": len(activities),
            "total_calories_burned": total_calories,
            "total_duration_minutes": total_duration,
            "avg_intensity_mets": round(avg_intensity, 1)
        }

    async def get_strength_training_volume(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate strength training volume.

        Args:
            user_id: User UUID
            days: Number of days to analyze

        Returns:
            Dict with total volume, workout count, exercises
        """
        activities = await self.get_activities_by_category(
            user_id,
            "strength_training",
            days
        )

        total_volume = 0
        exercise_volumes = {}

        for activity in activities:
            metrics = activity.get("metrics", {})
            exercises = metrics.get("exercises", [])

            for exercise in exercises:
                exercise_name = exercise.get("name", "").lower()
                sets = exercise.get("sets", 0)
                reps = exercise.get("reps", 0)
                weight = exercise.get("weight_kg", 0)

                volume = sets * reps * weight
                total_volume += volume

                if exercise_name not in exercise_volumes:
                    exercise_volumes[exercise_name] = 0
                exercise_volumes[exercise_name] += volume

        # Top 5 exercises by volume
        top_exercises = sorted(
            exercise_volumes.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            "days_analyzed": days,
            "workout_count": len(activities),
            "total_volume_kg": round(total_volume, 1),
            "avg_volume_per_workout_kg": round(total_volume / len(activities), 1) if activities else 0,
            "top_exercises": [
                {"exercise": name, "volume_kg": round(vol, 1)}
                for name, vol in top_exercises
            ]
        }
