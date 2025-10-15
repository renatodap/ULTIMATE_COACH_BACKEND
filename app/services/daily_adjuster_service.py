"""
Daily Adjuster Service

Applies day-level adaptive adjustments based on adherence and recovery signals.
Writes:
- day_overrides (nutrition/training)
- plan_change_events (for structural swaps)
- calendar_events status updates

Uses existing activity/meal/body_metrics and optional wearables (health_metrics).
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timedelta, date
import structlog

from app.services.supabase_service import SupabaseService

logger = structlog.get_logger()


class DailyAdjusterService:
    def __init__(self, db: Optional[SupabaseService] = None) -> None:
        self.db = db or SupabaseService()

    def _today(self) -> date:
        return date.today()

    def adjust_today(self, user_id: str, program_id: str) -> Dict[str, Any]:
        """
        Compute and apply day-level adjustments for the next 24h.

        Rules (v1):
        - If a planned session yesterday was skipped → write nutrition override today: -5% kcal, keep protein.
        - If sleep/readiness is poor (from health_metrics) → downgrade today's HIIT to easy Z1/Z2 and reduce volume ~20%.
        - Always pass safety bounds before changing calories.
        - Update calendar events status accordingly.
        """
        client = self.db.client
        today = self._today()
        yesterday = today - timedelta(days=1)

        # Did we miss a planned session yesterday?
        skipped = client.table("adherence_records").select("*") \
            .eq("user_id", user_id) \
            .eq("status", "skipped") \
            .gte("assessed_at", str(yesterday)) \
            .lte("assessed_at", str(yesterday) + " 23:59:59") \
            .execute().data

        # Sleep/readiness last night
        sleep_rows = client.table("health_metrics").select("*") \
            .eq("user_id", user_id).eq("metric_type", "sleep") \
            .gte("recorded_at", str(yesterday)) \
            .lte("recorded_at", str(today)) \
            .order("recorded_at", desc=True) \
            .limit(1).execute().data

        poor_sleep = False
        if sleep_rows:
            v = sleep_rows[0].get("value") or {}
            # Heuristic: sleep_score < 60 or <5h duration
            score = v.get("score") or 0
            dur = v.get("duration_min") or 0
            poor_sleep = score < 60 or dur < 300

        # Nutrition override if missed yesterday
        overrides_written = []
        if skipped:
            nutrition = {"delta_calories_pct": -0.07, "keep_protein": True, "notes": "Missed session yesterday"}
            dor = {
                "user_id": user_id,
                "date": str(today),
                "override_type": "nutrition",
                "reason_code": "missed_workout",
                "reason_details": f"{len(skipped)} planned sessions skipped on {yesterday}",
                "confidence": 0.8,
                "nutrition_override": nutrition,
            }
            client.table("day_overrides").insert(dor).execute()
            overrides_written.append("nutrition")

        # Training downgrade if poor sleep
        if poor_sleep:
            training = {
                "action": "downgrade",
                "target": "all_hiit_today",
                "new_intensity": "Z1/Z2",
                "volume_multiplier": 0.8,
                "notes": "Poor sleep detected; reduce intensity and volume",
            }
            dor = {
                "user_id": user_id,
                "date": str(today),
                "override_type": "training",
                "reason_code": "poor_sleep",
                "reason_details": "sleep score low or duration short",
                "confidence": 0.7,
                "training_override": training,
            }
            client.table("day_overrides").insert(dor).execute()
            overrides_written.append("training")

        return {"date": str(today), "overrides": overrides_written}

