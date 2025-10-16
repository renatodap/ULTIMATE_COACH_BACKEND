"""
Daily Adjustment Service

Implements intelligent daily adjustments based on user context and adherence.
Creates day_overrides that modify planned calories/volume based on:
- Missed workouts (reduce calories on rest days)
- Poor sleep (reduce volume, maintain calories)
- High stress (reduce volume, increase recovery)
- Injury/soreness (modify exercises, reduce volume)
- Over/under adherence (adjust targets)

This service is context-aware and applies safety gates to prevent extreme adjustments.
"""

from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
from uuid import UUID
import structlog

from app.services.supabase_service import SupabaseService
from app.services.adjustment_approval_service import adjustment_approval_service

logger = structlog.get_logger()


class DailyAdjustmentService:
    """Creates intelligent daily adjustments based on user context"""

    def __init__(self, db: Optional[SupabaseService] = None):
        self.db = db or SupabaseService()

    async def analyze_and_adjust(
        self,
        user_id: str,
        target_date: date,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze user context and create day override if needed.

        Args:
            user_id: User UUID
            target_date: Date to adjust
            context: User context (sleep, stress, soreness, etc.)
                     If None, will be inferred from recent data

        Returns:
            day_override dict if adjustment made, None otherwise

        Flow:
        1. Gather context (adherence, sleep, stress, injuries)
        2. Identify adjustment triggers
        3. Calculate adjustments (calories, volume, exercise swaps)
        4. Apply safety gates
        5. Create day_override record
        """
        client = self.db.client

        logger.info(
            "analyzing_daily_adjustment",
            user_id=user_id,
            date=str(target_date),
        )

        # Step 1: Gather context
        if context is None:
            context = await self._gather_context(user_id, target_date)

        logger.info(
            "context_gathered",
            user_id=user_id,
            context_keys=list(context.keys()),
        )

        # Step 2: Identify triggers
        triggers = self._identify_triggers(context)

        if not triggers:
            logger.info("no_adjustment_triggers", user_id=user_id, date=str(target_date))
            return None

        logger.info(
            "adjustment_triggers_identified",
            user_id=user_id,
            triggers=[t["trigger_type"] for t in triggers],
        )

        # Step 3: Calculate adjustments
        nutrition_override = self._calculate_nutrition_adjustment(context, triggers)
        training_override = self._calculate_training_adjustment(context, triggers)

        # Step 4: Apply safety gates
        nutrition_override = self._apply_nutrition_safety_gates(
            nutrition_override, context
        )
        training_override = self._apply_training_safety_gates(
            training_override, context
        )

        # Determine override type
        has_nutrition = nutrition_override and any(
            nutrition_override.get(k) for k in ["calorie_adjustment", "macro_adjustments"]
        )
        has_training = training_override and any(
            training_override.get(k)
            for k in ["volume_multiplier", "exercise_swaps", "session_cancelled"]
        )

        if not has_nutrition and not has_training:
            logger.info("no_significant_adjustments", user_id=user_id)
            return None

        override_type = (
            "both" if (has_nutrition and has_training) else (
                "nutrition" if has_nutrition else "training"
            )
        )

        # Step 5: Determine approval workflow
        confidence = self._calculate_confidence(triggers, context)
        primary_trigger = triggers[0]["trigger_type"]

        # Check user preferences for primary trigger
        action = await adjustment_approval_service.should_request_approval(
            user_id=user_id,
            trigger_type=primary_trigger,
            adjustment_type=override_type,
        )

        logger.info(
            "approval_action_determined",
            user_id=user_id,
            trigger=primary_trigger,
            action=action,
            confidence=confidence,
        )

        # Determine initial status and grace period
        if action == "disable":
            logger.info("adjustment_disabled_by_user_preference", user_id=user_id, trigger=primary_trigger)
            return None
        elif action == "auto_apply":
            # Auto-apply: check confidence for grace period
            if confidence > 0.8:
                # High confidence: pending with grace period, then auto-apply
                status = "pending"
                prefs = await adjustment_approval_service.get_user_preferences(user_id)
                grace_period_expires_at = datetime.utcnow() + timedelta(
                    minutes=prefs.auto_apply_grace_period_minutes
                )
            else:
                # Low confidence: request approval even if preference is auto_apply
                status = "pending"
                grace_period_expires_at = None
                logger.info(
                    "low_confidence_override",
                    user_id=user_id,
                    confidence=confidence,
                    message="Requesting approval despite auto_apply preference due to low confidence",
                )
        else:  # action == "ask_me"
            status = "pending"
            grace_period_expires_at = None

        # Create day_override
        override_data = {
            "user_id": user_id,
            "date": target_date.isoformat(),
            "override_type": override_type,
            "reason_code": primary_trigger,
            "reason_details": self._format_reason_details(triggers),
            "confidence": confidence,
            "nutrition_override": nutrition_override if has_nutrition else None,
            "training_override": training_override if has_training else None,
            "status": status,
            "grace_period_expires_at": grace_period_expires_at.isoformat() if grace_period_expires_at else None,
        }

        result = client.table("day_overrides").insert(override_data).execute()

        if not result.data:
            logger.error("failed_to_create_day_override", user_id=user_id)
            return None

        override = result.data[0]

        logger.info(
            "day_override_created",
            override_id=override["id"],
            override_type=override_type,
            reason_code=override["reason_code"],
            status=status,
            grace_period_expires_at=grace_period_expires_at.isoformat() if grace_period_expires_at else None,
        )

        # Step 6: Create notification if pending
        if status == "pending":
            try:
                notification_id = await adjustment_approval_service.create_adjustment_notification(
                    user_id=user_id,
                    day_override_id=override["id"],
                    adjustment_summary=override,
                )
                override["notification_id"] = notification_id
                logger.info(
                    "adjustment_notification_created",
                    override_id=override["id"],
                    notification_id=notification_id,
                )
            except Exception as e:
                logger.error(
                    "failed_to_create_notification",
                    override_id=override["id"],
                    error=str(e),
                )

        return override

    async def _gather_context(
        self, user_id: str, target_date: date
    ) -> Dict[str, Any]:
        """
        Gather user context for decision making.

        Context sources:
        - Recent adherence (last 7 days)
        - Sleep quality (if tracked)
        - Stress level (if tracked)
        - Soreness/injury reports
        - Missed workouts
        - Body metrics trends
        """
        client = self.db.client
        context = {}

        # Adherence over last 7 days
        week_ago = target_date - timedelta(days=7)
        adherence_result = (
            client.table("adherence_records")
            .select("*")
            .eq("user_id", user_id)
            .gte("assessed_at", week_ago.isoformat())
            .lte("assessed_at", target_date.isoformat())
            .execute()
        )

        if adherence_result.data:
            training_adherence = [
                r for r in adherence_result.data if r.get("planned_entity_type") == "session"
            ]
            nutrition_adherence = [
                r for r in adherence_result.data if r.get("planned_entity_type") == "meal"
            ]

            context["recent_training_adherence"] = len(
                [r for r in training_adherence if r.get("status") in ["completed", "similar"]]
            ) / max(len(training_adherence), 1)

            context["recent_nutrition_adherence"] = (
                sum(r.get("similarity_score", 0) for r in nutrition_adherence)
                / max(len(nutrition_adherence), 1)
            )

            # Check for missed workouts yesterday
            yesterday = target_date - timedelta(days=1)
            missed_yesterday = [
                r
                for r in training_adherence
                if r.get("status") == "skipped"
                and r.get("assessed_at", "").startswith(yesterday.isoformat())
            ]
            context["missed_workout_yesterday"] = len(missed_yesterday) > 0

        # Check user_context_log for sleep, stress, soreness
        context_log_result = (
            client.table("user_context_log")
            .select("*")
            .eq("user_id", user_id)
            .eq("date", (target_date - timedelta(days=1)).isoformat())
            .execute()
        )

        if context_log_result.data:
            log_entry = context_log_result.data[0]
            context["sleep_hours"] = log_entry.get("sleep_hours")
            context["sleep_quality"] = log_entry.get("sleep_quality")
            context["stress_level"] = log_entry.get("stress_level")
            context["soreness_level"] = log_entry.get("soreness_level")
            context["injury_reported"] = log_entry.get("injury_notes") is not None

        # Get user's active program
        program_result = (
            client.table("programs")
            .select("id, macros, tdee")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if program_result.data:
            program = program_result.data[0]
            context["program_id"] = program["id"]
            context["target_calories"] = program.get("macros", {}).get("calories_kcal", 0)
            context["tdee"] = program.get("tdee", {}).get("tdee_kcal", 0)

        return context

    def _identify_triggers(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify triggers that warrant daily adjustments.

        Triggers:
        - Poor sleep (< 6 hours or quality < 5/10)
        - High stress (level > 7/10)
        - High soreness (level > 7/10)
        - Injury reported
        - Missed workout yesterday
        - Very low adherence (< 50% over last week)
        - Very high adherence (> 95% - reward day)
        """
        triggers = []

        # Sleep trigger
        sleep_hours = context.get("sleep_hours")
        sleep_quality = context.get("sleep_quality")

        if sleep_hours and sleep_hours < 6:
            triggers.append({
                "trigger_type": "poor_sleep",
                "severity": min(10, int((6 - sleep_hours) * 2)),
                "details": f"Only {sleep_hours} hours of sleep",
            })
        elif sleep_quality and sleep_quality < 5:
            triggers.append({
                "trigger_type": "poor_sleep_quality",
                "severity": int((5 - sleep_quality) * 2),
                "details": f"Sleep quality: {sleep_quality}/10",
            })

        # Stress trigger
        stress_level = context.get("stress_level")
        if stress_level and stress_level > 7:
            triggers.append({
                "trigger_type": "high_stress",
                "severity": stress_level,
                "details": f"Stress level: {stress_level}/10",
            })

        # Soreness/injury trigger
        soreness_level = context.get("soreness_level")
        if soreness_level and soreness_level > 7:
            triggers.append({
                "trigger_type": "high_soreness",
                "severity": soreness_level,
                "details": f"Soreness level: {soreness_level}/10",
            })

        if context.get("injury_reported"):
            triggers.append({
                "trigger_type": "injury",
                "severity": 9,
                "details": "Injury reported",
            })

        # Missed workout trigger
        if context.get("missed_workout_yesterday"):
            triggers.append({
                "trigger_type": "missed_workout",
                "severity": 6,
                "details": "Missed workout yesterday",
            })

        # Adherence triggers
        training_adherence = context.get("recent_training_adherence", 1.0)
        if training_adherence < 0.5:
            triggers.append({
                "trigger_type": "low_adherence",
                "severity": int((0.5 - training_adherence) * 20),
                "details": f"Training adherence: {training_adherence*100:.0f}%",
            })
        elif training_adherence > 0.95:
            triggers.append({
                "trigger_type": "high_adherence",
                "severity": 2,  # Low severity, this is a reward
                "details": f"Excellent adherence: {training_adherence*100:.0f}%",
            })

        return triggers

    def _calculate_nutrition_adjustment(
        self, context: Dict[str, Any], triggers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate nutrition adjustments based on triggers.

        Adjustments:
        - Missed workout: -200 to -400 kcal (prevent surplus on unplanned rest day)
        - Poor sleep: No change (maintain calories for recovery)
        - High stress: +100 kcal (support recovery)
        - High adherence: +100-200 kcal (reward, refeed)
        """
        adjustment = {
            "calorie_adjustment": 0,
            "macro_adjustments": {},
            "reasoning": [],
        }

        target_calories = context.get("target_calories", 2000)

        for trigger in triggers:
            trigger_type = trigger["trigger_type"]
            severity = trigger["severity"]

            if trigger_type == "missed_workout":
                # Reduce calories to prevent surplus
                cal_reduction = min(400, int(severity * 40))
                adjustment["calorie_adjustment"] -= cal_reduction
                adjustment["reasoning"].append(
                    f"Reduced calories by {cal_reduction} due to missed workout"
                )

            elif trigger_type in ["poor_sleep", "poor_sleep_quality"]:
                # Maintain calories for recovery
                adjustment["reasoning"].append(
                    "Maintaining calories despite poor sleep to support recovery"
                )

            elif trigger_type == "high_stress":
                # Slight increase for recovery
                cal_increase = min(150, int(severity * 15))
                adjustment["calorie_adjustment"] += cal_increase
                adjustment["reasoning"].append(
                    f"Increased calories by {cal_increase} to support stress recovery"
                )

            elif trigger_type == "high_adherence":
                # Reward with refeed
                cal_increase = 200
                adjustment["calorie_adjustment"] += cal_increase
                adjustment["macro_adjustments"]["carbs_g"] = 50  # Extra carbs
                adjustment["reasoning"].append(
                    "Reward day: +200 kcal (mostly carbs) for excellent adherence"
                )

            elif trigger_type == "low_adherence":
                # Small reduction to compensate for lower activity
                cal_reduction = 100
                adjustment["calorie_adjustment"] -= cal_reduction
                adjustment["reasoning"].append(
                    "Slight calorie reduction due to low recent activity"
                )

        return adjustment

    def _calculate_training_adjustment(
        self, context: Dict[str, Any], triggers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate training adjustments based on triggers.

        Adjustments:
        - Poor sleep: -20% volume (reduce sets/reps)
        - High stress: -15% volume + focus on technique
        - High soreness: -25% volume + lower intensity
        - Injury: Cancel or modify session
        - Missed workout: No adjustment (catch up if possible)
        """
        adjustment = {
            "volume_multiplier": 1.0,
            "intensity_adjustment": 0,
            "exercise_swaps": [],
            "session_cancelled": False,
            "session_notes": [],
            "reasoning": [],
        }

        for trigger in triggers:
            trigger_type = trigger["trigger_type"]
            severity = trigger["severity"]

            if trigger_type in ["poor_sleep", "poor_sleep_quality"]:
                # Reduce volume
                volume_reduction = min(0.3, severity / 50)
                adjustment["volume_multiplier"] *= (1 - volume_reduction)
                adjustment["session_notes"].append(
                    f"Reduce volume by {int(volume_reduction*100)}% due to poor sleep"
                )
                adjustment["reasoning"].append(
                    "Volume reduced to prevent overtraining with poor recovery"
                )

            elif trigger_type == "high_stress":
                # Reduce volume slightly
                volume_reduction = 0.15
                adjustment["volume_multiplier"] *= 0.85
                adjustment["session_notes"].append(
                    "Reduce volume by 15% and focus on form due to high stress"
                )
                adjustment["reasoning"].append(
                    "Training adjusted for high stress - focus on quality over quantity"
                )

            elif trigger_type == "high_soreness":
                # Reduce volume and intensity
                volume_reduction = 0.25
                adjustment["volume_multiplier"] *= 0.75
                adjustment["intensity_adjustment"] = -1  # Reduce by 1 RIR
                adjustment["session_notes"].append(
                    "Reduce volume by 25% and leave 1 more rep in reserve"
                )
                adjustment["reasoning"].append(
                    "Deload day due to high soreness - allow recovery"
                )

            elif trigger_type == "injury":
                # Cancel or heavily modify
                adjustment["session_cancelled"] = True
                adjustment["session_notes"].append(
                    "Session cancelled due to injury - rest and recovery"
                )
                adjustment["reasoning"].append(
                    "Safety first: session cancelled to allow injury recovery"
                )

        # Cap volume multiplier at reasonable bounds
        adjustment["volume_multiplier"] = max(0.5, min(1.0, adjustment["volume_multiplier"]))

        return adjustment

    def _apply_nutrition_safety_gates(
        self, adjustment: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply safety gates to prevent extreme nutrition adjustments.

        Gates:
        - Max calorie adjustment: ±500 kcal
        - Don't go below BMR
        - Don't exceed TDEE + 500
        """
        if not adjustment:
            return adjustment

        cal_adj = adjustment.get("calorie_adjustment", 0)
        target_calories = context.get("target_calories", 2000)
        tdee = context.get("tdee", 2000)

        # Gate 1: Max ±500 kcal adjustment
        if abs(cal_adj) > 500:
            adjustment["calorie_adjustment"] = 500 if cal_adj > 0 else -500
            adjustment["reasoning"].append(
                f"Adjustment capped at ±500 kcal for safety (was {cal_adj:+d})"
            )

        # Gate 2: Don't go below 1200 kcal (minimum safe intake)
        new_calories = target_calories + adjustment["calorie_adjustment"]
        if new_calories < 1200:
            adjustment["calorie_adjustment"] = 1200 - target_calories
            adjustment["reasoning"].append(
                "Adjustment limited to maintain minimum 1200 kcal"
            )

        # Gate 3: Don't exceed TDEE + 500
        if new_calories > tdee + 500:
            adjustment["calorie_adjustment"] = (tdee + 500) - target_calories
            adjustment["reasoning"].append(
                f"Adjustment capped to avoid excessive surplus (TDEE + 500)"
            )

        return adjustment

    def _apply_training_safety_gates(
        self, adjustment: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply safety gates to prevent extreme training adjustments.

        Gates:
        - Min volume multiplier: 0.5 (don't reduce below 50%)
        - Max volume multiplier: 1.0 (no increases via this system)
        """
        if not adjustment:
            return adjustment

        # Gate: Volume multiplier bounds
        volume_mult = adjustment.get("volume_multiplier", 1.0)
        if volume_mult < 0.5:
            adjustment["volume_multiplier"] = 0.5
            adjustment["reasoning"].append(
                "Volume reduction capped at 50% for safety"
            )
        elif volume_mult > 1.0:
            adjustment["volume_multiplier"] = 1.0
            adjustment["reasoning"].append(
                "Volume increases not permitted via daily adjustments"
            )

        return adjustment

    def _format_reason_details(self, triggers: List[Dict[str, Any]]) -> str:
        """Format trigger details into human-readable string"""
        if not triggers:
            return ""

        details = []
        for trigger in triggers:
            details.append(f"{trigger['trigger_type']}: {trigger.get('details', '')}")

        return "; ".join(details)

    def _calculate_confidence(
        self, triggers: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for the adjustment.

        Factors:
        - Number of triggers (more = higher confidence)
        - Severity of triggers (higher = higher confidence)
        - Data quality (complete context = higher confidence)
        """
        if not triggers:
            return 0.0

        # Base confidence from trigger count
        trigger_confidence = min(0.5, len(triggers) * 0.15)

        # Add severity component
        avg_severity = sum(t["severity"] for t in triggers) / len(triggers)
        severity_confidence = min(0.3, avg_severity / 30)

        # Add data quality component
        data_quality_score = sum([
            0.05 if context.get("sleep_hours") else 0,
            0.05 if context.get("sleep_quality") else 0,
            0.05 if context.get("stress_level") else 0,
            0.05 if context.get("soreness_level") else 0,
            0.1 if context.get("recent_training_adherence") else 0,
        ])

        confidence = trigger_confidence + severity_confidence + data_quality_score

        return min(1.0, confidence)

    async def get_adjustment_for_date(
        self, user_id: str, target_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing day override for a specific date.

        Args:
            user_id: User UUID
            target_date: Date to check

        Returns:
            day_override dict if exists, None otherwise
        """
        client = self.db.client

        result = (
            client.table("day_overrides")
            .select("*")
            .eq("user_id", user_id)
            .eq("date", target_date.isoformat())
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if result.data:
            return result.data[0]

        return None

    async def apply_override_to_plan(
        self, user_id: str, target_date: date, override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply day override to today's plan (for display to user).

        Args:
            user_id: User UUID
            target_date: Date of the plan
            override: day_override record

        Returns:
            Adjusted plan with override applied
        """
        client = self.db.client

        # Get today's calendar events
        events_result = (
            client.table("calendar_events")
            .select("*")
            .eq("user_id", user_id)
            .eq("date", target_date.isoformat())
            .execute()
        )

        events = events_result.data if events_result.data else []

        # Apply overrides
        nutrition_override = override.get("nutrition_override", {})
        training_override = override.get("training_override", {})

        # Adjust meal events
        for event in events:
            if event["event_type"] == "meal" and nutrition_override:
                details = event.get("details", {})
                cal_adj = nutrition_override.get("calorie_adjustment", 0)

                # Adjust calories proportionally
                if cal_adj != 0 and details.get("calories"):
                    original_cal = details["calories"]
                    # Distribute adjustment across meals proportionally
                    num_meals = sum(1 for e in events if e["event_type"] == "meal")
                    meal_adjustment = cal_adj / max(num_meals, 1)
                    details["calories_adjusted"] = int(original_cal + meal_adjustment)
                    details["adjustment_reason"] = nutrition_override.get("reasoning", [])

                event["details"] = details

            # Adjust training events
            elif event["event_type"] == "training" and training_override:
                details = event.get("details", {})

                if training_override.get("session_cancelled"):
                    event["status"] = "cancelled"
                    details["cancellation_reason"] = training_override.get("reasoning", [])
                else:
                    volume_mult = training_override.get("volume_multiplier", 1.0)
                    if volume_mult != 1.0:
                        details["volume_multiplier"] = volume_mult
                        details["adjustment_notes"] = training_override.get("session_notes", [])

                event["details"] = details

        return {
            "date": target_date.isoformat(),
            "events": events,
            "override": override,
            "has_adjustments": True,
        }


# Global singleton instance
daily_adjustment_service = DailyAdjustmentService()
