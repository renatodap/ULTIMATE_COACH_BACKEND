"""
Bi-weekly Reassessment Service

This service implements the 14-day reassessment cycle for adaptive program adjustments.
It aggregates 14 days of data, runs PID controllers, and generates new program versions
when significant adjustments are needed.

Key Components:
1. Reassessment Trigger - Automated 14-day intervals
2. Data Aggregation - Collect adherence, body metrics, context data
3. PID Controllers - CaloriePIDController, VolumePIDController
4. Plan Generation - Create new program versions with change tracking

Flow:
1. Check if reassessment is due (14 days since last)
2. Aggregate 14 days of data
3. Calculate progress vs goals
4. Run PID controllers to determine adjustments
5. Generate new program if adjustments needed
6. Create plan_change_events for audit trail
"""

import structlog
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID

from app.services.supabase_service import SupabaseService

logger = structlog.get_logger()


class CaloriePIDController:
    """
    PID Controller for calorie adjustments based on weight progress.

    PID Control:
    - P (Proportional): Adjust based on current error (weight delta vs goal)
    - I (Integral): Adjust based on accumulated error over time
    - D (Derivative): Adjust based on rate of change

    Goal: Minimize error between actual weight change and target weight change.
    """

    def __init__(
        self,
        kp: float = 100.0,  # Proportional gain (kcal per kg error)
        ki: float = 20.0,   # Integral gain (kcal per kg*day accumulated error)
        kd: float = 50.0,   # Derivative gain (kcal per kg/day rate change)
    ):
        """
        Initialize PID controller with tuning parameters.

        Args:
            kp: Proportional gain - how aggressively to respond to current error
            ki: Integral gain - how much to account for accumulated error
            kd: Derivative gain - how much to respond to rate of change
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.integral_error = 0.0
        self.previous_error = 0.0

        logger.info(
            "calorie_pid_initialized",
            kp=kp,
            ki=ki,
            kd=kd
        )

    def calculate_adjustment(
        self,
        target_weight_change_kg: float,  # Goal: e.g., -0.5 kg/week
        actual_weight_change_kg: float,  # Actual: e.g., -0.3 kg/week
        time_period_days: int = 14,      # Reassessment period
    ) -> Dict[str, Any]:
        """
        Calculate calorie adjustment using PID control.

        Args:
            target_weight_change_kg: Expected weight change (negative for loss)
            actual_weight_change_kg: Actual weight change observed
            time_period_days: Number of days in assessment period

        Returns:
            {
                "calorie_adjustment": int,  # kcal to add/subtract
                "error_kg": float,          # Current error
                "p_term": float,            # Proportional contribution
                "i_term": float,            # Integral contribution
                "d_term": float,            # Derivative contribution
                "confidence": float         # 0-1
            }
        """
        # Calculate error (actual - target)
        # If target = -0.5 kg and actual = -0.3 kg, error = 0.2 kg (losing too slowly)
        error_kg = actual_weight_change_kg - target_weight_change_kg

        # Proportional term: immediate response to current error
        p_term = self.kp * error_kg

        # Integral term: accumulated error over time
        self.integral_error += error_kg * time_period_days
        i_term = self.ki * self.integral_error

        # Derivative term: rate of change of error
        d_term = self.kd * (error_kg - self.previous_error)
        self.previous_error = error_kg

        # Total adjustment (negative = reduce calories, positive = increase)
        # If losing too slowly (error > 0), adjustment is positive → INCREASE deficit (reduce calories)
        # If losing too fast (error < 0), adjustment is negative → DECREASE deficit (increase calories)
        total_adjustment = -(p_term + i_term + d_term)

        # Confidence based on consistency of weight data
        confidence = min(1.0, time_period_days / 14.0)

        logger.info(
            "calorie_pid_calculation",
            target_change=target_weight_change_kg,
            actual_change=actual_weight_change_kg,
            error_kg=error_kg,
            p_term=p_term,
            i_term=i_term,
            d_term=d_term,
            total_adjustment=total_adjustment,
            confidence=confidence
        )

        return {
            "calorie_adjustment": int(round(total_adjustment)),
            "error_kg": error_kg,
            "p_term": p_term,
            "i_term": i_term,
            "d_term": d_term,
            "confidence": confidence,
        }


class VolumePIDController:
    """
    PID Controller for training volume adjustments based on adherence and recovery.

    Goal: Optimize training volume to maximize adherence while avoiding overtraining.

    Inputs:
    - Adherence rate (% of sessions completed)
    - Average soreness level
    - Average stress level

    Output: Volume multiplier (0.7-1.3x)
    """

    def __init__(
        self,
        kp: float = 0.5,   # Proportional gain
        ki: float = 0.1,   # Integral gain
        kd: float = 0.2,   # Derivative gain
    ):
        """Initialize volume PID controller."""
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.integral_error = 0.0
        self.previous_error = 0.0

        logger.info(
            "volume_pid_initialized",
            kp=kp,
            ki=ki,
            kd=kd
        )

    def calculate_adjustment(
        self,
        adherence_rate: float,        # 0-1 (e.g., 0.85 = 85%)
        avg_soreness: float = 5.0,    # 1-10
        avg_stress: float = 5.0,      # 1-10
        time_period_days: int = 14,
    ) -> Dict[str, Any]:
        """
        Calculate training volume adjustment.

        Logic:
        - High adherence (>90%) + low soreness → increase volume
        - Low adherence (<70%) + high soreness → decrease volume
        - Moderate adherence → minimal change

        Args:
            adherence_rate: % of sessions completed (0-1)
            avg_soreness: Average soreness level (1-10)
            avg_stress: Average stress level (1-10)
            time_period_days: Assessment period

        Returns:
            {
                "volume_multiplier": float,  # 0.7-1.3x
                "adherence_factor": float,
                "recovery_factor": float,
                "confidence": float
            }
        """
        # Target adherence: 85%
        target_adherence = 0.85
        error = adherence_rate - target_adherence

        # Proportional term
        p_term = self.kp * error

        # Integral term
        self.integral_error += error * time_period_days
        i_term = self.ki * self.integral_error

        # Derivative term
        d_term = self.kd * (error - self.previous_error)
        self.previous_error = error

        # Base adjustment from PID
        base_adjustment = p_term + i_term + d_term

        # Recovery factor (soreness + stress)
        # High soreness/stress → reduce volume
        recovery_score = (10 - avg_soreness + 10 - avg_stress) / 20  # 0-1
        recovery_factor = (recovery_score - 0.5) * 0.2  # -0.1 to +0.1

        # Total volume multiplier
        volume_multiplier = 1.0 + base_adjustment + recovery_factor

        # Clamp to safe range
        volume_multiplier = max(0.7, min(1.3, volume_multiplier))

        # Confidence
        confidence = min(1.0, time_period_days / 14.0)

        logger.info(
            "volume_pid_calculation",
            adherence_rate=adherence_rate,
            avg_soreness=avg_soreness,
            avg_stress=avg_stress,
            error=error,
            p_term=p_term,
            i_term=i_term,
            d_term=d_term,
            recovery_factor=recovery_factor,
            volume_multiplier=volume_multiplier,
            confidence=confidence
        )

        return {
            "volume_multiplier": volume_multiplier,
            "adherence_factor": base_adjustment,
            "recovery_factor": recovery_factor,
            "confidence": confidence,
        }


class ReassessmentService:
    """
    Bi-weekly reassessment service for adaptive program adjustments.

    Triggers every 14 days to:
    1. Aggregate user data (adherence, weight, context)
    2. Analyze progress vs goals
    3. Run PID controllers for adjustments
    4. Generate new program version if needed
    """

    def __init__(self):
        self.db = SupabaseService()
        self.calorie_pid = CaloriePIDController()
        self.volume_pid = VolumePIDController()

    async def check_reassessment_due(
        self,
        user_id: str,
    ) -> Tuple[bool, Optional[date]]:
        """
        Check if user is due for reassessment.

        Args:
            user_id: User UUID

        Returns:
            (is_due, next_reassessment_date)
        """
        try:
            # Get current active program
            program = (
                self.db.client.table("programs")
                .select("*")
                .eq("user_id", user_id)
                .is_("valid_until", "null")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if not program.data:
                logger.warning("no_active_program", user_id=user_id)
                return False, None

            program_data = program.data[0]
            next_reassessment = program_data.get("next_reassessment_date")

            if not next_reassessment:
                # Calculate from program start date
                start_date = date.fromisoformat(program_data["program_start_date"])
                next_reassessment = start_date + timedelta(days=14)
            else:
                next_reassessment = date.fromisoformat(next_reassessment)

            is_due = date.today() >= next_reassessment

            logger.info(
                "reassessment_check",
                user_id=user_id,
                next_reassessment=str(next_reassessment),
                is_due=is_due
            )

            return is_due, next_reassessment

        except Exception as e:
            logger.error("reassessment_check_failed", user_id=user_id, error=str(e))
            raise

    async def aggregate_data(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        Aggregate 14 days of user data for reassessment.

        Collects:
        - Adherence records (sessions and meals)
        - Body metrics (weight changes)
        - User context (sleep, stress, soreness)
        - Day overrides (daily adjustments made)

        Args:
            user_id: User UUID
            start_date: Start of reassessment period
            end_date: End of reassessment period

        Returns:
            {
                "adherence": {...},
                "body_metrics": {...},
                "context": {...},
                "overrides": {...}
            }
        """
        logger.info(
            "aggregating_data",
            user_id=user_id,
            start_date=str(start_date),
            end_date=str(end_date)
        )

        try:
            # 1. Adherence data
            adherence = await self._aggregate_adherence(user_id, start_date, end_date)

            # 2. Body metrics (weight)
            body_metrics = await self._aggregate_body_metrics(user_id, start_date, end_date)

            # 3. User context (sleep, stress, soreness)
            context = await self._aggregate_context(user_id, start_date, end_date)

            # 4. Day overrides
            overrides = await self._aggregate_overrides(user_id, start_date, end_date)

            return {
                "adherence": adherence,
                "body_metrics": body_metrics,
                "context": context,
                "overrides": overrides,
                "period_days": (end_date - start_date).days,
            }

        except Exception as e:
            logger.error("data_aggregation_failed", user_id=user_id, error=str(e))
            raise

    async def _aggregate_adherence(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Aggregate adherence records for period."""
        records = (
            self.db.client.table("adherence_records")
            .select("*")
            .eq("user_id", user_id)
            .gte("assessed_at", start_date.isoformat())
            .lte("assessed_at", end_date.isoformat())
            .execute()
        )

        if not records.data:
            return {
                "training_adherence_percent": 0.0,
                "nutrition_adherence_percent": 0.0,
                "sessions_completed": 0,
                "sessions_scheduled": 0,
                "meals_completed": 0,
                "meals_scheduled": 0,
            }

        # Separate by type
        training = [r for r in records.data if r["planned_entity_type"] == "session"]
        nutrition = [r for r in records.data if r["planned_entity_type"] == "meal"]

        # Training adherence
        training_completed = len([r for r in training if r["status"] in ["completed", "similar"]])
        training_scheduled = len(training)
        training_adherence = (
            training_completed / training_scheduled if training_scheduled > 0 else 0.0
        )

        # Nutrition adherence
        nutrition_completed = len([r for r in nutrition if r["status"] in ["completed", "similar"]])
        nutrition_scheduled = len(nutrition)
        nutrition_adherence = (
            nutrition_completed / nutrition_scheduled if nutrition_scheduled > 0 else 0.0
        )

        return {
            "training_adherence_percent": training_adherence * 100,
            "nutrition_adherence_percent": nutrition_adherence * 100,
            "sessions_completed": training_completed,
            "sessions_scheduled": training_scheduled,
            "meals_completed": nutrition_completed,
            "meals_scheduled": nutrition_scheduled,
        }

    async def _aggregate_body_metrics(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Aggregate body metrics (weight changes)."""
        metrics = (
            self.db.client.table("body_metrics")
            .select("*")
            .eq("user_id", user_id)
            .gte("recorded_at", start_date.isoformat())
            .lte("recorded_at", end_date.isoformat())
            .order("recorded_at", desc=False)
            .execute()
        )

        if not metrics.data or len(metrics.data) < 2:
            return {
                "weight_change_kg": 0.0,
                "weight_change_percent": 0.0,
                "measurements_count": len(metrics.data) if metrics.data else 0,
                "has_sufficient_data": False,
            }

        # First and last weight
        first_weight = float(metrics.data[0]["weight_kg"])
        last_weight = float(metrics.data[-1]["weight_kg"])

        weight_change_kg = last_weight - first_weight
        weight_change_percent = (weight_change_kg / first_weight) * 100

        return {
            "weight_change_kg": weight_change_kg,
            "weight_change_percent": weight_change_percent,
            "start_weight_kg": first_weight,
            "end_weight_kg": last_weight,
            "measurements_count": len(metrics.data),
            "has_sufficient_data": True,
        }

    async def _aggregate_context(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Aggregate user context (sleep, stress, soreness)."""
        context = (
            self.db.client.table("user_context_log")
            .select("*")
            .eq("user_id", user_id)
            .gte("date", start_date.isoformat())
            .lte("date", end_date.isoformat())
            .execute()
        )

        if not context.data:
            return {
                "avg_sleep_hours": None,
                "avg_sleep_quality": None,
                "avg_stress_level": None,
                "avg_soreness_level": None,
                "avg_energy_level": None,
                "data_points": 0,
            }

        # Calculate averages
        sleep_hours = [r["sleep_hours"] for r in context.data if r.get("sleep_hours")]
        sleep_quality = [r["sleep_quality"] for r in context.data if r.get("sleep_quality")]
        stress = [r["stress_level"] for r in context.data if r.get("stress_level")]
        soreness = [r["soreness_level"] for r in context.data if r.get("soreness_level")]
        energy = [r["energy_level"] for r in context.data if r.get("energy_level")]

        return {
            "avg_sleep_hours": sum(sleep_hours) / len(sleep_hours) if sleep_hours else None,
            "avg_sleep_quality": sum(sleep_quality) / len(sleep_quality) if sleep_quality else None,
            "avg_stress_level": sum(stress) / len(stress) if stress else None,
            "avg_soreness_level": sum(soreness) / len(soreness) if soreness else None,
            "avg_energy_level": sum(energy) / len(energy) if energy else None,
            "data_points": len(context.data),
        }

    async def _aggregate_overrides(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Aggregate day overrides made during period."""
        overrides = (
            self.db.client.table("day_overrides")
            .select("*")
            .eq("user_id", user_id)
            .gte("date", start_date.isoformat())
            .lte("date", end_date.isoformat())
            .execute()
        )

        if not overrides.data:
            return {
                "total_overrides": 0,
                "nutrition_overrides": 0,
                "training_overrides": 0,
                "most_common_reason": None,
            }

        # Count by type
        nutrition = len([o for o in overrides.data if o["override_type"] in ["nutrition", "both"]])
        training = len([o for o in overrides.data if o["override_type"] in ["training", "both"]])

        # Most common reason
        reasons = [o.get("reason_code") for o in overrides.data if o.get("reason_code")]
        most_common = max(set(reasons), key=reasons.count) if reasons else None

        return {
            "total_overrides": len(overrides.data),
            "nutrition_overrides": nutrition,
            "training_overrides": training,
            "most_common_reason": most_common,
        }

    async def run_reassessment(
        self,
        user_id: str,
        force: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Run complete reassessment for user.

        Flow:
        1. Check if reassessment is due
        2. Aggregate 14 days of data
        3. Run PID controllers
        4. Determine if new program is needed
        5. Generate plan_change_events
        6. Update next reassessment date

        Args:
            user_id: User UUID
            force: Force reassessment even if not due

        Returns:
            Reassessment result with adjustments, or None if not needed
        """
        logger.info("starting_reassessment", user_id=user_id, force=force)

        try:
            # 1. Check if due
            is_due, next_date = await self.check_reassessment_due(user_id)

            if not is_due and not force:
                logger.info(
                    "reassessment_not_due",
                    user_id=user_id,
                    next_date=str(next_date) if next_date else None
                )
                return None

            # 2. Get current program
            program = (
                self.db.client.table("programs")
                .select("*")
                .eq("user_id", user_id)
                .is_("valid_until", "null")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if not program.data:
                raise ValueError(f"No active program found for user {user_id}")

            program_data = program.data[0]

            # 3. Aggregate data
            end_date = date.today()
            start_date = end_date - timedelta(days=14)
            aggregated = await self.aggregate_data(user_id, start_date, end_date)

            # 4. Run PID controllers
            adjustments = await self._calculate_adjustments(
                program_data,
                aggregated
            )

            # 5. Determine if new program needed
            needs_new_program = self._should_generate_new_program(adjustments)

            # 6. Update next reassessment date
            new_reassessment_date = date.today() + timedelta(days=14)
            self.db.client.table("programs").update({
                "next_reassessment_date": new_reassessment_date.isoformat()
            }).eq("id", program_data["id"]).execute()

            result = {
                "user_id": user_id,
                "program_id": program_data["id"],
                "reassessment_date": date.today().isoformat(),
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "aggregated_data": aggregated,
                "adjustments": adjustments,
                "needs_new_program": needs_new_program,
                "next_reassessment_date": new_reassessment_date.isoformat(),
            }

            logger.info(
                "reassessment_complete",
                user_id=user_id,
                needs_new_program=needs_new_program,
                calorie_adjustment=adjustments["calorie"]["calorie_adjustment"],
                volume_multiplier=adjustments["volume"]["volume_multiplier"]
            )

            return result

        except Exception as e:
            logger.error("reassessment_failed", user_id=user_id, error=str(e), exc_info=True)
            raise

    async def _calculate_adjustments(
        self,
        program_data: Dict[str, Any],
        aggregated: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate calorie and volume adjustments using PID controllers.

        Args:
            program_data: Current program data
            aggregated: Aggregated 14-day data

        Returns:
            {
                "calorie": {...},  # CaloriePIDController output
                "volume": {...}    # VolumePIDController output
            }
        """
        # Extract target and actual weight changes
        macros = program_data.get("macros", {})
        target_calories = macros.get("calories", 2000)

        # Estimate target weight change from deficit
        # 7700 kcal deficit = 1 kg fat loss
        # 500 kcal daily deficit = 3500 kcal weekly = 0.45 kg/week
        profile_result = (
            self.db.client.table("profiles")
            .select("estimated_tdee")
            .eq("id", program_data["user_id"])
            .single()
            .execute()
        )

        tdee = profile_result.data.get("estimated_tdee", 2500) if profile_result.data else 2500
        daily_deficit = tdee - target_calories
        target_weekly_change_kg = (daily_deficit * 7) / 7700  # Negative for loss
        target_biweekly_change_kg = target_weekly_change_kg * 2

        # Actual weight change
        actual_weight_change_kg = aggregated["body_metrics"].get("weight_change_kg", 0.0)

        # Run calorie PID
        calorie_adjustment = self.calorie_pid.calculate_adjustment(
            target_weight_change_kg=target_biweekly_change_kg,
            actual_weight_change_kg=actual_weight_change_kg,
            time_period_days=aggregated["period_days"],
        )

        # Run volume PID
        adherence_rate = aggregated["adherence"]["training_adherence_percent"] / 100.0
        avg_soreness = aggregated["context"].get("avg_soreness_level", 5.0) or 5.0
        avg_stress = aggregated["context"].get("avg_stress_level", 5.0) or 5.0

        volume_adjustment = self.volume_pid.calculate_adjustment(
            adherence_rate=adherence_rate,
            avg_soreness=avg_soreness,
            avg_stress=avg_stress,
            time_period_days=aggregated["period_days"],
        )

        return {
            "calorie": calorie_adjustment,
            "volume": volume_adjustment,
            "target_weight_change_kg": target_biweekly_change_kg,
            "actual_weight_change_kg": actual_weight_change_kg,
        }

    def _should_generate_new_program(
        self,
        adjustments: Dict[str, Any],
    ) -> bool:
        """
        Determine if adjustments warrant a new program version.

        Criteria:
        - Calorie adjustment > 300 kcal
        - Volume multiplier outside 0.9-1.1 range
        - Low confidence in current program

        Args:
            adjustments: PID controller outputs

        Returns:
            True if new program should be generated
        """
        calorie_adj = abs(adjustments["calorie"]["calorie_adjustment"])
        volume_mult = adjustments["volume"]["volume_multiplier"]

        # Significant calorie change
        if calorie_adj > 300:
            logger.info("new_program_needed_calorie", adjustment=calorie_adj)
            return True

        # Significant volume change
        if volume_mult < 0.9 or volume_mult > 1.1:
            logger.info("new_program_needed_volume", multiplier=volume_mult)
            return True

        return False

    async def create_plan_change_events(
        self,
        user_id: str,
        program_id: str,
        adjustments: Dict[str, Any],
        effective_date: date,
    ) -> List[str]:
        """
        Create plan_change_events for audit trail of reassessment adjustments.

        Args:
            user_id: User UUID
            program_id: Program UUID
            adjustments: PID controller outputs
            effective_date: When changes take effect

        Returns:
            List of created event IDs
        """
        logger.info(
            "creating_plan_change_events",
            user_id=user_id,
            program_id=program_id,
            effective_date=str(effective_date)
        )

        events = []

        # Create nutrition change event
        calorie_adj = adjustments["calorie"]["calorie_adjustment"]
        if abs(calorie_adj) > 50:  # Only record significant changes
            nutrition_event = {
                "program_id": program_id,
                "user_id": user_id,
                "change_type": "edit",
                "planned_entity_type": "meal",
                "planned_entity_id": program_id,  # Program-level change
                "effective_date": effective_date.isoformat(),
                "reason_code": "biweekly_reassessment_nutrition",
                "reason_text": f"PID controller adjusted calories by {calorie_adj:+d} kcal based on weight progress",
                "diff_json": {
                    "calorie_adjustment": calorie_adj,
                    "error_kg": adjustments["calorie"]["error_kg"],
                    "target_change_kg": adjustments["target_weight_change_kg"],
                    "actual_change_kg": adjustments["actual_weight_change_kg"],
                    "confidence": adjustments["calorie"]["confidence"],
                },
            }
            events.append(nutrition_event)

        # Create training change event
        volume_mult = adjustments["volume"]["volume_multiplier"]
        if abs(volume_mult - 1.0) > 0.05:  # Only record significant changes
            training_event = {
                "program_id": program_id,
                "user_id": user_id,
                "change_type": "edit",
                "planned_entity_type": "session",
                "planned_entity_id": program_id,  # Program-level change
                "effective_date": effective_date.isoformat(),
                "reason_code": "biweekly_reassessment_volume",
                "reason_text": f"PID controller adjusted training volume to {volume_mult:.2f}x based on adherence and recovery",
                "diff_json": {
                    "volume_multiplier": volume_mult,
                    "adherence_factor": adjustments["volume"]["adherence_factor"],
                    "recovery_factor": adjustments["volume"]["recovery_factor"],
                    "confidence": adjustments["volume"]["confidence"],
                },
            }
            events.append(training_event)

        # Insert events
        event_ids = []
        for event in events:
            try:
                result = (
                    self.db.client.table("plan_change_events")
                    .insert(event)
                    .execute()
                )
                if result.data:
                    event_ids.append(result.data[0]["id"])
                    logger.info(
                        "plan_change_event_created",
                        event_id=result.data[0]["id"],
                        change_type=event["change_type"],
                        reason_code=event["reason_code"]
                    )
            except Exception as e:
                logger.error(
                    "plan_change_event_creation_failed",
                    event=event,
                    error=str(e)
                )

        return event_ids

    async def apply_adjustments_to_program(
        self,
        user_id: str,
        program_id: str,
        adjustments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply PID adjustments to current program (in-place modification).

        This updates the program's macro targets and training parameters
        without creating a new program version.

        Args:
            user_id: User UUID
            program_id: Program UUID
            adjustments: PID controller outputs

        Returns:
            Updated program data
        """
        logger.info(
            "applying_adjustments",
            user_id=user_id,
            program_id=program_id
        )

        try:
            # Get current program
            program = (
                self.db.client.table("programs")
                .select("*")
                .eq("id", program_id)
                .single()
                .execute()
            )

            if not program.data:
                raise ValueError(f"Program {program_id} not found")

            current_macros = program.data.get("macros", {})
            current_calories = current_macros.get("calories", 2000)

            # Apply calorie adjustment
            calorie_adj = adjustments["calorie"]["calorie_adjustment"]
            new_calories = current_calories + calorie_adj

            # Recalculate macros (keep protein constant, adjust carbs/fats)
            protein_g = current_macros.get("protein_g", 150)
            protein_cals = protein_g * 4

            fat_percent = 0.25  # 25% of calories
            fat_cals = new_calories * fat_percent
            fat_g = fat_cals / 9

            carb_cals = new_calories - protein_cals - fat_cals
            carb_g = carb_cals / 4

            updated_macros = {
                "calories": int(new_calories),
                "protein_g": int(protein_g),
                "carbs_g": int(carb_g),
                "fat_g": int(fat_g),
            }

            # Update program
            update_result = (
                self.db.client.table("programs")
                .update({
                    "macros": updated_macros,
                })
                .eq("id", program_id)
                .execute()
            )

            logger.info(
                "program_adjusted",
                program_id=program_id,
                old_calories=current_calories,
                new_calories=new_calories,
                volume_multiplier=adjustments["volume"]["volume_multiplier"]
            )

            return update_result.data[0] if update_result.data else None

        except Exception as e:
            logger.error(
                "adjustment_application_failed",
                program_id=program_id,
                error=str(e)
            )
            raise


# Singleton instance
reassessment_service = ReassessmentService()
