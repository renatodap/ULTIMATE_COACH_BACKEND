"""
Activity service for managing workout and activity tracking.

Handles business logic for creating, reading, updating, and deleting activities.
Calculates daily summaries and manages activity-specific metrics.
"""

import structlog
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, date, timedelta
from fastapi import HTTPException, status

from app.services.supabase_service import SupabaseService
from app.services.calorie_calculator import estimate_activity_calories
from app.services.activity_matching_service import activity_matching_service

logger = structlog.get_logger()  # Force reload


class ActivityService:
    """
    Service for activity tracking operations.

    Features:
    - CRUD operations for activities
    - Daily/weekly aggregations
    - Duration calculations
    - Category-specific metric validation
    """

    def __init__(self):
        self.db = SupabaseService()

    async def get_user_activities(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get activities for a user within a date range.

        Args:
            user_id: User UUID
            start_date: Start date (inclusive), defaults to 30 days ago
            end_date: End date (inclusive), defaults to today
            limit: Max activities to return
            offset: Pagination offset

        Returns:
            List of activity dicts sorted by start_time DESC
        """
        try:
            # Default date range: last 90 days (more inclusive)
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=90)

            logger.info(
                "fetching_user_activities",
                user_id=str(user_id),
                start_date=str(start_date),
                end_date=str(end_date),
                limit=limit,
                offset=offset
            )

            activities = await self.db.get_user_activities(
                user_id=user_id,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                limit=limit,
                offset=offset
            )

            # Post-process: ensure duration is calculated
            for activity in activities:
                if not activity.get('duration_minutes') and activity.get('end_time'):
                    activity['duration_minutes'] = self._calculate_duration(
                        activity['start_time'],
                        activity['end_time']
                    )

            logger.info(
                "activities_fetched",
                user_id=str(user_id),
                count=len(activities)
            )

            return activities

        except Exception as e:
            logger.error(
                "fetch_activities_failed",
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch activities"
            )

    async def get_daily_summary(
        self,
        user_id: UUID,
        target_date: date
    ) -> Dict[str, Any]:
        """
        Calculate daily activity summary with aggregated stats.

        Args:
            user_id: User UUID
            target_date: Date to summarize

        Returns:
            Dict with total_calories, total_duration, avg_intensity, etc.
        """
        try:
            logger.info(
                "calculating_daily_summary",
                user_id=str(user_id),
                date=str(target_date)
            )

            # Get user's daily goal
            profile = await self.db.get_profile(user_id)
            daily_goal = profile.get('daily_calorie_burn_goal', 500) if profile else 500

            # Get activities for the day
            activities = await self.get_user_activities(
                user_id=user_id,
                start_date=target_date,
                end_date=target_date,
                limit=100  # Get all activities for the day
            )

            # Calculate aggregates
            total_calories = sum(a.get('calories_burned', 0) for a in activities)
            total_duration = sum(a.get('duration_minutes', 0) for a in activities)
            activity_count = len(activities)

            # Calculate average intensity (METs)
            avg_intensity = 0.0
            if activity_count > 0:
                total_mets = sum(a.get('intensity_mets', 0) for a in activities)
                avg_intensity = total_mets / activity_count

            # Calculate goal percentage
            goal_percentage = (total_calories / daily_goal * 100) if daily_goal > 0 else 0

            summary = {
                "total_calories_burned": total_calories,
                "total_duration_minutes": total_duration,
                "average_intensity": round(avg_intensity, 1),
                "activity_count": activity_count,
                "daily_goal_calories": daily_goal,
                "goal_percentage": round(goal_percentage, 1)
            }

            logger.info(
                "daily_summary_calculated",
                user_id=str(user_id),
                date=str(target_date),
                total_calories=total_calories,
                activity_count=activity_count
            )

            return summary

        except Exception as e:
            logger.error(
                "daily_summary_failed",
                user_id=str(user_id),
                date=str(target_date),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to calculate daily summary"
            )

    async def get_activity(
        self,
        activity_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Get a single activity by ID.

        Args:
            activity_id: Activity UUID
            user_id: User UUID (for ownership verification)

        Returns:
            Activity dict

        Raises:
            HTTPException 404: Activity not found
            HTTPException 403: Not authorized
        """
        try:
            logger.info(
                "fetching_activity",
                activity_id=str(activity_id),
                user_id=str(user_id)
            )

            # Fetch from database
            activity = await self.db.get_activity(activity_id)

            if not activity:
                logger.warning(
                    "activity_not_found",
                    activity_id=str(activity_id),
                    user_id=str(user_id)
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Activity not found"
                )

            # Verify ownership
            if activity['user_id'] != str(user_id):
                logger.warning(
                    "activity_access_denied",
                    activity_id=str(activity_id),
                    user_id=str(user_id),
                    owner_id=activity['user_id']
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this activity"
                )

            return activity

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "fetch_activity_failed",
                activity_id=str(activity_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch activity"
            )

    async def create_activity(
        self,
        user_id: UUID,
        category: str,
        activity_name: str,
        start_time: datetime,
        end_time: Optional[datetime],
        duration_minutes: Optional[int],
        calories_burned: Optional[int],
        intensity_mets: Optional[float],
        metrics: Dict[str, Any],
        notes: Optional[str]
    ) -> Dict[str, Any]:
        """
        Create a new activity.

        Args:
            user_id: User UUID
            category: Activity category
            activity_name: Custom name
            start_time: Start timestamp
            end_time: End timestamp (optional)
            duration_minutes: Duration (optional if end_time provided)
            calories_burned: Calories burned (optional, will be auto-calculated)
            intensity_mets: Intensity level in METs (optional, will be auto-looked-up)
            metrics: Category-specific metrics (JSONB)
            notes: User notes

        Returns:
            Created activity dict
        """
        try:
            # Calculate duration if not provided
            if not duration_minutes and end_time:
                duration_minutes = self._calculate_duration(start_time, end_time)

            # Ensure duration is set
            if not duration_minutes:
                raise ValueError("Either duration_minutes or end_time must be provided")

            # Auto-calculate calories if not provided
            if calories_burned is None or intensity_mets is None:
                # Get user's weight from profile
                profile = await self.db.get_profile(user_id)
                user_weight_kg = profile.get('current_weight_kg') if profile else None

                if user_weight_kg is None:
                    logger.warning(
                        "no_user_weight_for_calorie_calculation",
                        user_id=str(user_id)
                    )
                    # Use average weight as fallback (70kg)
                    user_weight_kg = 70.0

                # Estimate calories using calorie calculator
                estimation = estimate_activity_calories(
                    activity_name=activity_name,
                    category=category,
                    duration_minutes=duration_minutes,
                    weight_kg=user_weight_kg,
                    user_provided_mets=intensity_mets  # Will be None if not provided
                )

                # Use calculated values if not provided by user
                if calories_burned is None:
                    calories_burned = estimation['calories']
                    logger.info(
                        "calories_auto_calculated",
                        user_id=str(user_id),
                        activity_name=activity_name,
                        calories=calories_burned,
                        method=estimation['method']
                    )

                if intensity_mets is None:
                    intensity_mets = estimation['mets']
                    logger.info(
                        "mets_auto_looked_up",
                        user_id=str(user_id),
                        activity_name=activity_name,
                        mets=intensity_mets,
                        matched_activity=estimation['matched_activity']
                    )

            activity_data = {
                'user_id': str(user_id),
                'category': category,
                'activity_name': activity_name,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat() if end_time else None,
                'duration_minutes': duration_minutes,
                'calories_burned': calories_burned,
                'intensity_mets': intensity_mets,
                'metrics': metrics,
                'notes': notes
            }

            logger.info(
                "creating_activity",
                user_id=str(user_id),
                category=category,
                activity_name=activity_name,
                duration=duration_minutes
            )

            activity = await self.db.create_activity(activity_data)

            logger.info(
                "activity_created",
                activity_id=activity['id'],
                user_id=str(user_id)
            )

            # Attempt to match activity to planned session (non-blocking)
            try:
                await activity_matching_service.match_activity_to_session(
                    activity_id=activity['id'],
                    user_id=str(user_id)
                )
            except Exception as e:
                # Don't fail activity creation if matching fails
                logger.warning(
                    "activity_matching_failed",
                    activity_id=activity['id'],
                    user_id=str(user_id),
                    error=str(e)
                )

            return activity

        except ValueError as e:
            logger.warning(
                "activity_validation_failed",
                user_id=str(user_id),
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(
                "create_activity_failed",
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create activity"
            )

    async def update_activity(
        self,
        activity_id: UUID,
        user_id: UUID,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing activity.

        Args:
            activity_id: Activity UUID
            user_id: User UUID (for ownership verification)
            updates: Fields to update

        Returns:
            Updated activity dict

        Raises:
            HTTPException 404: Activity not found
            HTTPException 403: Not authorized
        """
        try:
            # Verify ownership
            existing = await self.get_activity(activity_id, user_id)

            # Recalculate duration if times changed
            if 'start_time' in updates or 'end_time' in updates:
                start = updates.get('start_time', existing.get('start_time'))
                end = updates.get('end_time', existing.get('end_time'))

                if end and start:
                    # Convert strings to datetime if needed
                    if isinstance(start, str):
                        start = datetime.fromisoformat(start)
                    if isinstance(end, str):
                        end = datetime.fromisoformat(end)

                    updates['duration_minutes'] = self._calculate_duration(start, end)

            # Convert datetime objects to ISO strings
            for key in ['start_time', 'end_time']:
                if key in updates and isinstance(updates[key], datetime):
                    updates[key] = updates[key].isoformat()

            logger.info(
                "updating_activity",
                activity_id=str(activity_id),
                user_id=str(user_id),
                fields=list(updates.keys())
            )

            activity = await self.db.update_activity(activity_id, user_id, updates)

            logger.info(
                "activity_updated",
                activity_id=str(activity_id),
                user_id=str(user_id)
            )

            return activity

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "update_activity_failed",
                activity_id=str(activity_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update activity"
            )

    async def delete_activity(
        self,
        activity_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete an activity (soft delete).

        Args:
            activity_id: Activity UUID
            user_id: User UUID (for ownership verification)

        Returns:
            True if deleted successfully

        Raises:
            HTTPException 404: Activity not found
            HTTPException 403: Not authorized
        """
        try:
            # Verify ownership
            await self.get_activity(activity_id, user_id)

            logger.info(
                "deleting_activity",
                activity_id=str(activity_id),
                user_id=str(user_id)
            )

            success = await self.db.delete_activity(activity_id, user_id)

            if success:
                logger.info(
                    "activity_deleted",
                    activity_id=str(activity_id),
                    user_id=str(user_id)
                )
            else:
                logger.warning(
                    "activity_delete_failed",
                    activity_id=str(activity_id),
                    user_id=str(user_id)
                )

            return success

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "delete_activity_failed",
                activity_id=str(activity_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete activity"
            )

    def _calculate_duration(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """
        Calculate duration in minutes between two timestamps.

        Args:
            start_time: Start datetime
            end_time: End datetime

        Returns:
            Duration in minutes (rounded)
        """
        # Handle string inputs
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

        delta = end_time - start_time
        return int(delta.total_seconds() / 60)


# Global singleton instance
activity_service = ActivityService()
