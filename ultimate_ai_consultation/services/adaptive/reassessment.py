"""
Bi-Weekly Reassessment System

Orchestrates the adaptive loop:
1. Aggregate user data from last 2 weeks
2. Run PID controllers to calculate adjustments
3. Generate updated plan version
4. Store adjustments in database
5. Notify user of changes

Called automatically every 14 days or manually triggered by user/coach.
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json

from .data_aggregator import DataAggregator, AggregatedData, TrendDirection
from .controllers import (
    AdaptiveController,
    CalorieAdjustment,
    VolumeAdjustment,
    generate_adjustment_summary,
)


@dataclass
class ReassessmentResult:
    """Complete reassessment output"""

    user_id: str
    old_plan_version: int
    new_plan_version: int
    assessment_date: datetime
    assessment_period_days: int

    # Aggregated data
    aggregated_data: AggregatedData

    # Adjustments
    calorie_adjustment: CalorieAdjustment
    volume_adjustment: VolumeAdjustment

    # New targets
    new_calorie_target: int
    new_macro_targets: Dict[str, int]
    new_volume_per_muscle: Dict[str, int]

    # Summary
    summary: Dict[str, any]
    user_message: str  # Human-readable message for user
    coach_notes: str  # Technical notes for coach/system


class ReassessmentOrchestrator:
    """
    Orchestrates bi-weekly reassessments and adaptive adjustments.
    """

    def __init__(self, supabase_client=None):
        """
        Args:
            supabase_client: Supabase client for database operations
        """
        self.supabase = supabase_client
        self.data_aggregator = DataAggregator(supabase_client)
        self.adaptive_controller = AdaptiveController()

    async def run_reassessment(
        self,
        user_id: str,
        plan_version: int,
        manual_trigger: bool = False,
    ) -> ReassessmentResult:
        """
        Run complete reassessment and generate adjustments.

        Args:
            user_id: User UUID
            plan_version: Current plan version
            manual_trigger: Whether manually triggered (vs automatic)

        Returns:
            ReassessmentResult with all adjustments
        """
        # Step 1: Get current plan and determine assessment period
        current_plan = await self._fetch_current_plan(user_id, plan_version)
        assessment_period = await self._determine_assessment_period(
            user_id, plan_version, manual_trigger
        )

        # Step 2: Aggregate user data
        aggregated_data = await self.data_aggregator.aggregate_progress(
            user_id=user_id,
            plan_version=plan_version,
            start_date=assessment_period["start_date"],
            end_date=assessment_period["end_date"],
        )

        # Step 3: Extract current targets from plan
        current_targets = self._extract_current_targets(current_plan)

        # Step 4: Run PID controllers
        calorie_adj, volume_adj = self.adaptive_controller.calculate_adjustments(
            target_rate_kg_per_week=aggregated_data.body_metrics.target_rate_kg_per_week,
            actual_rate_kg_per_week=aggregated_data.body_metrics.actual_rate_kg_per_week,
            current_calories=current_targets["calories"],
            current_volume_per_week=current_targets["total_volume"],
            target_adherence=0.85,  # Target 85% adherence
            actual_adherence=aggregated_data.training_adherence.adherence_rate,
            weeks_since_deload=current_targets["weeks_since_deload"],
            weeks_elapsed=aggregated_data.body_metrics.weeks_elapsed,
            overall_confidence=aggregated_data.overall_confidence,
        )

        # Step 5: Calculate new macro targets
        new_macro_targets = self._calculate_new_macros(
            new_calories=calorie_adj.recommended_calories,
            current_macros=current_targets["macros"],
        )

        # Step 6: Distribute new volume across muscle groups
        new_volume_per_muscle = self._redistribute_volume(
            new_total_volume=volume_adj.recommended_volume_per_week,
            current_volume_per_muscle=current_targets["volume_per_muscle"],
        )

        # Step 7: Generate summary and messages
        summary = generate_adjustment_summary(calorie_adj, volume_adj)
        user_message = self._generate_user_message(
            aggregated_data, calorie_adj, volume_adj
        )
        coach_notes = self._generate_coach_notes(
            aggregated_data, calorie_adj, volume_adj
        )

        # Step 8: Create reassessment result
        result = ReassessmentResult(
            user_id=user_id,
            old_plan_version=plan_version,
            new_plan_version=plan_version + 1,
            assessment_date=datetime.now(),
            assessment_period_days=aggregated_data.assessment_period_days,
            aggregated_data=aggregated_data,
            calorie_adjustment=calorie_adj,
            volume_adjustment=volume_adj,
            new_calorie_target=calorie_adj.recommended_calories,
            new_macro_targets=new_macro_targets,
            new_volume_per_muscle=new_volume_per_muscle,
            summary=summary,
            user_message=user_message,
            coach_notes=coach_notes,
        )

        # Step 9: Store in database
        await self._store_reassessment(result, current_plan)

        return result

    async def _fetch_current_plan(self, user_id: str, plan_version: int) -> Dict:
        """Fetch current plan from database"""
        if not self.supabase:
            return {}

        response = (
            self.supabase.table("plan_versions")
            .select("*")
            .eq("user_id", user_id)
            .eq("version", plan_version)
            .single()
            .execute()
        )
        return response.data

    async def _determine_assessment_period(
        self, user_id: str, plan_version: int, manual_trigger: bool
    ) -> Dict[str, datetime]:
        """Determine start and end dates for assessment period"""
        if not self.supabase:
            # Default to last 14 days for testing
            end_date = datetime.now()
            start_date = end_date - timedelta(days=14)
            return {"start_date": start_date, "end_date": end_date}

        # Get date of plan creation or last adjustment
        response = (
            self.supabase.table("plan_adjustments")
            .select("adjustment_date")
            .eq("user_id", user_id)
            .eq("plan_version", plan_version)
            .order("adjustment_date", desc=True)
            .limit(1)
            .execute()
        )

        if response.data:
            # Start from last adjustment
            start_date = datetime.fromisoformat(response.data[0]["adjustment_date"])
        else:
            # Start from plan creation
            plan_response = (
                self.supabase.table("plan_versions")
                .select("created_at")
                .eq("user_id", user_id)
                .eq("version", plan_version)
                .single()
                .execute()
            )
            start_date = datetime.fromisoformat(plan_response.data["created_at"])

        end_date = datetime.now()

        return {"start_date": start_date, "end_date": end_date}

    def _extract_current_targets(self, current_plan: Dict) -> Dict:
        """Extract current targets from plan JSON"""
        if not current_plan:
            # Defaults for testing
            return {
                "calories": 2500,
                "macros": {"protein_g": 180, "carbs_g": 300, "fat_g": 70},
                "total_volume": 80,
                "volume_per_muscle": {
                    "chest": 16,
                    "back": 18,
                    "shoulders": 14,
                    "quads": 14,
                    "hamstrings": 12,
                },
                "weeks_since_deload": 2,
            }

        plan_data = current_plan.get("data", {})
        training_program = plan_data.get("training_program", {})

        # Calculate weeks since deload
        created_at = datetime.fromisoformat(current_plan["created_at"])
        weeks_since_plan_start = (datetime.now() - created_at).days / 7
        deload_week = training_program.get("deload_week", 5)
        weeks_since_deload = int(weeks_since_plan_start % deload_week)

        return {
            "calories": plan_data.get("daily_calorie_target", 2500),
            "macros": plan_data.get("macro_targets", {}),
            "total_volume": sum(
                training_program.get("weekly_volume_per_muscle", {}).values()
            ),
            "volume_per_muscle": training_program.get("weekly_volume_per_muscle", {}),
            "weeks_since_deload": weeks_since_deload,
        }

    def _calculate_new_macros(
        self, new_calories: int, current_macros: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Calculate new macro targets based on new calorie target.

        Maintains same macro ratios but scales to new calories.
        """
        current_calories = (
            current_macros.get("protein_g", 0) * 4
            + current_macros.get("carbs_g", 0) * 4
            + current_macros.get("fat_g", 0) * 9
        )

        if current_calories == 0:
            # Fallback to default ratios
            protein_g = int(new_calories * 0.30 / 4)  # 30% protein
            fat_g = int(new_calories * 0.25 / 9)  # 25% fat
            carbs_g = int((new_calories - protein_g * 4 - fat_g * 9) / 4)  # Remainder
        else:
            # Scale existing macros proportionally
            scale_factor = new_calories / current_calories
            protein_g = int(current_macros.get("protein_g", 0) * scale_factor)
            carbs_g = int(current_macros.get("carbs_g", 0) * scale_factor)
            fat_g = int(current_macros.get("fat_g", 0) * scale_factor)

        return {"protein_g": protein_g, "carbs_g": carbs_g, "fat_g": fat_g}

    def _redistribute_volume(
        self, new_total_volume: int, current_volume_per_muscle: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Redistribute new total volume across muscle groups.

        Maintains same proportions as current distribution.
        """
        if not current_volume_per_muscle:
            # Default distribution
            return {
                "chest": int(new_total_volume * 0.20),
                "back": int(new_total_volume * 0.225),
                "shoulders": int(new_total_volume * 0.175),
                "quads": int(new_total_volume * 0.175),
                "hamstrings": int(new_total_volume * 0.15),
                "biceps": int(new_total_volume * 0.0375),
                "triceps": int(new_total_volume * 0.0375),
            }

        current_total = sum(current_volume_per_muscle.values())
        if current_total == 0:
            current_total = 1  # Avoid division by zero

        new_distribution = {}
        for muscle, current_sets in current_volume_per_muscle.items():
            proportion = current_sets / current_total
            new_sets = int(new_total_volume * proportion)
            new_distribution[muscle] = new_sets

        return new_distribution

    def _generate_user_message(
        self,
        aggregated_data: AggregatedData,
        calorie_adj: CalorieAdjustment,
        volume_adj: VolumeAdjustment,
    ) -> str:
        """Generate friendly message for user"""
        lines = []

        # Header
        lines.append("🎯 Your 2-Week Progress Check-In")
        lines.append("")

        # Progress summary
        body_metrics = aggregated_data.body_metrics
        lines.append("📊 Progress Summary:")
        lines.append(
            f"  • Weight: {body_metrics.start_weight_kg:.1f} kg → {body_metrics.current_weight_kg:.1f} kg "
            f"({body_metrics.weight_change_kg:+.1f} kg)"
        )
        lines.append(
            f"  • Rate: {body_metrics.actual_rate_kg_per_week:+.2f} kg/week "
            f"(target: {body_metrics.target_rate_kg_per_week:+.2f} kg/week)"
        )
        lines.append(
            f"  • Meal logging: {aggregated_data.meal_adherence.adherence_rate:.0%}"
        )
        lines.append(
            f"  • Training adherence: {aggregated_data.training_adherence.adherence_rate:.0%}"
        )
        lines.append("")

        # Adjustments
        if (
            calorie_adj.adjustment_type.value != "maintain"
            or volume_adj.adjustment_type.value != "maintain"
        ):
            lines.append("🔄 Plan Adjustments:")

            if calorie_adj.adjustment_type.value != "maintain":
                lines.append(
                    f"  • Calories: {calorie_adj.current_calories} → {calorie_adj.recommended_calories} kcal/day "
                    f"({calorie_adj.adjustment_percentage:+.0f}%)"
                )
                lines.append(f"    Why: {calorie_adj.rationale}")

            if volume_adj.adjustment_type.value != "maintain":
                lines.append(
                    f"  • Training Volume: {volume_adj.current_volume_per_week} → {volume_adj.recommended_volume_per_week} sets/week "
                    f"({volume_adj.adjustment_percentage:+.0f}%)"
                )
                lines.append(f"    Why: {volume_adj.rationale}")

            lines.append("")
        else:
            lines.append("✅ You're on track! No changes needed.")
            lines.append("")

        # Encouragement and next steps
        if body_metrics.trend_direction == TrendDirection.ON_TRACK:
            lines.append(
                "💪 Keep up the great work! Your progress is exactly where we want it."
            )
        elif body_metrics.trend_direction == TrendDirection.STALLED:
            lines.append(
                "📈 We've made adjustments to get you back on track. Stay consistent!"
            )
        elif body_metrics.trend_direction == TrendDirection.EXCEEDING:
            lines.append(
                "⚠️  We've adjusted your plan to ensure healthy, sustainable progress."
            )

        lines.append("")
        lines.append("Next check-in: 2 weeks from today. Keep logging!")

        return "\n".join(lines)

    def _generate_coach_notes(
        self,
        aggregated_data: AggregatedData,
        calorie_adj: CalorieAdjustment,
        volume_adj: VolumeAdjustment,
    ) -> str:
        """Generate technical notes for coach/system"""
        notes = []

        notes.append(f"Reassessment Period: {aggregated_data.assessment_period_days} days")
        notes.append(f"Overall Confidence: {aggregated_data.overall_confidence:.2f}")
        notes.append("")

        notes.append("Data Quality:")
        notes.append(f"  - Meal logging: {aggregated_data.meal_adherence.data_quality.value}")
        notes.append(
            f"  - Training logging: {aggregated_data.training_adherence.data_quality.value}"
        )
        notes.append(f"  - Body metrics: {aggregated_data.body_metrics.data_quality.value}")
        notes.append("")

        if aggregated_data.red_flags:
            notes.append("⚠️  Red Flags:")
            for flag in aggregated_data.red_flags:
                notes.append(f"  - {flag}")
            notes.append("")

        notes.append("PID Controller Adjustments:")
        notes.append(
            f"  - Calorie: {calorie_adj.current_calories} → {calorie_adj.recommended_calories} "
            f"({calorie_adj.adjustment_amount:+d} kcal)"
        )
        notes.append(
            f"  - Volume: {volume_adj.current_volume_per_week} → {volume_adj.recommended_volume_per_week} "
            f"({volume_adj.adjustment_amount:+d} sets)"
        )
        notes.append("")

        if aggregated_data.recommendations:
            notes.append("System Recommendations:")
            for rec in aggregated_data.recommendations:
                notes.append(f"  - {rec}")

        return "\n".join(notes)

    async def _store_reassessment(
        self, result: ReassessmentResult, current_plan: Dict
    ):
        """Store reassessment results in database"""
        if not self.supabase:
            return  # Skip for testing

        # 1. Create new plan version (copy current plan with updated targets)
        new_plan_data = current_plan.get("data", {}).copy()
        new_plan_data["daily_calorie_target"] = result.new_calorie_target
        new_plan_data["macro_targets"] = result.new_macro_targets
        if "training_program" in new_plan_data:
            new_plan_data["training_program"]["weekly_volume_per_muscle"] = (
                result.new_volume_per_muscle
            )

        # Insert new plan version
        self.supabase.table("plan_versions").insert(
            {
                "user_id": result.user_id,
                "version": result.new_plan_version,
                "data": new_plan_data,
                "is_active": True,
            }
        ).execute()

        # Mark old plan as inactive
        self.supabase.table("plan_versions").update({"is_active": False}).eq(
            "user_id", result.user_id
        ).eq("version", result.old_plan_version).execute()

        # 2. Store adjustment record
        self.supabase.table("plan_adjustments").insert(
            {
                "user_id": result.user_id,
                "plan_version": result.new_plan_version,
                "adjustment_date": result.assessment_date.isoformat(),
                "assessment_period_days": result.assessment_period_days,
                "previous_calories": result.calorie_adjustment.current_calories,
                "new_calories": result.calorie_adjustment.recommended_calories,
                "previous_volume": result.volume_adjustment.current_volume_per_week,
                "new_volume": result.volume_adjustment.recommended_volume_per_week,
                "adherence_metrics": {
                    "meal_adherence": result.aggregated_data.meal_adherence.adherence_rate,
                    "training_adherence": result.aggregated_data.training_adherence.adherence_rate,
                },
                "progress_metrics": {
                    "weight_change_kg": result.aggregated_data.body_metrics.weight_change_kg,
                    "actual_rate": result.aggregated_data.body_metrics.actual_rate_kg_per_week,
                    "target_rate": result.aggregated_data.body_metrics.target_rate_kg_per_week,
                },
                "adjustments_rationale": {
                    "calorie": result.calorie_adjustment.rationale,
                    "volume": result.volume_adjustment.rationale,
                },
                "confidence": result.aggregated_data.overall_confidence,
                "notes": result.coach_notes,
            }
        ).execute()

    def reset_controllers(self):
        """Reset PID controllers (call when starting new plan)"""
        self.adaptive_controller.reset_all()
