"""
Body metrics service for managing weight and body composition tracking.

Handles business logic for creating, reading, updating, and deleting body metrics.
Calculates trends and provides weight progress analysis.
"""

import structlog
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, date, timedelta
from fastapi import HTTPException, status

from app.services.supabase_service import SupabaseService

logger = structlog.get_logger()


class BodyMetricsService:
    """
    Service for body metrics tracking operations.

    Features:
    - CRUD operations for body metrics
    - Weight trend analysis
    - Progress calculations
    - Historical tracking
    """

    def __init__(self):
        self.db = SupabaseService()

    async def get_user_body_metrics(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get body metrics for a user within a date range.

        Args:
            user_id: User UUID
            start_date: Start date (inclusive), defaults to 30 days ago
            end_date: End date (inclusive), defaults to today
            limit: Max metrics to return
            offset: Pagination offset

        Returns:
            List of body metric dicts sorted by recorded_at DESC
        """
        try:
            # Default date range: last 30 days
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            logger.info(
                "fetching_user_body_metrics",
                user_id=str(user_id),
                start_date=str(start_date),
                end_date=str(end_date),
                limit=limit,
                offset=offset
            )

            metrics = await self.db.get_user_body_metrics(
                user_id=user_id,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                limit=limit,
                offset=offset
            )

            logger.info(
                "body_metrics_fetched",
                user_id=str(user_id),
                count=len(metrics)
            )

            return metrics

        except Exception as e:
            logger.error(
                "fetch_body_metrics_failed",
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch body metrics"
            )

    async def get_latest_body_metric(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get the most recent body metric for a user.

        Args:
            user_id: User UUID

        Returns:
            Latest body metric dict or None
        """
        try:
            logger.info(
                "fetching_latest_body_metric",
                user_id=str(user_id)
            )

            metric = await self.db.get_latest_body_metric(user_id)

            if metric:
                logger.info(
                    "latest_body_metric_found",
                    user_id=str(user_id),
                    metric_id=metric.get('id'),
                    weight_kg=metric.get('weight_kg')
                )
            else:
                logger.info(
                    "no_body_metrics_found",
                    user_id=str(user_id)
                )

            return metric

        except Exception as e:
            logger.error(
                "fetch_latest_body_metric_failed",
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch latest body metric"
            )

    async def calculate_weight_trend(
        self,
        user_id: UUID,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Calculate weight trend over a specified period.

        Args:
            user_id: User UUID
            days: Number of days to analyze (default: 7)

        Returns:
            Dict with trend analysis: current_weight, previous_weight, change_kg,
            change_percentage, trend_direction, avg_change_per_week
        """
        try:
            logger.info(
                "calculating_weight_trend",
                user_id=str(user_id),
                days=days
            )

            # Get latest metric
            latest = await self.get_latest_body_metric(user_id)

            if not latest:
                # No data yet
                return {
                    "current_weight": None,
                    "previous_weight": None,
                    "change_kg": 0.0,
                    "change_percentage": 0.0,
                    "trend_direction": "stable",
                    "days_between": 0,
                    "avg_change_per_week": 0.0
                }

            current_weight = latest.get('weight_kg')
            current_date = datetime.fromisoformat(str(latest.get('recorded_at')))

            # Get metric from N days ago
            past_date = current_date - timedelta(days=days)
            past_metrics = await self.db.get_user_body_metrics(
                user_id=user_id,
                start_date=None,
                end_date=past_date.isoformat(),
                limit=1,
                offset=0
            )

            if not past_metrics or len(past_metrics) == 0:
                # Only have current data, no comparison
                return {
                    "current_weight": current_weight,
                    "previous_weight": None,
                    "change_kg": 0.0,
                    "change_percentage": 0.0,
                    "trend_direction": "stable",
                    "days_between": 0,
                    "avg_change_per_week": 0.0
                }

            previous_weight = past_metrics[0].get('weight_kg')
            previous_date = datetime.fromisoformat(str(past_metrics[0].get('recorded_at')))

            # Calculate changes
            change_kg = round(current_weight - previous_weight, 2)
            change_percentage = round((change_kg / previous_weight) * 100, 2) if previous_weight > 0 else 0.0

            # Determine trend direction
            if abs(change_kg) < 0.5:
                trend_direction = "stable"
            elif change_kg > 0:
                trend_direction = "up"
            else:
                trend_direction = "down"

            # Calculate days between measurements
            days_between = (current_date - previous_date).days

            # Calculate average change per week
            if days_between > 0:
                avg_change_per_week = round((change_kg / days_between) * 7, 2)
            else:
                avg_change_per_week = 0.0

            trend = {
                "current_weight": current_weight,
                "previous_weight": previous_weight,
                "change_kg": change_kg,
                "change_percentage": change_percentage,
                "trend_direction": trend_direction,
                "days_between": days_between,
                "avg_change_per_week": avg_change_per_week
            }

            logger.info(
                "weight_trend_calculated",
                user_id=str(user_id),
                trend_direction=trend_direction,
                change_kg=change_kg
            )

            return trend

        except Exception as e:
            logger.error(
                "calculate_weight_trend_failed",
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to calculate weight trend"
            )

    async def get_body_metric(
        self,
        metric_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Get a single body metric by ID.

        Args:
            metric_id: Body metric UUID
            user_id: User UUID (for ownership verification)

        Returns:
            Body metric dict

        Raises:
            HTTPException 404: Metric not found
            HTTPException 403: Not authorized
        """
        try:
            logger.info(
                "fetching_body_metric",
                metric_id=str(metric_id),
                user_id=str(user_id)
            )

            # Fetch from database
            metric = await self.db.get_body_metric(metric_id)

            if not metric:
                logger.warning(
                    "body_metric_not_found",
                    metric_id=str(metric_id),
                    user_id=str(user_id)
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Body metric not found"
                )

            # Verify ownership
            if metric['user_id'] != str(user_id):
                logger.warning(
                    "body_metric_access_denied",
                    metric_id=str(metric_id),
                    user_id=str(user_id),
                    owner_id=metric['user_id']
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this body metric"
                )

            return metric

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "fetch_body_metric_failed",
                metric_id=str(metric_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch body metric"
            )

    async def create_body_metric(
        self,
        user_id: UUID,
        recorded_at: datetime,
        weight_kg: float,
        body_fat_percentage: Optional[float] = None,
        height_cm: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new body metric entry.

        Args:
            user_id: User UUID
            recorded_at: When measurement was taken
            weight_kg: Weight in kilograms
            body_fat_percentage: Optional body fat percentage
            notes: Optional user notes

        Returns:
            Created body metric dict
        """
        try:
            metric_data = {
                'user_id': str(user_id),
                'recorded_at': recorded_at.isoformat(),
                'weight_kg': weight_kg,
                'body_fat_percentage': body_fat_percentage,
                'notes': notes
            }
            if height_cm is not None:
                metric_data['height_cm'] = height_cm

            logger.info(
                "creating_body_metric",
                user_id=str(user_id),
                weight_kg=weight_kg,
                recorded_at=recorded_at.isoformat()
            )

            metric = await self.db.create_body_metric(metric_data)

            logger.info(
                "body_metric_created",
                metric_id=metric['id'],
                user_id=str(user_id)
            )

            return metric

        except Exception as e:
            logger.error(
                "create_body_metric_failed",
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create body metric"
            )

    async def update_body_metric(
        self,
        metric_id: UUID,
        user_id: UUID,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing body metric.

        Args:
            metric_id: Body metric UUID
            user_id: User UUID (for ownership verification)
            updates: Fields to update

        Returns:
            Updated body metric dict

        Raises:
            HTTPException 404: Metric not found
            HTTPException 403: Not authorized
        """
        try:
            # Verify ownership
            await self.get_body_metric(metric_id, user_id)

            # Convert datetime objects to ISO strings
            if 'recorded_at' in updates and isinstance(updates['recorded_at'], datetime):
                updates['recorded_at'] = updates['recorded_at'].isoformat()

            logger.info(
                "updating_body_metric",
                metric_id=str(metric_id),
                user_id=str(user_id),
                fields=list(updates.keys())
            )

            metric = await self.db.update_body_metric(metric_id, user_id, updates)

            logger.info(
                "body_metric_updated",
                metric_id=str(metric_id),
                user_id=str(user_id)
            )

            return metric

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "update_body_metric_failed",
                metric_id=str(metric_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update body metric"
            )

    async def delete_body_metric(
        self,
        metric_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete a body metric.

        Args:
            metric_id: Body metric UUID
            user_id: User UUID (for ownership verification)

        Returns:
            True if deleted successfully

        Raises:
            HTTPException 404: Metric not found
            HTTPException 403: Not authorized
        """
        try:
            # Verify ownership
            await self.get_body_metric(metric_id, user_id)

            logger.info(
                "deleting_body_metric",
                metric_id=str(metric_id),
                user_id=str(user_id)
            )

            success = await self.db.delete_body_metric(metric_id, user_id)

            if success:
                logger.info(
                    "body_metric_deleted",
                    metric_id=str(metric_id),
                    user_id=str(user_id)
                )
            else:
                logger.warning(
                    "body_metric_delete_failed",
                    metric_id=str(metric_id),
                    user_id=str(user_id)
                )

            return success

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "delete_body_metric_failed",
                metric_id=str(metric_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete body metric"
            )


# Global singleton instance
body_metrics_service = BodyMetricsService()
