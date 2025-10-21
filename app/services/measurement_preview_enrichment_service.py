"""
Measurement Preview Enrichment Service

Enhances measurement (weight/body fat) log previews with:
- Trend analysis (↑/↓ from last week, last month)
- Anomaly detection (physiologically impossible changes)
- Validation warnings (extreme changes, missing data)
- Historical context (progress since start, typical range)

This service runs BEFORE showing preview to user, allowing them to:
- See how this measurement compares to their history
- Catch data entry errors (e.g., 50 lbs instead of 150 lbs)
- Understand their progress trend
- Verify unusual measurements before logging

Design Philosophy:
- Prevent data corruption from typos (150 → 50, 180 → 80)
- Provide immediate context without requiring navigation
- Catch physiologically impossible changes (>3kg/day)
- Show progress to motivate users
"""

import structlog
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

logger = structlog.get_logger()


# ============================================================================
# VALIDATION THRESHOLDS
# ============================================================================

# Maximum physiologically possible weight changes
MAX_WEIGHT_CHANGE_PER_DAY_KG = 3.0      # ~6.6 lbs (extreme but possible with water weight)
MAX_WEIGHT_CHANGE_PER_WEEK_KG = 5.0     # ~11 lbs (very aggressive but possible)
MAX_WEIGHT_CHANGE_PER_MONTH_KG = 10.0   # ~22 lbs (aggressive but achievable)

# Body fat percentage validation
MAX_BODY_FAT_CHANGE_PER_WEEK_PCT = 2.0  # 2% per week is extreme but possible
MAX_BODY_FAT_CHANGE_PER_MONTH_PCT = 5.0 # 5% per month is very aggressive

# Weight range validation (database has 30-300kg, but these are "likely typo" thresholds)
TYPICAL_WEIGHT_RANGE_KG = (40.0, 250.0)  # Outside this = likely typo

# Body fat range validation (database has 3-60%, but these are "unusual" thresholds)
TYPICAL_BODY_FAT_RANGE_PCT = (5.0, 50.0)  # Outside this = unusual but possible


# ============================================================================
# SINGLETON PATTERN
# ============================================================================

_measurement_enrichment_service = None


def get_measurement_preview_enrichment_service(supabase_client):
    """
    Get singleton instance of MeasurementPreviewEnrichmentService.

    Args:
        supabase_client: Supabase client for database queries

    Returns:
        MeasurementPreviewEnrichmentService instance
    """
    global _measurement_enrichment_service
    if _measurement_enrichment_service is None:
        _measurement_enrichment_service = MeasurementPreviewEnrichmentService(supabase_client)
    return _measurement_enrichment_service


# ============================================================================
# ENRICHMENT SERVICE
# ============================================================================

