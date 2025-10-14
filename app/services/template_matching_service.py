"""
Template Matching Service

Intelligent algorithm to match activities with templates based on:
- Activity type (40 pts) - Exact match required
- Distance (25 pts) - Within tolerance range
- Time of day (20 pts) - Within time window
- Day of week (10 pts) - Matches preferred days
- Duration (5 pts) - Within tolerance range

Total possible score: 100 points
Match thresholds:
- 90-100: Excellent match (auto-suggest with high confidence)
- 70-89: Good match (suggest to user)
- 50-69: Fair match (show in "other suggestions")
- 0-49: Poor match (don't show)
"""

import structlog
from datetime import datetime, date, time
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

from fastapi import HTTPException, status

from app.services.supabase_service import SupabaseService
from app.services.template_service import template_service

logger = structlog.get_logger()


class MatchScoreBreakdown:
    """Detailed breakdown of match score calculation"""

    def __init__(
        self,
        type_score: int = 0,
        distance_score: float = 0.0,
        time_score: float = 0.0,
        day_score: float = 0.0,
        duration_score: float = 0.0,
    ):
        self.type_score = type_score
        self.distance_score = distance_score
        self.time_score = time_score
        self.day_score = day_score
        self.duration_score = duration_score
        self.total = int(
            type_score + distance_score + time_score + day_score + duration_score
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type_score": self.type_score,
            "distance_score": round(self.distance_score, 2),
            "time_score": round(self.time_score, 2),
            "day_score": round(self.day_score, 2),
            "duration_score": round(self.duration_score, 2),
            "total": self.total,
        }


class MatchResult:
    """Single template match result with score"""

    def __init__(
        self,
        template_id: UUID,
        template_name: str,
        match_score: int,
        breakdown: MatchScoreBreakdown,
        template: Dict[str, Any],
    ):
        self.template_id = template_id
        self.template_name = template_name
        self.match_score = match_score
        self.breakdown = breakdown
        self.template = template

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": str(self.template_id),
            "template_name": self.template_name,
            "match_score": self.match_score,
            "breakdown": self.breakdown.to_dict(),
            "template": self.template,
        }


class MatchSuggestion:
    """Grouped match suggestions by quality"""

    def __init__(
        self,
        excellent: List[MatchResult],
        good: List[MatchResult],
        fair: List[MatchResult],
    ):
        self.excellent = excellent
        self.good = good
        self.fair = fair

    def to_dict(self) -> Dict[str, Any]:
        return {
            "excellent": [m.to_dict() for m in self.excellent],
            "good": [m.to_dict() for m in self.good],
            "fair": [m.to_dict() for m in self.fair],
        }


