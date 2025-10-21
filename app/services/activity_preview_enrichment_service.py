"""
Activity Preview Enrichment Service

Enhances activity log previews with:
- Personalized calorie estimates based on user weight + fitness level
- Matched activities from user history
- METs adjustments for fitness level
- Editable fields marked
- Validation warnings

This service runs BEFORE showing preview to user, allowing them to:
- See personalized calorie estimates
- See how their activity compares to past performance
- Edit duration/intensity if estimate seems off
- Get fitness-adjusted METs values

Design Philosophy:
- Same user, same activity → different calories based on fitness improvement
- Beginner running 5k → higher METs (harder effort) → more calories
- Athlete running 5k → lower METs (easier effort) → fewer calories
- User history provides baseline for "normal" intensity
"""

import structlog
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import difflib

logger = structlog.get_logger()


# ============================================================================
# SINGLETON PATTERN
# ============================================================================

_activity_enrichment_service = None


def get_activity_preview_enrichment_service(supabase_client):
    """
    Get singleton instance of ActivityPreviewEnrichmentService.

    Args:
        supabase_client: Supabase client for database queries

    Returns:
        ActivityPreviewEnrichmentService instance
    """
    global _activity_enrichment_service
    if _activity_enrichment_service is None:
        _activity_enrichment_service = ActivityPreviewEnrichmentService(supabase_client)
    return _activity_enrichment_service


# ============================================================================
# FITNESS LEVEL ADJUSTMENTS
# ============================================================================

FITNESS_METS_MULTIPLIERS = {
    # Fitness level → METs multiplier for same activity
    # Beginners work harder (higher HR, more effort) for same activity
    # Advanced athletes work less hard (lower HR, more efficient)
    "beginner": 1.15,        # 15% harder
    "intermediate": 1.0,     # Baseline
    "advanced": 0.90,        # 10% easier
    "expert": 0.85           # 15% easier
}

INTENSITY_METS_MULTIPLIERS = {
    # User-reported intensity → METs adjustment
    "low": 0.75,
    "moderate": 1.0,
    "high": 1.3,
    "very_high": 1.5
}


# ============================================================================
# ENRICHMENT SERVICE
# ============================================================================