class MeasurementPreviewEnrichmentService:
    """
    Enriches measurement log previews with validation and trend analysis.

    Key Features:
    - Detects physiologically impossible changes (>3kg/day)
    - Calculates trend from last measurement
    - Shows progress since start
    - Identifies likely typos (150 → 50)
    - Provides context (you usually weigh X kg)
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def enrich_measurement_preview(
        self,
        structured_data: Dict[str, Any],
        user_id: str
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Enrich measurement preview with trend analysis and validation.

        Args:
            structured_data: LLM-extracted data with measurement details
            user_id: User UUID for history lookup

        Returns:
            Tuple of (enriched_data, warnings)

        enriched_data format:
        {
            "weight_kg": 72.5,
            "body_fat_percentage": 18.5,
            "recorded_at": "2025-10-21T10:00:00Z",
            "notes": "Morning weight",
            "trend_analysis": {
                "last_measurement": {
                    "weight_kg": 73.2,
                    "recorded_at": "2025-10-14T10:00:00Z",
                    "days_ago": 7
                },
                "change_from_last": {
                    "weight_kg": -0.7,
                    "weight_direction": "down",  # "up" | "down" | "stable"
                    "display_text": "↓0.7 kg from last week"
                },
                "progress_since_start": {
                    "first_measurement": {
                        "weight_kg": 80.0,
                        "recorded_at": "2025-08-01T10:00:00Z"
                    },
                    "total_change_kg": -7.5,
                    "direction": "down",
                    "display_text": "↓7.5 kg total progress"
                },
                "typical_range": {
                    "min_kg": 71.0,
                    "max_kg": 75.0,
                    "avg_kg": 73.0,
                    "measurements_count": 12
                }
            },
            "validation": {
                "is_likely_typo": false,
                "is_physiologically_impossible": false,
                "is_unusual": false,
                "suggested_value": null  // If typo detected, suggest correct value
            },
            "editable_fields": ["weight_kg", "body_fat_percentage", "recorded_at", "notes"],
            "warnings": []
        }
        """
        logger.info("[MeasurementEnrichment] ⚖️ Enriching measurement preview with trend analysis")

        weight_kg = structured_data.get("weight_kg")
        body_fat_pct = structured_data.get("body_fat_percentage")
        recorded_at = structured_data.get("recorded_at", datetime.utcnow().isoformat())

        if not weight_kg:
            logger.warning("[MeasurementEnrichment] ⚠️ No weight in structured_data")
            return structured_data, ["No weight measurement detected"]

        logger.info(f"[MeasurementEnrichment] Processing: {weight_kg} kg (body fat: {body_fat_pct}%)")

        warnings = []
        enriched_data = dict(structured_data)  # Copy original data

        # STEP 1: Get user's measurement history
        history = await self._get_measurement_history(user_id, limit=30)

        if not history or len(history) == 0:
            logger.info("[MeasurementEnrichment] ℹ️ No measurement history - first measurement")
            enriched_data["trend_analysis"] = None
            enriched_data["validation"] = {
                "is_likely_typo": False,
                "is_physiologically_impossible": False,
                "is_unusual": False,
                "suggested_value": None
            }
            enriched_data["editable_fields"] = ["weight_kg", "body_fat_percentage", "recorded_at", "notes"]
            enriched_data["warnings"] = []
            return enriched_data, []

        # STEP 2: Calculate trend analysis
        trend_analysis = self._calculate_trend_analysis(
            current_weight=weight_kg,
            current_date=datetime.fromisoformat(recorded_at.replace('Z', '+00:00')),
            history=history
        )
        enriched_data["trend_analysis"] = trend_analysis

        # STEP 3: Validate measurement
        validation_result = self._validate_measurement(
            current_weight=weight_kg,
            current_body_fat=body_fat_pct,
            current_date=datetime.fromisoformat(recorded_at.replace('Z', '+00:00')),
            history=history
        )
        enriched_data["validation"] = validation_result

        # STEP 4: Generate warnings
        validation_warnings = self._generate_validation_warnings(
            weight_kg=weight_kg,
            body_fat_pct=body_fat_pct,
            validation=validation_result,
            trend=trend_analysis
        )
        warnings.extend(validation_warnings)

        # STEP 5: Mark editable fields
        enriched_data["editable_fields"] = ["weight_kg", "body_fat_percentage", "recorded_at", "notes"]
        enriched_data["warnings"] = warnings

        logger.info(
            f"[MeasurementEnrichment] ✅ Enrichment complete: "
            f"{len(warnings)} warnings, typo_detected={validation_result['is_likely_typo']}"
        )

        return enriched_data, warnings

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _get_measurement_history(
        self,
        user_id: str,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Fetch user's measurement history (last 30 measurements)."""
        try:
            result = self.supabase.table("body_metrics")\
                .select("weight_kg, body_fat_percentage, recorded_at, notes")\
                .eq("user_id", user_id)\
                .order("recorded_at", desc=True)\
                .limit(limit)\
                .execute()

            if not result.data:
                return []

            return result.data

        except Exception as e:
            logger.error(f"[MeasurementEnrichment] Failed to fetch measurement history: {e}")
            return []

    def _calculate_trend_analysis(
        self,
        current_weight: float,
        current_date: datetime,
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate trend from last measurement and progress since start."""

        if not history or len(history) == 0:
            return None

        # Last measurement
        last_measurement = history[0]
        last_weight = float(last_measurement["weight_kg"])
        last_date = datetime.fromisoformat(last_measurement["recorded_at"].replace('Z', '+00:00'))
        days_ago = (current_date - last_date).days

        # Change from last
        weight_change = current_weight - last_weight
        weight_direction = "down" if weight_change < -0.1 else ("up" if weight_change > 0.1 else "stable")

        # Format display text
        if weight_direction == "stable":
            display_text = "No change from last measurement"
        else:
            arrow = "↓" if weight_direction == "down" else "↑"
            time_text = self._format_time_ago(days_ago)
            display_text = f"{arrow}{abs(weight_change):.1f} kg from {time_text}"

        change_from_last = {
            "weight_kg": round(weight_change, 1),
            "weight_direction": weight_direction,
            "display_text": display_text
        }

        # Progress since start (first measurement)
        first_measurement = history[-1]
        first_weight = float(first_measurement["weight_kg"])
        first_date = datetime.fromisoformat(first_measurement["recorded_at"].replace('Z', '+00:00'))

        total_change = current_weight - first_weight
        progress_direction = "down" if total_change < -0.1 else ("up" if total_change > 0.1 else "stable")

        progress_since_start = {
            "first_measurement": {
                "weight_kg": first_weight,
                "recorded_at": first_measurement["recorded_at"]
            },
            "total_change_kg": round(total_change, 1),
            "direction": progress_direction,
            "display_text": f"{'↓' if progress_direction == 'down' else '↑' if progress_direction == 'up' else '='}{abs(total_change):.1f} kg total progress" if progress_direction != "stable" else "No change since first measurement"
        }

        # Typical range (last 30 days or 10 measurements)
        recent_measurements = [float(m["weight_kg"]) for m in history[:10]]
        typical_range = {
            "min_kg": round(min(recent_measurements), 1),
            "max_kg": round(max(recent_measurements), 1),
            "avg_kg": round(sum(recent_measurements) / len(recent_measurements), 1),
            "measurements_count": len(recent_measurements)
        }

        return {
            "last_measurement": {
                "weight_kg": last_weight,
                "recorded_at": last_measurement["recorded_at"],
                "days_ago": days_ago
            },
            "change_from_last": change_from_last,
            "progress_since_start": progress_since_start,
            "typical_range": typical_range
        }

    def _validate_measurement(
        self,
        current_weight: float,
        current_body_fat: Optional[float],
        current_date: datetime,
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate measurement for typos and physiologically impossible changes."""

        is_likely_typo = False
        is_physiologically_impossible = False
        is_unusual = False
        suggested_value = None

        # Check typical weight range
        if current_weight < TYPICAL_WEIGHT_RANGE_KG[0] or current_weight > TYPICAL_WEIGHT_RANGE_KG[1]:
            is_unusual = True

        if history and len(history) > 0:
            last_measurement = history[0]
            last_weight = float(last_measurement["weight_kg"])
            last_date = datetime.fromisoformat(last_measurement["recorded_at"].replace('Z', '+00:00'))
            days_elapsed = (current_date - last_date).days

            if days_elapsed > 0:
                weight_change = abs(current_weight - last_weight)
                change_per_day = weight_change / days_elapsed

                # Check for physiologically impossible changes
                if change_per_day > MAX_WEIGHT_CHANGE_PER_DAY_KG:
                    is_physiologically_impossible = True

                # Check for likely typos (missing digit)
                # Example: 150 → 50 (missing "1"), 180 → 80 (missing "1")
                if weight_change > 50:  # Massive change
                    # Check if adding a leading digit makes it closer
                    for digit in ['1', '2']:
                        potential_typo = float(f"{digit}{int(current_weight)}")
                        if abs(potential_typo - last_weight) < 10:  # Much more reasonable
                            is_likely_typo = True
                            suggested_value = potential_typo
                            break

                    # Check if removing a leading digit makes it closer
                    if current_weight > 100 and not is_likely_typo:
                        potential_typo = float(str(int(current_weight))[1:])
                        if abs(potential_typo - last_weight) < 10:
                            is_likely_typo = True
                            suggested_value = potential_typo

        # Validate body fat percentage if provided
        if current_body_fat is not None:
            if current_body_fat < TYPICAL_BODY_FAT_RANGE_PCT[0] or current_body_fat > TYPICAL_BODY_FAT_RANGE_PCT[1]:
                is_unusual = True

            if history and len(history) > 0:
                last_bf = history[0].get("body_fat_percentage")
                if last_bf:
                    last_bf = float(last_bf)
                    last_date = datetime.fromisoformat(history[0]["recorded_at"].replace('Z', '+00:00'))
                    days_elapsed = max(1, (current_date - last_date).days)

                    bf_change = abs(current_body_fat - last_bf)
                    if days_elapsed <= 7 and bf_change > MAX_BODY_FAT_CHANGE_PER_WEEK_PCT:
                        is_physiologically_impossible = True

        return {
            "is_likely_typo": is_likely_typo,
            "is_physiologically_impossible": is_physiologically_impossible,
            "is_unusual": is_unusual,
            "suggested_value": suggested_value
        }

    def _generate_validation_warnings(
        self,
        weight_kg: float,
        body_fat_pct: Optional[float],
        validation: Dict[str, Any],
        trend: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate human-readable warnings based on validation results."""
        warnings = []

        # Critical errors (likely typos or impossible changes)
        if validation["is_likely_typo"] and validation["suggested_value"]:
            warnings.append(
                f"⚠️ Did you mean {validation['suggested_value']:.1f} kg? "
                f"{weight_kg} kg seems like a typo."
            )

        if validation["is_physiologically_impossible"]:
            warnings.append(
                f"❌ This change is physiologically impossible "
                f"({trend['change_from_last']['display_text']}). "
                f"Please verify the weight is correct."
            )

        # Unusual values (might be correct, but worth verifying)
        if validation["is_unusual"] and not validation["is_likely_typo"]:
            if weight_kg < TYPICAL_WEIGHT_RANGE_KG[0]:
                warnings.append(
                    f"ℹ️ {weight_kg} kg is lower than typical. Please verify this is correct."
                )
            elif weight_kg > TYPICAL_WEIGHT_RANGE_KG[1]:
                warnings.append(
                    f"ℹ️ {weight_kg} kg is higher than typical. Please verify this is correct."
                )

        # Body fat warnings
        if body_fat_pct is not None:
            if body_fat_pct < TYPICAL_BODY_FAT_RANGE_PCT[0]:
                warnings.append(
                    f"ℹ️ {body_fat_pct}% body fat is very low. Elite athletes only. Verify measurement."
                )
            elif body_fat_pct > TYPICAL_BODY_FAT_RANGE_PCT[1]:
                warnings.append(
                    f"ℹ️ {body_fat_pct}% body fat is very high. Please verify measurement."
                )

        return warnings

    def _format_time_ago(self, days: int) -> str:
        """Format days ago as human-readable string."""
        if days == 0:
            return "today"
        elif days == 1:
            return "yesterday"
        elif days < 7:
            return f"{days} days ago"
        elif days < 14:
            return "last week"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} weeks ago"
        elif days < 60:
            return "last month"
        else:
            months = days // 30
            return f"{months} months ago"