class TemplateMatchingService:
    """Service for matching activities with templates"""

    def __init__(self):
        self.db = SupabaseService()

    def _extract_activity_features(
        self, activity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract matchable features from activity data.

        Args:
            activity_data: Activity data (from form or database)

        Returns:
            Dict with features: activity_type, distance_m, duration_minutes,
            start_time, day_of_week
        """
        # Get activity type (try both field names for compatibility)
        activity_type = activity_data.get("activity_type") or activity_data.get(
            "category"
        )

        # Get distance (might be in metrics or top-level)
        distance_m = None
        if "metrics" in activity_data and isinstance(activity_data["metrics"], dict):
            distance_km = activity_data["metrics"].get("distance_km")
            if distance_km:
                distance_m = distance_km * 1000

        # Get duration
        duration_minutes = activity_data.get("duration_minutes")

        # Get start time
        start_time_str = activity_data.get("start_time")
        start_time = None
        day_of_week = None

        if start_time_str:
            try:
                if isinstance(start_time_str, str):
                    dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                else:
                    dt = start_time_str

                start_time = dt.time()
                # ISO weekday: Monday=1, Sunday=7
                day_of_week = dt.isoweekday()
            except Exception as e:
                logger.warning(
                    "Failed to parse start_time",
                    start_time=start_time_str,
                    error=str(e),
                )

        return {
            "activity_type": activity_type,
            "distance_m": distance_m,
            "duration_minutes": duration_minutes,
            "start_time": start_time,
            "day_of_week": day_of_week,
        }

    def _calculate_type_score(
        self, activity_type: str, template_type: str
    ) -> int:
        """
        Calculate activity type match score.

        Args:
            activity_type: Activity type from activity
            template_type: Activity type from template

        Returns:
            40 points if exact match, 0 otherwise
        """
        if not activity_type or not template_type:
            return 0

        # Exact match required
        if activity_type.lower() == template_type.lower():
            return 40

        return 0

    def _calculate_distance_score(
        self,
        activity_distance_m: Optional[float],
        expected_distance_m: Optional[float],
        tolerance_percent: int,
    ) -> float:
        """
        Calculate distance match score.

        Args:
            activity_distance_m: Actual distance in meters
            expected_distance_m: Expected distance from template
            tolerance_percent: Tolerance percentage (±)

        Returns:
            0-25 points based on how close distance is to expected
        """
        # If template doesn't specify distance, give neutral score
        if expected_distance_m is None:
            return 12.5  # Half points

        # If activity doesn't have distance but template expects it, penalize
        if activity_distance_m is None:
            return 0

        # Calculate percentage difference
        difference = abs(activity_distance_m - expected_distance_m)
        percent_diff = (difference / expected_distance_m) * 100

        # Within tolerance: full points
        if percent_diff <= tolerance_percent:
            return 25.0

        # Outside tolerance: score decays linearly
        # At 2x tolerance: 0 points
        max_diff = tolerance_percent * 2
        if percent_diff >= max_diff:
            return 0

        # Linear decay between tolerance and 2x tolerance
        score = 25.0 * (1 - (percent_diff - tolerance_percent) / tolerance_percent)
        return max(0, score)

    def _calculate_time_score(
        self,
        activity_time: Optional[time],
        typical_time: Optional[time],
        window_hours: int,
    ) -> float:
        """
        Calculate time of day match score.

        Args:
            activity_time: Time of day activity started
            typical_time: Typical start time from template
            window_hours: Time window in hours (±)

        Returns:
            0-20 points based on how close time is to typical
        """
        # If template doesn't specify time, give neutral score
        if typical_time is None:
            return 10.0  # Half points

        # If activity doesn't have time but template expects it, penalize
        if activity_time is None:
            return 0

        # Convert times to minutes since midnight for comparison
        activity_minutes = activity_time.hour * 60 + activity_time.minute
        typical_minutes = typical_time.hour * 60 + typical_time.minute

        # Calculate difference (accounting for day wraparound)
        diff_minutes = abs(activity_minutes - typical_minutes)
        # Handle wraparound (e.g., 23:00 to 01:00 is 2 hours, not 22 hours)
        if diff_minutes > 720:  # 12 hours
            diff_minutes = 1440 - diff_minutes

        # Convert window to minutes
        window_minutes = window_hours * 60

        # Within window: full points
        if diff_minutes <= window_minutes:
            return 20.0

        # Outside window: score decays linearly
        # At 2x window: 0 points
        max_diff = window_minutes * 2
        if diff_minutes >= max_diff:
            return 0

        # Linear decay
        score = 20.0 * (1 - (diff_minutes - window_minutes) / window_minutes)
        return max(0, score)

    def _calculate_day_score(
        self, activity_day: Optional[int], preferred_days: Optional[List[int]]
    ) -> float:
        """
        Calculate day of week match score.

        Args:
            activity_day: Day of week (1=Monday, 7=Sunday)
            preferred_days: List of preferred days from template

        Returns:
            0-10 points based on whether day matches preferences
        """
        # If template doesn't specify preferred days, give neutral score
        if not preferred_days:
            return 5.0  # Half points

        # If activity doesn't have day, penalize
        if activity_day is None:
            return 0

        # Full points if day matches
        if activity_day in preferred_days:
            return 10.0

        return 0

    def _calculate_duration_score(
        self,
        activity_duration: Optional[int],
        expected_duration: Optional[int],
        tolerance_percent: int,
    ) -> float:
        """
        Calculate duration match score.

        Args:
            activity_duration: Actual duration in minutes
            expected_duration: Expected duration from template
            tolerance_percent: Tolerance percentage (±)

        Returns:
            0-5 points based on how close duration is to expected
        """
        # If template doesn't specify duration, give neutral score
        if expected_duration is None:
            return 2.5  # Half points

        # If activity doesn't have duration but template expects it, penalize
        if activity_duration is None:
            return 0

        # Calculate percentage difference
        difference = abs(activity_duration - expected_duration)
        percent_diff = (difference / expected_duration) * 100

        # Within tolerance: full points
        if percent_diff <= tolerance_percent:
            return 5.0

        # Outside tolerance: score decays linearly
        max_diff = tolerance_percent * 2
        if percent_diff >= max_diff:
            return 0

        # Linear decay
        score = 5.0 * (1 - (percent_diff - tolerance_percent) / tolerance_percent)
        return max(0, score)

    def calculate_match_score(
        self, activity_data: Dict[str, Any], template: Dict[str, Any]
    ) -> Tuple[int, MatchScoreBreakdown]:
        """
        Calculate match score for a single template vs activity.

        Args:
            activity_data: Activity data
            template: Template data

        Returns:
            Tuple of (total_score, breakdown)
        """
        logger.info(
            "calculating_match_score",
            template_id=template.get("id"),
            activity_type=activity_data.get("activity_type"),
        )

        # Extract features from activity
        features = self._extract_activity_features(activity_data)

        # Calculate individual scores
        type_score = self._calculate_type_score(
            features["activity_type"], template.get("activity_type")
        )

        distance_score = self._calculate_distance_score(
            features["distance_m"],
            template.get("expected_distance_m"),
            template.get("distance_tolerance_percent", 10),
        )

        time_score = self._calculate_time_score(
            features["start_time"],
            (
                datetime.strptime(template["typical_start_time"], "%H:%M:%S").time()
                if template.get("typical_start_time")
                else None
            ),
            template.get("time_window_hours", 2),
        )

        day_score = self._calculate_day_score(
            features["day_of_week"], template.get("preferred_days")
        )

        duration_score = self._calculate_duration_score(
            features["duration_minutes"],
            template.get("expected_duration_minutes"),
            template.get("duration_tolerance_percent", 15),
        )

        # Build breakdown
        breakdown = MatchScoreBreakdown(
            type_score=type_score,
            distance_score=distance_score,
            time_score=time_score,
            day_score=day_score,
            duration_score=duration_score,
        )

        logger.info(
            "match_score_calculated",
            template_id=template.get("id"),
            total_score=breakdown.total,
            breakdown=breakdown.to_dict(),
        )

        return breakdown.total, breakdown

    async def find_matching_templates(
        self,
        user_id: UUID,
        activity_data: Dict[str, Any],
        limit: int = 10,
    ) -> List[MatchResult]:
        """
        Find all matching templates for an activity.

        Args:
            user_id: User ID for template filtering
            activity_data: Activity data to match against
            limit: Maximum number of matches to return

        Returns:
            List of MatchResult objects sorted by score descending
        """
        logger.info(
            "finding_matching_templates",
            user_id=str(user_id),
            activity_type=activity_data.get("activity_type"),
        )

        # Extract activity type
        features = self._extract_activity_features(activity_data)
        activity_type = features["activity_type"]

        if not activity_type:
            logger.warning("no_activity_type", user_id=str(user_id))
            return []

        # Get all active templates for this user and activity type
        templates, total = await template_service.list_templates(
            user_id=user_id, activity_type=activity_type, is_active=True, limit=100
        )

        if not templates:
            logger.info(
                "no_templates_found",
                user_id=str(user_id),
                activity_type=activity_type,
            )
            return []

        # Calculate score for each template
        matches = []
        for template in templates:
            score, breakdown = self.calculate_match_score(activity_data, template)

            # Filter by template's min_match_score
            min_score = template.get("min_match_score", 70)
            if score >= min_score:
                match = MatchResult(
                    template_id=UUID(template["id"]),
                    template_name=template["template_name"],
                    match_score=score,
                    breakdown=breakdown,
                    template=template,
                )
                matches.append(match)

        # Sort by score descending
        matches.sort(key=lambda m: m.match_score, reverse=True)

        # Limit results
        matches = matches[:limit]

        logger.info(
            "matches_found",
            user_id=str(user_id),
            activity_type=activity_type,
            match_count=len(matches),
        )

        return matches

    async def get_match_suggestions(
        self, user_id: UUID, activity_data: Dict[str, Any]
    ) -> MatchSuggestion:
        """
        Get match suggestions grouped by quality.

        Args:
            user_id: User ID
            activity_data: Activity data

        Returns:
            MatchSuggestion with excellent, good, and fair matches
        """
        logger.info("getting_match_suggestions", user_id=str(user_id))

        # Find all matches
        matches = await self.find_matching_templates(user_id, activity_data)

        # Group by quality
        excellent = [m for m in matches if m.match_score >= 90]
        good = [m for m in matches if 70 <= m.match_score < 90]
        fair = [m for m in matches if 50 <= m.match_score < 70]

        suggestion = MatchSuggestion(excellent=excellent, good=good, fair=fair)

        logger.info(
            "suggestions_grouped",
            user_id=str(user_id),
            excellent_count=len(excellent),
            good_count=len(good),
            fair_count=len(fair),
        )

        return suggestion

    async def apply_template_to_activity(
        self,
        user_id: UUID,
        template_id: UUID,
        activity_id: UUID,
        match_score: Optional[int] = None,
        match_method: str = "manual",
    ) -> Dict[str, Any]:
        """
        Apply a template to an activity.

        Updates activity with:
        - template_id
        - template_match_score
        - template_applied_at
        - Copies default_metrics if activity metrics empty
        - Copies default_notes if activity notes empty

        Args:
            user_id: User ID (for ownership verification)
            template_id: Template to apply
            activity_id: Activity to update
            match_score: Match score (if auto-matched)
            match_method: 'manual' or 'auto'

        Returns:
            Updated activity data
        """
        logger.info(
            "applying_template_to_activity",
            user_id=str(user_id),
            template_id=str(template_id),
            activity_id=str(activity_id),
            match_method=match_method,
        )

        # Get template (with ownership verification)
        template = await template_service.get_template(template_id, user_id)

        # Get activity (verify ownership)
        activity_response = (
            self.db.supabase.table("activities")
            .select("*")
            .eq("id", str(activity_id))
            .eq("user_id", str(user_id))
            .execute()
        )

        if not activity_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
            )

        activity = activity_response.data[0]

        # Build update payload
        updates = {
            "template_id": str(template_id),
            "template_match_score": match_score,
            "template_applied_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Copy default metrics if activity metrics is empty
        if not activity.get("metrics") or activity.get("metrics") == {}:
            if template.get("default_metrics"):
                updates["metrics"] = template["default_metrics"]

        # Copy default notes if activity notes is empty
        if not activity.get("notes"):
            if template.get("default_notes"):
                updates["notes"] = template["default_notes"]

        # Update activity
        update_response = (
            self.db.supabase.table("activities")
            .update(updates)
            .eq("id", str(activity_id))
            .eq("user_id", str(user_id))
            .execute()
        )

        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update activity",
            )

        updated_activity = update_response.data[0]

        # Update template usage stats
        self.db.supabase.table("activity_templates").update(
            {
                "use_count": template["use_count"] + 1,
                "last_used_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", str(template_id)).execute()

        # Record match decision
        await self.record_match_decision(
            user_id=user_id,
            activity_id=activity_id,
            template_id=template_id,
            match_score=match_score or 0,
            match_method=match_method,
            user_decision="accepted",
        )

        logger.info(
            "template_applied",
            user_id=str(user_id),
            template_id=str(template_id),
            activity_id=str(activity_id),
        )

        return updated_activity

    async def record_match_decision(
        self,
        user_id: UUID,
        activity_id: UUID,
        template_id: UUID,
        match_score: int,
        match_method: str,
        user_decision: str,
    ) -> Dict[str, Any]:
        """
        Record a match decision in activity_template_matches table.

        Args:
            user_id: User ID
            activity_id: Activity ID
            template_id: Template ID
            match_score: Match score
            match_method: 'manual' or 'auto'
            user_decision: 'accepted', 'rejected', or 'ignored'

        Returns:
            Created match record
        """
        logger.info(
            "recording_match_decision",
            user_id=str(user_id),
            activity_id=str(activity_id),
            template_id=str(template_id),
            decision=user_decision,
        )

        record = {
            "activity_id": str(activity_id),
            "template_id": str(template_id),
            "match_score": match_score,
            "match_method": match_method,
            "user_decision": user_decision,
            "decided_at": datetime.utcnow().isoformat(),
        }

        response = self.db.supabase.table("activity_template_matches").insert(record).execute()

        if not response.data:
            logger.error(
                "failed_to_record_decision",
                user_id=str(user_id),
                activity_id=str(activity_id),
                template_id=str(template_id),
            )
            # Don't raise - this is non-critical
            return {}

        logger.info(
            "match_decision_recorded",
            user_id=str(user_id),
            activity_id=str(activity_id),
            template_id=str(template_id),
        )

        return response.data[0]


# Singleton instance
template_matching_service = TemplateMatchingService()
