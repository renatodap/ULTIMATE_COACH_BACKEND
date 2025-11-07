"""
Body Metrics Repository

Handles all body measurement database operations.

Responsibilities:
- Body measurement CRUD operations
- Measurement history queries
- Weight trend calculations
- Latest measurements retrieval

Usage:
    repo = BodyMetricsRepository(supabase)
    measurements = await repo.get_recent_measurements(user_id, days=30)
    latest = await repo.get_latest_weight(user_id)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from app.repositories.base_repository import BaseRepository
from app.database.query_patterns import QueryPatterns


class BodyMetricsRepository(BaseRepository):
    """Repository for body measurement operations."""

    async def get_measurement(
        self,
        measurement_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get measurement by ID.

        Args:
            measurement_id: Measurement UUID
            user_id: User UUID (for ownership verification)

        Returns:
            Body measurement dict
        """
        return await self.get_one(
            "body_metrics",
            {"id": measurement_id, "user_id": user_id},
            select=QueryPatterns.body_metrics_full()
        )

    async def get_recent_measurements(
        self,
        user_id: str,
        days: int = 30,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent body measurements.

        Args:
            user_id: User UUID
            days: Number of days to look back
            limit: Optional limit on number of results

        Returns:
            List of measurements ordered by date (newest first)
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        query = self.supabase.table("body_metrics")\
            .select(QueryPatterns.body_metrics_full())\
            .eq("user_id", user_id)\
            .gte("recorded_at", cutoff_date)\
            .order("recorded_at", desc=True)

        if limit:
            query = query.limit(limit)

        result = query.execute()
        return result.data if result.data else []

    async def get_latest_weight(self, user_id: str) -> Optional[float]:
        """
        Get user's latest weight.

        Args:
            user_id: User UUID

        Returns:
            Weight in kg or None if no measurements
        """
        result = self.supabase.table("body_metrics")\
            .select("weight_kg")\
            .eq("user_id", user_id)\
            .order("recorded_at", desc=True)\
            .limit(1)\
            .execute()

        if result.data and len(result.data) > 0:
            return float(result.data[0].get("weight_kg", 0))

        return None

    async def get_latest_measurement(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's latest complete measurement.

        Args:
            user_id: User UUID

        Returns:
            Latest measurement dict or None
        """
        result = self.supabase.table("body_metrics")\
            .select(QueryPatterns.body_metrics_full())\
            .eq("user_id", user_id)\
            .order("recorded_at", desc=True)\
            .limit(1)\
            .execute()

        if result.data and len(result.data) > 0:
            return result.data[0]

        return None

    async def create_measurement(
        self,
        user_id: str,
        measurement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new body measurement.

        Args:
            user_id: User UUID
            measurement_data: Measurement data

        Returns:
            Created measurement
        """
        measurement_data["user_id"] = user_id
        if "recorded_at" not in measurement_data:
            measurement_data["recorded_at"] = datetime.utcnow().isoformat()

        return await self.create("body_metrics", measurement_data)

    async def update_measurement(
        self,
        measurement_id: str,
        user_id: str,
        measurement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a body measurement.

        Args:
            measurement_id: Measurement UUID
            user_id: User UUID (for ownership verification)
            measurement_data: Update data

        Returns:
            Updated measurement
        """
        return await self.update(
            "body_metrics",
            {"id": measurement_id, "user_id": user_id},
            measurement_data
        )

    async def delete_measurement(
        self,
        measurement_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a body measurement.

        Args:
            measurement_id: Measurement UUID
            user_id: User UUID (for ownership verification)

        Returns:
            True if successful
        """
        # Hard delete for body metrics (no soft delete needed)
        return await self.delete(
            "body_metrics",
            {"id": measurement_id, "user_id": user_id},
            soft=False
        )

    async def calculate_weight_trend(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate weight trend over time.

        Args:
            user_id: User UUID
            days: Number of days to analyze

        Returns:
            Dict with trend analysis
        """
        measurements = await self.get_recent_measurements(user_id, days)

        if len(measurements) < 2:
            return {
                "error": "Need at least 2 weight measurements for trend analysis",
                "data_points": len(measurements)
            }

        # Reverse to get oldest first
        measurements = list(reversed(measurements))

        first = measurements[0]
        last = measurements[-1]

        first_weight = float(first["weight_kg"])
        last_weight = float(last["weight_kg"])

        change = last_weight - first_weight
        percent_change = (change / first_weight * 100) if first_weight > 0 else 0

        direction = "stable"
        if abs(percent_change) > 2:
            direction = "decreasing" if change < 0 else "increasing"

        return {
            "days_analyzed": days,
            "data_points": len(measurements),
            "first_weight_kg": round(first_weight, 1),
            "last_weight_kg": round(last_weight, 1),
            "change_kg": round(change, 1),
            "percent_change": round(percent_change, 1),
            "direction": direction,
            "first_date": first["recorded_at"],
            "last_date": last["recorded_at"]
        }

    async def get_measurements_by_date_range(
        self,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get measurements within a date range.

        Args:
            user_id: User UUID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of measurements in date range
        """
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        query = self.supabase.table("body_metrics")\
            .select(QueryPatterns.body_metrics_full())\
            .eq("user_id", user_id)\
            .gte("recorded_at", start_datetime.isoformat())\
            .lte("recorded_at", end_datetime.isoformat())\
            .order("recorded_at", desc=False)

        result = query.execute()
        return result.data if result.data else []

    async def get_average_weight(
        self,
        user_id: str,
        days: int = 7
    ) -> Optional[float]:
        """
        Calculate average weight over period.

        Args:
            user_id: User UUID
            days: Number of days to average

        Returns:
            Average weight in kg or None
        """
        measurements = await self.get_recent_measurements(user_id, days)

        if not measurements:
            return None

        weights = [float(m["weight_kg"]) for m in measurements]
        return round(sum(weights) / len(weights), 1)