class ActivityPreviewEnrichmentService:
    """
    Enriches activity log previews with personalization and editability metadata.

    Key Features:
    - Personalized calorie estimates based on user weight + fitness level
    - Activity matching against user history
    - Fitness-adjusted METs values
    - Top 3 similar activities for reference
    - Editable field markers
    - Validation warnings (unrealistic duration, missing data)
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def enrich_activity_preview(
        self,
        structured_data: Dict[str, Any],
        user_id: str
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Enrich activity preview with personalized estimates and history matching.

        Args:
            structured_data: LLM-extracted data with activity details
            user_id: User UUID for personalization

        Returns:
            Tuple of (enriched_data, warnings)

        enriched_data format:
        {
            "activity_name": "Morning Run",
            "category": "cardio_steady_state",
            "duration_minutes": 30,
            "intensity": "moderate",
            "matched_activity": {
                "id": "uuid-123",
                "activity_name": "Morning Run",
                "avg_duration_minutes": 28,
                "avg_calories": 285,
                "times_logged": 12,
                "last_logged": "2025-10-15"
            },
            "match_reason": "user_history",  # or "category_default"
            "match_confidence": 92,
            "personalized_calories": {
                "estimated": 295,
                "base_mets": 8.0,
                "adjusted_mets": 9.2,  # Fitness-adjusted
                "calculation_method": "user_weight_and_fitness",
                "factors": {
                    "user_weight_kg": 70,
                    "fitness_level": "intermediate",
                    "fitness_multiplier": 1.0,
                    "intensity_multiplier": 1.0
                }
            },
            "similar_activities": [
                {
                    "id": "uuid-456",
                    "activity_name": "Evening Run",
                    "avg_calories": 310
                }
            ],
            "editable_fields": ["duration_minutes", "intensity", "activity_name"],
            "warnings": [],
            "notes": null
        }
        """
        logger.info("[ActivityEnrichment] 🏃 Enriching activity preview with personalization")

        activity_name = structured_data.get("activity_name", "Unknown Activity")
        category = structured_data.get("category", "other")
        duration_minutes = structured_data.get("duration_minutes", 0)
        intensity = structured_data.get("intensity", "moderate")

        logger.info(
            f"[ActivityEnrichment] Processing: '{activity_name}' "
            f"({category}, {duration_minutes}min, {intensity})"
        )

        warnings = []
        enriched_data = dict(structured_data)  # Copy original data

        # STEP 1: Get user profile for personalization
        user_profile = await self._get_user_profile(user_id)
        if not user_profile:
            logger.warning("[ActivityEnrichment] ⚠️ User profile not found - using defaults")
            user_profile = {
                "weight_kg": 70,  # Default
                "fitness_level": "intermediate",
                "experience_level": "intermediate"
            }

        # STEP 2: Search for matching activity in user history
        match_result = await self._search_user_activity_history(
            user_id=user_id,
            activity_name=activity_name,
            category=category,
            top_n=3
        )

        if match_result:
            matched_activity, match_score, match_reason, similar_activities = match_result
            logger.info(
                f"[ActivityEnrichment] ✅ Found match: '{matched_activity.get('activity_name')}' "
                f"(confidence: {match_score}%, reason: {match_reason})"
            )

            enriched_data["matched_activity"] = {
                "id": matched_activity.get("id"),
                "activity_name": matched_activity.get("activity_name"),
                "avg_duration_minutes": matched_activity.get("avg_duration_minutes"),
                "avg_calories": matched_activity.get("avg_calories"),
                "times_logged": matched_activity.get("times_logged"),
                "last_logged": matched_activity.get("last_logged")
            }
            enriched_data["match_reason"] = match_reason
            enriched_data["match_confidence"] = match_score
            enriched_data["similar_activities"] = similar_activities

            # Add context warning if duration significantly different
            if matched_activity.get("avg_duration_minutes"):
                avg_duration = matched_activity["avg_duration_minutes"]
                diff_pct = abs(duration_minutes - avg_duration) / avg_duration * 100
                if diff_pct > 50:
                    warnings.append(
                        f"Duration ({duration_minutes}min) differs significantly from your usual "
                        f"({avg_duration}min). Verify this is correct."
                    )
        else:
            logger.info(f"[ActivityEnrichment] ℹ️ No user history for '{activity_name}' - using defaults")
            enriched_data["matched_activity"] = None
            enriched_data["match_reason"] = "category_default"
            enriched_data["match_confidence"] = 50
            enriched_data["similar_activities"] = []

        # STEP 3: Calculate personalized calories
        personalized_calories = await self._calculate_personalized_calories(
            activity_name=activity_name,
            category=category,
            duration_minutes=duration_minutes,
            intensity=intensity,
            user_profile=user_profile,
            user_history=match_result[0] if match_result else None
        )

        enriched_data["personalized_calories"] = personalized_calories

        # STEP 4: Validation warnings
        validation_warnings = self._validate_activity_data(
            activity_name=activity_name,
            duration_minutes=duration_minutes,
            estimated_calories=personalized_calories["estimated"],
            category=category
        )
        warnings.extend(validation_warnings)

        # STEP 5: Mark editable fields
        enriched_data["editable_fields"] = [
            "duration_minutes",
            "intensity",
            "activity_name",
            "notes"
        ]

        # STEP 6: Add warnings array
        enriched_data["warnings"] = warnings

        logger.info(
            f"[ActivityEnrichment] ✅ Enrichment complete: "
            f"{personalized_calories['estimated']} cal estimated "
            f"({len(warnings)} warnings)"
        )

        return enriched_data, warnings

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch user profile for personalization."""
        try:
            result = self.supabase.table("profiles")\
                .select("weight_kg, fitness_level, experience_level")\
                .eq("id", user_id)\
                .single()\
                .execute()

            if not result.data:
                return None

            profile = result.data

            # Map experience_level to fitness_level if needed
            fitness_level = profile.get("fitness_level") or profile.get("experience_level", "intermediate")

            return {
                "weight_kg": profile.get("weight_kg", 70),
                "fitness_level": fitness_level,
                "experience_level": profile.get("experience_level", "intermediate")
            }

        except Exception as e:
            logger.error(f"[ActivityEnrichment] Failed to fetch user profile: {e}")
            return None

    async def _search_user_activity_history(
        self,
        user_id: str,
        activity_name: str,
        category: str,
        top_n: int = 3
    ) -> Optional[Tuple[Dict[str, Any], int, str, List[Dict[str, Any]]]]:
        """
        Search user's activity history for matching activities.

        Returns:
            Tuple of (matched_activity, confidence_score, match_reason, similar_activities)
            or None if no matches found
        """
        try:
            # Fetch user's past activities (last 90 days, same category)
            ninety_days_ago = (datetime.utcnow() - timedelta(days=90)).isoformat()

            result = self.supabase.table("activities")\
                .select("id, activity_name, category, duration_minutes, calories_burned, created_at")\
                .eq("user_id", user_id)\
                .eq("category", category)\
                .is_("deleted_at", "null")\
                .gte("created_at", ninety_days_ago)\
                .execute()

            if not result.data or len(result.data) == 0:
                logger.info(f"[ActivityEnrichment] No activity history in category '{category}'")
                return None

            activities = result.data

            # Group by activity_name and calculate averages
            activity_groups = {}
            for activity in activities:
                name = activity["activity_name"]
                if name not in activity_groups:
                    activity_groups[name] = {
                        "activity_name": name,
                        "category": category,
                        "durations": [],
                        "calories": [],
                        "ids": []
                    }

                activity_groups[name]["durations"].append(activity["duration_minutes"])
                activity_groups[name]["calories"].append(activity["calories_burned"])
                activity_groups[name]["ids"].append(activity["id"])

            # Calculate averages for each group
            activity_summaries = []
            for name, group in activity_groups.items():
                avg_duration = sum(group["durations"]) / len(group["durations"])
                avg_calories = sum(group["calories"]) / len(group["calories"])
                times_logged = len(group["durations"])

                activity_summaries.append({
                    "id": group["ids"][0],  # Most recent ID
                    "activity_name": name,
                    "category": group["category"],
                    "avg_duration_minutes": round(avg_duration),
                    "avg_calories": round(avg_calories),
                    "times_logged": times_logged,
                    "last_logged": activities[0]["created_at"][:10]  # Date only
                })

            # Find best match using fuzzy string matching
            best_match = None
            best_score = 0
            match_reason = "fuzzy_search"

            for activity_summary in activity_summaries:
                # Exact match
                if activity_summary["activity_name"].lower() == activity_name.lower():
                    best_match = activity_summary
                    best_score = 100
                    match_reason = "user_history"
                    break

                # Fuzzy match
                similarity = difflib.SequenceMatcher(
                    None,
                    activity_name.lower(),
                    activity_summary["activity_name"].lower()
                ).ratio()

                score = int(similarity * 100)

                if score > best_score and score >= 70:  # 70% threshold
                    best_match = activity_summary
                    best_score = score
                    match_reason = "user_history" if score >= 85 else "fuzzy_search"

            if not best_match:
                logger.info(f"[ActivityEnrichment] No fuzzy match found (best score < 70%)")
                return None

            # Get similar activities (excluding the best match)
            similar_activities = [
                {
                    "id": activity["id"],
                    "activity_name": activity["activity_name"],
                    "avg_calories": activity["avg_calories"]
                }
                for activity in activity_summaries
                if activity["activity_name"] != best_match["activity_name"]
            ][:top_n - 1]

            logger.info(
                f"[ActivityEnrichment] Found match: '{best_match['activity_name']}' "
                f"(score: {best_score}%, logged {best_match['times_logged']}× before)"
            )

            return best_match, best_score, match_reason, similar_activities

        except Exception as e:
            logger.error(f"[ActivityEnrichment] Failed to search activity history: {e}")
            return None

    async def _calculate_personalized_calories(
        self,
        activity_name: str,
        category: str,
        duration_minutes: int,
        intensity: str,
        user_profile: Dict[str, Any],
        user_history: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate personalized calorie estimate.

        Personalization factors:
        1. User weight (heavier = more calories)
        2. Fitness level (beginner = harder effort = more calories for same activity)
        3. Intensity (user-reported)
        4. User history (if available, use their typical calories as baseline)
        """
        from app.services.calorie_calculator import lookup_mets, calculate_calories

        weight_kg = user_profile.get("weight_kg", 70)
        fitness_level = user_profile.get("fitness_level", "intermediate")

        # STEP 1: Get base METs value
        base_mets, matched_description = lookup_mets(activity_name, category)

        # STEP 2: Adjust METs for fitness level
        fitness_multiplier = FITNESS_METS_MULTIPLIERS.get(fitness_level, 1.0)

        # STEP 3: Adjust for intensity
        intensity_multiplier = INTENSITY_METS_MULTIPLIERS.get(intensity, 1.0)

        # STEP 4: Calculate adjusted METs
        adjusted_mets = base_mets * fitness_multiplier * intensity_multiplier

        # STEP 5: Calculate calories
        estimated_calories = calculate_calories(
            mets=adjusted_mets,
            weight_kg=weight_kg,
            duration_minutes=duration_minutes
        )

        calculation_method = "user_weight_and_fitness"

        # STEP 6: If user history exists, blend estimate with historical average
        if user_history and user_history.get("avg_calories"):
            historical_calories = user_history["avg_calories"]
            historical_duration = user_history["avg_duration_minutes"]

            # Scale historical calories to current duration
            if historical_duration > 0:
                scaled_historical_calories = int(
                    historical_calories * (duration_minutes / historical_duration)
                )

                # Blend: 70% formula + 30% history
                blended_calories = int(estimated_calories * 0.7 + scaled_historical_calories * 0.3)

                logger.info(
                    f"[ActivityEnrichment] Blended estimate: "
                    f"formula={estimated_calories}, history={scaled_historical_calories}, "
                    f"blended={blended_calories}"
                )

                estimated_calories = blended_calories
                calculation_method = "blended_formula_and_history"

        return {
            "estimated": estimated_calories,
            "base_mets": round(base_mets, 1),
            "adjusted_mets": round(adjusted_mets, 1),
            "calculation_method": calculation_method,
            "factors": {
                "user_weight_kg": weight_kg,
                "fitness_level": fitness_level,
                "fitness_multiplier": fitness_multiplier,
                "intensity": intensity,
                "intensity_multiplier": intensity_multiplier
            }
        }

    def _validate_activity_data(
        self,
        activity_name: str,
        duration_minutes: int,
        estimated_calories: int,
        category: str
    ) -> List[str]:
        """
        Validate activity data and return warnings.

        Checks for:
        - Unrealistic durations (> 4 hours)
        - Very high calorie burns (> 2000 cal suggests miscalculation)
        - Very short durations (< 5 min)
        """
        warnings = []

        # Duration validation
        if duration_minutes > 240:  # > 4 hours
            warnings.append(
                f"Duration ({duration_minutes} min) is very long. "
                f"Verify this is correct."
            )
        elif duration_minutes < 5:
            warnings.append(
                f"Duration ({duration_minutes} min) is very short. "
                f"Consider adjusting."
            )

        # Calorie validation
        if estimated_calories > 2000:
            warnings.append(
                f"Estimated calories ({estimated_calories}) is very high. "
                f"Verify intensity and duration are correct."
            )

        # Missing data warnings
        if not activity_name or activity_name == "Unknown Activity":
            warnings.append("Activity name is missing - please add a descriptive name.")

        return warnings
