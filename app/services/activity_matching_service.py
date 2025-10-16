"""
Activity Matching Service

Matches logged activities to planned session_instances and calculates adherence.
This service bridges the gap between:
- User's actual logged activities (activities table)
- User's planned training sessions (session_instances table)

Matching Algorithm:
1. Find planned sessions for the same day as logged activity
2. Calculate similarity score based on:
   - Exercise overlap (did they do planned exercises?)
   - Volume match (sets × reps close to plan?)
   - Timing match (did they train at planned time of day?)
3. Link activity to best matching session_instance
4. Create adherence_record with status (completed/similar/partial/skipped)
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
from uuid import UUID
import structlog

from app.services.supabase_service import SupabaseService

logger = structlog.get_logger()


class ActivityMatchingService:
    """Matches logged activities to planned sessions and calculates adherence"""

    def __init__(self, db: Optional[SupabaseService] = None):
        self.db = db or SupabaseService()

    async def match_activity_to_session(
        self,
        activity_id: str,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Match a logged activity to a planned session_instance.

        Args:
            activity_id: UUID of the logged activity
            user_id: User UUID

        Returns:
            Adherence record dict if matched, None if no match found

        Flow:
        1. Fetch logged activity details
        2. Find planned sessions for that day
        3. Calculate similarity scores
        4. Link to best match (if score > threshold)
        5. Create adherence_record
        """
        client = self.db.client

        logger.info(
            "matching_activity_to_session",
            activity_id=activity_id,
            user_id=user_id,
        )

        # Step 1: Fetch logged activity
        activity_result = (
            client.table("activities")
            .select("*")
            .eq("id", activity_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )

        if not activity_result.data:
            logger.warning("activity_not_found", activity_id=activity_id)
            return None

        activity = activity_result.data[0]
        activity_date = datetime.fromisoformat(
            activity["start_time"].replace("Z", "+00:00")
        ).date()

        logger.info(
            "fetched_activity",
            activity_id=activity_id,
            activity_date=str(activity_date),
            category=activity.get("category"),
        )

        # Step 2: Find planned sessions for that day
        # First, get user's active program
        program_result = (
            client.table("programs")
            .select("id, program_start_date, program_duration_weeks")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not program_result.data:
            logger.warning("no_active_program", user_id=user_id)
            return None

        program = program_result.data[0]
        program_id = program["id"]
        program_start = date.fromisoformat(program["program_start_date"])

        # Calculate week_index and day_index
        days_since_start = (activity_date - program_start).days
        if days_since_start < 0:
            logger.warning(
                "activity_before_program_start",
                activity_date=str(activity_date),
                program_start=str(program_start),
            )
            return None

        week_index = days_since_start // 7
        day_index = days_since_start % 7

        logger.info(
            "calculated_program_day",
            week_index=week_index,
            day_index=day_index,
            program_id=program_id,
        )

        # Fetch planned sessions for this day
        # (session_instances repeat weekly, so we use week_index % repeating_weeks)
        # For now, assume week_index 0 (first week pattern repeats)
        sessions_result = (
            client.table("session_instances")
            .select("*, exercise_plan_items(*)")
            .eq("program_id", program_id)
            .eq("week_index", 0)  # Sessions repeat weekly
            .eq("day_index", day_index)
            .eq("state", "planned")
            .execute()
        )

        if not sessions_result.data:
            logger.info(
                "no_planned_sessions_for_day",
                day_index=day_index,
                program_id=program_id,
            )
            return None

        # Step 3: Calculate similarity scores for each planned session
        best_match = None
        best_score = 0.0
        similarity_threshold = 0.3  # Minimum 30% similarity to consider a match

        for session in sessions_result.data:
            score = self._calculate_similarity_score(activity, session)
            logger.info(
                "calculated_similarity",
                session_id=session["id"],
                session_name=session.get("session_name"),
                score=score,
            )

            if score > best_score:
                best_score = score
                best_match = session

        if best_score < similarity_threshold:
            logger.info(
                "no_match_above_threshold",
                best_score=best_score,
                threshold=similarity_threshold,
            )
            return None

        # Step 4: Link activity to session
        logger.info(
            "matched_activity_to_session",
            activity_id=activity_id,
            session_id=best_match["id"],
            similarity_score=best_score,
        )

        # Update activity with planned_session_instance_id
        client.table("activities").update(
            {"planned_session_instance_id": best_match["id"]}
        ).eq("id", activity_id).execute()

        # Step 5: Create adherence record
        adherence_status = self._determine_adherence_status(best_score)

        adherence_data = {
            "user_id": user_id,
            "program_id": program_id,
            "date": activity_date.isoformat(),
            "category": "training",
            "planned_ref_table": "session_instances",
            "planned_ref_id": best_match["id"],
            "actual_ref_table": "activities",
            "actual_ref_id": activity_id,
            "status": adherence_status,
            "similarity_score": best_score,
            "details": {
                "matched_session": best_match.get("session_name"),
                "activity_category": activity.get("category"),
                "exercise_overlap": self._extract_exercise_overlap(activity, best_match),
            },
        }

        adherence_result = (
            client.table("adherence_records").insert(adherence_data).execute()
        )

        if not adherence_result.data:
            logger.error("failed_to_create_adherence_record", activity_id=activity_id)
            return None

        logger.info(
            "adherence_record_created",
            adherence_id=adherence_result.data[0]["id"],
            status=adherence_status,
            similarity_score=best_score,
        )

        return adherence_result.data[0]

    def _calculate_similarity_score(
        self, activity: Dict[str, Any], session: Dict[str, Any]
    ) -> float:
        """
        Calculate similarity between logged activity and planned session.

        Scoring factors:
        - Category match (40%): Is it a resistance training activity?
        - Exercise overlap (30%): Did they do the planned exercises?
        - Volume match (20%): Sets × reps close to plan?
        - Timing match (10%): Did they train at planned time of day?

        Args:
            activity: Logged activity dict
            session: Planned session_instance dict (with exercise_plan_items)

        Returns:
            Similarity score (0.0 to 1.0)
        """
        score = 0.0

        # Factor 1: Category match (40%)
        activity_category = activity.get("category", "")
        session_kind = session.get("session_kind", "")

        if "strength" in activity_category or "resistance" in activity_category:
            if session_kind == "resistance":
                score += 0.4
        elif "cardio" in activity_category:
            if session_kind == "cardio":
                score += 0.4

        # Factor 2: Exercise overlap (30%)
        # Compare exercises in logged activity metrics to planned exercises
        activity_exercises = self._extract_logged_exercises(activity)
        planned_exercises = self._extract_planned_exercises(session)

        if activity_exercises and planned_exercises:
            overlap_score = self._calculate_exercise_overlap(
                activity_exercises, planned_exercises
            )
            score += overlap_score * 0.3

        # Factor 3: Volume match (20%)
        # Compare total volume (sets × reps × weight) if available
        activity_volume = self._calculate_activity_volume(activity)
        planned_volume = self._calculate_planned_volume(session)

        if activity_volume > 0 and planned_volume > 0:
            volume_ratio = min(activity_volume, planned_volume) / max(
                activity_volume, planned_volume
            )
            score += volume_ratio * 0.2

        # Factor 4: Timing match (10%)
        # Compare time of day
        activity_time = self._extract_time_of_day(activity)
        planned_time = session.get("time_of_day")

        if activity_time and planned_time and activity_time == planned_time:
            score += 0.1

        return min(score, 1.0)  # Cap at 1.0

    def _extract_logged_exercises(self, activity: Dict[str, Any]) -> List[str]:
        """Extract exercise names from logged activity metrics"""
        metrics = activity.get("metrics", {})
        if not metrics:
            return []

        # Handle strength training format: {"exercises": [...]}
        exercises = metrics.get("exercises", [])
        if isinstance(exercises, list):
            return [ex.get("name", "").lower() for ex in exercises if ex.get("name")]

        return []

    def _extract_planned_exercises(self, session: Dict[str, Any]) -> List[str]:
        """Extract exercise names from planned session"""
        exercise_items = session.get("exercise_plan_items", [])
        if not exercise_items:
            return []

        return [item.get("name", "").lower() for item in exercise_items]

    def _calculate_exercise_overlap(
        self, logged: List[str], planned: List[str]
    ) -> float:
        """
        Calculate overlap between logged and planned exercises.

        Returns:
            Overlap score (0.0 to 1.0)
        """
        if not logged or not planned:
            return 0.0

        # Normalize exercise names (lowercase, strip whitespace)
        logged_set = set(ex.strip().lower() for ex in logged)
        planned_set = set(ex.strip().lower() for ex in planned)

        # Calculate Jaccard similarity: intersection / union
        intersection = logged_set.intersection(planned_set)
        union = logged_set.union(planned_set)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _calculate_activity_volume(self, activity: Dict[str, Any]) -> float:
        """Calculate total volume from logged activity"""
        metrics = activity.get("metrics", {})
        if not metrics:
            return 0.0

        exercises = metrics.get("exercises", [])
        if not isinstance(exercises, list):
            return 0.0

        total_volume = 0.0
        for ex in exercises:
            sets = ex.get("sets", 0)
            reps = ex.get("reps", 0)
            weight_kg = ex.get("weight_kg", 0)

            # Volume = sets × reps × weight
            total_volume += sets * reps * weight_kg

        return total_volume

    def _calculate_planned_volume(self, session: Dict[str, Any]) -> float:
        """Calculate total planned volume from session"""
        exercise_items = session.get("exercise_plan_items", [])
        if not exercise_items:
            return 0.0

        total_volume = 0.0
        for item in exercise_items:
            sets = item.get("sets", 0)
            # Parse rep_range (e.g., "8-12" → take midpoint)
            rep_range = item.get("rep_range", "0")
            reps = self._parse_rep_range(rep_range)

            # Weight not available in plan, so estimate based on typical volume
            # For now, just use sets × reps as a proxy
            total_volume += sets * reps

        return total_volume

    def _parse_rep_range(self, rep_range: str) -> float:
        """Parse rep range string (e.g., '8-12') to midpoint"""
        if not rep_range:
            return 0.0

        try:
            if "-" in rep_range:
                low, high = rep_range.split("-")
                return (int(low.strip()) + int(high.strip())) / 2
            else:
                return float(rep_range.strip())
        except (ValueError, AttributeError):
            return 0.0

    def _extract_time_of_day(self, activity: Dict[str, Any]) -> Optional[str]:
        """Extract time of day from activity start_time"""
        start_time_str = activity.get("start_time")
        if not start_time_str:
            return None

        try:
            start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            hour = start_time.hour

            # Categorize by time of day
            if 5 <= hour < 12:
                return "morning"
            elif 12 <= hour < 17:
                return "afternoon"
            elif 17 <= hour < 21:
                return "evening"
            else:
                return "night"
        except (ValueError, AttributeError):
            return None

    def _determine_adherence_status(self, similarity_score: float) -> str:
        """
        Determine adherence status based on similarity score.

        Thresholds:
        - 0.8+ = completed (excellent match)
        - 0.6-0.8 = similar (good match)
        - 0.3-0.6 = partial (some overlap)
        - <0.3 = skipped (no match)

        Args:
            similarity_score: Score from 0.0 to 1.0

        Returns:
            Status string: "completed", "similar", "partial", or "skipped"
        """
        if similarity_score >= 0.8:
            return "completed"
        elif similarity_score >= 0.6:
            return "similar"
        elif similarity_score >= 0.3:
            return "partial"
        else:
            return "skipped"

    def _extract_exercise_overlap(
        self, activity: Dict[str, Any], session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract exercise overlap details for adherence record"""
        logged = self._extract_logged_exercises(activity)
        planned = self._extract_planned_exercises(session)

        logged_set = set(logged)
        planned_set = set(planned)

        matched = list(logged_set.intersection(planned_set))
        missed = list(planned_set.difference(logged_set))
        extra = list(logged_set.difference(planned_set))

        return {
            "matched_exercises": matched,
            "missed_exercises": missed,
            "extra_exercises": extra,
            "total_logged": len(logged),
            "total_planned": len(planned),
        }

    async def match_skipped_sessions(
        self, user_id: str, target_date: date
    ) -> List[Dict[str, Any]]:
        """
        Find planned sessions that were not completed on a given day.

        Args:
            user_id: User UUID
            target_date: Date to check

        Returns:
            List of adherence records for skipped sessions
        """
        client = self.db.client

        logger.info(
            "checking_for_skipped_sessions",
            user_id=user_id,
            date=str(target_date),
        )

        # Get user's active program
        program_result = (
            client.table("programs")
            .select("id, program_start_date")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not program_result.data:
            logger.warning("no_active_program", user_id=user_id)
            return []

        program = program_result.data[0]
        program_id = program["id"]
        program_start = date.fromisoformat(program["program_start_date"])

        # Calculate day_index
        days_since_start = (target_date - program_start).days
        if days_since_start < 0:
            return []

        day_index = days_since_start % 7

        # Fetch planned sessions for this day
        sessions_result = (
            client.table("session_instances")
            .select("id, session_name, session_kind")
            .eq("program_id", program_id)
            .eq("week_index", 0)
            .eq("day_index", day_index)
            .eq("state", "planned")
            .execute()
        )

        if not sessions_result.data:
            logger.info("no_planned_sessions_for_day", day_index=day_index)
            return []

        # Check which sessions have adherence records
        skipped_records = []

        for session in sessions_result.data:
            # Check if adherence record exists
            adherence_result = (
                client.table("adherence_records")
                .select("id")
                .eq("user_id", user_id)
                .eq("date", target_date.isoformat())
                .eq("planned_ref_id", session["id"])
                .execute()
            )

            if not adherence_result.data:
                # No adherence record = session was skipped
                logger.info(
                    "session_skipped",
                    session_id=session["id"],
                    session_name=session.get("session_name"),
                )

                # Create adherence record for skipped session
                adherence_data = {
                    "user_id": user_id,
                    "program_id": program_id,
                    "date": target_date.isoformat(),
                    "category": "training",
                    "planned_ref_table": "session_instances",
                    "planned_ref_id": session["id"],
                    "actual_ref_table": None,
                    "actual_ref_id": None,
                    "status": "skipped",
                    "similarity_score": 0.0,
                    "details": {"reason": "no_activity_logged"},
                }

                adherence_record = (
                    client.table("adherence_records").insert(adherence_data).execute()
                )

                if adherence_record.data:
                    skipped_records.append(adherence_record.data[0])

        logger.info(
            "skipped_sessions_processed",
            user_id=user_id,
            date=str(target_date),
            skipped_count=len(skipped_records),
        )

        return skipped_records


# Global singleton instance
activity_matching_service = ActivityMatchingService()
