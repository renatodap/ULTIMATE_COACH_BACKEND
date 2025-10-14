"""
Data Aggregator

Pulls and aggregates data from ULTIMATE_COACH_BACKEND tables:
- meals (nutrition adherence)
- activities (training adherence and volume)
- body_metrics (weight, measurements)
- coach_conversations (sentiment signals)

Computes:
- Adherence rates (meal plan, training plan)
- Progress rates (weight change, strength gains)
- Trend detection (stalling, regressing, exceeding targets)
- Confidence metrics (data quality)
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import statistics


class TrendDirection(str, Enum):
    """Progress trend classification"""

    EXCEEDING = "exceeding"  # Progressing faster than target
    ON_TRACK = "on_track"  # Within expected range
    SLOW = "slow"  # Progressing slower than target
    STALLED = "stalled"  # No progress for 2+ weeks
    REGRESSING = "regressing"  # Moving backward


class DataQuality(str, Enum):
    """Data completeness quality"""

    HIGH = "high"  # >80% logged
    MEDIUM = "medium"  # 50-80% logged
    LOW = "low"  # <50% logged
    INSUFFICIENT = "insufficient"  # <3 data points


@dataclass
class MealAdherence:
    """Meal plan adherence statistics"""

    total_days: int
    logged_days: int
    adherence_rate: float  # % of days with meals logged
    avg_calories_per_day: float
    avg_protein_per_day: float
    avg_carbs_per_day: float
    avg_fat_per_day: float
    target_calories: int
    target_protein: int
    target_carbs: int
    target_fat: int
    calorie_deviation_pct: float  # % deviation from target
    protein_deviation_pct: float
    data_quality: DataQuality
    confidence: float  # 0.0-1.0


@dataclass
class TrainingAdherence:
    """Training plan adherence statistics"""

    total_sessions_planned: int
    total_sessions_completed: int
    adherence_rate: float  # % of planned sessions completed
    avg_volume_per_week: float  # Total sets across all muscles
    target_volume_per_week: float
    volume_deviation_pct: float
    missed_sessions_pattern: List[str]  # Which sessions are commonly missed
    data_quality: DataQuality
    confidence: float


@dataclass
class BodyMetricsTrend:
    """Body metrics progress tracking"""

    start_weight_kg: float
    current_weight_kg: float
    weight_change_kg: float
    weight_change_pct: float
    weeks_elapsed: float
    actual_rate_kg_per_week: float
    target_rate_kg_per_week: float
    trend_direction: TrendDirection
    measurements: Dict[str, float]  # waist, chest, arms, etc.
    data_quality: DataQuality
    confidence: float


@dataclass
class AggregatedData:
    """Complete aggregated data for reassessment"""

    user_id: str
    plan_version: int
    assessment_period_days: int
    start_date: datetime
    end_date: datetime
    meal_adherence: MealAdherence
    training_adherence: TrainingAdherence
    body_metrics: BodyMetricsTrend
    overall_confidence: float  # Combined confidence score
    red_flags: List[str]  # Issues requiring attention
    recommendations: List[str]  # Suggested adjustments


class DataAggregator:
    """Aggregates user data from database for adaptive adjustments"""

    def __init__(self, supabase_client=None):
        """
        Args:
            supabase_client: Supabase client instance (optional, for testing can be mocked)
        """
        self.supabase = supabase_client

    async def aggregate_progress(
        self,
        user_id: str,
        plan_version: int,
        start_date: datetime,
        end_date: datetime,
    ) -> AggregatedData:
        """
        Aggregate all user data for the assessment period.

        Args:
            user_id: User UUID
            plan_version: Current plan version
            start_date: Start of assessment period (typically plan start or last reassessment)
            end_date: End of assessment period (typically now)

        Returns:
            AggregatedData with all metrics and trends
        """
        days_elapsed = (end_date - start_date).days

        # Fetch data from database (or mock if no client)
        meals_data = await self._fetch_meals(user_id, start_date, end_date)
        activities_data = await self._fetch_activities(user_id, start_date, end_date)
        body_metrics_data = await self._fetch_body_metrics(user_id, start_date, end_date)
        plan_data = await self._fetch_plan(user_id, plan_version)

        # Calculate adherence metrics
        meal_adherence = self._calculate_meal_adherence(
            meals_data, plan_data, days_elapsed
        )
        training_adherence = self._calculate_training_adherence(
            activities_data, plan_data, days_elapsed
        )
        body_metrics_trend = self._calculate_body_metrics_trend(
            body_metrics_data, plan_data, days_elapsed
        )

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            meal_adherence, training_adherence, body_metrics_trend
        )

        # Detect red flags and generate recommendations
        red_flags = self._detect_red_flags(
            meal_adherence, training_adherence, body_metrics_trend
        )
        recommendations = self._generate_recommendations(
            meal_adherence, training_adherence, body_metrics_trend
        )

        return AggregatedData(
            user_id=user_id,
            plan_version=plan_version,
            assessment_period_days=days_elapsed,
            start_date=start_date,
            end_date=end_date,
            meal_adherence=meal_adherence,
            training_adherence=training_adherence,
            body_metrics=body_metrics_trend,
            overall_confidence=overall_confidence,
            red_flags=red_flags,
            recommendations=recommendations,
        )

    async def _fetch_meals(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> List[Dict]:
        """Fetch meals from database"""
        if not self.supabase:
            return []  # Return empty for testing

        response = (
            self.supabase.table("meals")
            .select("*")
            .eq("user_id", user_id)
            .gte("created_at", start_date.isoformat())
            .lte("created_at", end_date.isoformat())
            .execute()
        )
        return response.data

    async def _fetch_activities(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> List[Dict]:
        """Fetch activities from database"""
        if not self.supabase:
            return []

        response = (
            self.supabase.table("activities")
            .select("*")
            .eq("user_id", user_id)
            .gte("created_at", start_date.isoformat())
            .lte("created_at", end_date.isoformat())
            .execute()
        )
        return response.data

    async def _fetch_body_metrics(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> List[Dict]:
        """Fetch body metrics from database"""
        if not self.supabase:
            return []

        response = (
            self.supabase.table("body_metrics")
            .select("*")
            .eq("user_id", user_id)
            .gte("recorded_at", start_date.isoformat())
            .lte("recorded_at", end_date.isoformat())
            .order("recorded_at", desc=False)
            .execute()
        )
        return response.data

    async def _fetch_plan(self, user_id: str, plan_version: int) -> Dict:
        """Fetch plan data from database"""
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

    def _calculate_meal_adherence(
        self, meals_data: List[Dict], plan_data: Dict, days_elapsed: int
    ) -> MealAdherence:
        """Calculate nutrition adherence from meals data"""
        if not meals_data or days_elapsed == 0:
            return MealAdherence(
                total_days=days_elapsed,
                logged_days=0,
                adherence_rate=0.0,
                avg_calories_per_day=0.0,
                avg_protein_per_day=0.0,
                avg_carbs_per_day=0.0,
                avg_fat_per_day=0.0,
                target_calories=2500,  # Default, will be overridden by plan
                target_protein=150,
                target_carbs=300,
                target_fat=70,
                calorie_deviation_pct=0.0,
                protein_deviation_pct=0.0,
                data_quality=DataQuality.INSUFFICIENT,
                confidence=0.0,
            )

        # Extract targets from plan
        plan_json = plan_data.get("data", {}) if plan_data else {}
        target_calories = plan_json.get("daily_calorie_target", 2500)
        macro_targets = plan_json.get("macro_targets", {})
        target_protein = macro_targets.get("protein_g", 150)
        target_carbs = macro_targets.get("carbs_g", 300)
        target_fat = macro_targets.get("fat_g", 70)

        # Group meals by day
        meals_by_day = {}
        for meal in meals_data:
            date_key = meal["created_at"][:10]  # YYYY-MM-DD
            if date_key not in meals_by_day:
                meals_by_day[date_key] = []
            meals_by_day[date_key].append(meal)

        # Calculate daily totals
        daily_totals = []
        for day, day_meals in meals_by_day.items():
            total_calories = sum(m.get("calories", 0) for m in day_meals)
            total_protein = sum(m.get("protein_g", 0) for m in day_meals)
            total_carbs = sum(m.get("carbs_g", 0) for m in day_meals)
            total_fat = sum(m.get("fat_g", 0) for m in day_meals)

            daily_totals.append({
                "calories": total_calories,
                "protein": total_protein,
                "carbs": total_carbs,
                "fat": total_fat,
            })

        # Calculate averages
        logged_days = len(meals_by_day)
        adherence_rate = logged_days / days_elapsed if days_elapsed > 0 else 0.0

        avg_calories = statistics.mean([d["calories"] for d in daily_totals])
        avg_protein = statistics.mean([d["protein"] for d in daily_totals])
        avg_carbs = statistics.mean([d["carbs"] for d in daily_totals])
        avg_fat = statistics.mean([d["fat"] for d in daily_totals])

        # Calculate deviations
        calorie_deviation = ((avg_calories / target_calories) - 1) * 100
        protein_deviation = ((avg_protein / target_protein) - 1) * 100

        # Determine data quality
        if adherence_rate >= 0.8:
            data_quality = DataQuality.HIGH
            confidence = 0.9
        elif adherence_rate >= 0.5:
            data_quality = DataQuality.MEDIUM
            confidence = 0.7
        elif adherence_rate >= 0.3:
            data_quality = DataQuality.LOW
            confidence = 0.4
        else:
            data_quality = DataQuality.INSUFFICIENT
            confidence = 0.2

        return MealAdherence(
            total_days=days_elapsed,
            logged_days=logged_days,
            adherence_rate=adherence_rate,
            avg_calories_per_day=avg_calories,
            avg_protein_per_day=avg_protein,
            avg_carbs_per_day=avg_carbs,
            avg_fat_per_day=avg_fat,
            target_calories=target_calories,
            target_protein=target_protein,
            target_carbs=target_carbs,
            target_fat=target_fat,
            calorie_deviation_pct=calorie_deviation,
            protein_deviation_pct=protein_deviation,
            data_quality=data_quality,
            confidence=confidence,
        )

    def _calculate_training_adherence(
        self, activities_data: List[Dict], plan_data: Dict, days_elapsed: int
    ) -> TrainingAdherence:
        """Calculate training adherence from activities data"""
        if not activities_data:
            return TrainingAdherence(
                total_sessions_planned=0,
                total_sessions_completed=0,
                adherence_rate=0.0,
                avg_volume_per_week=0.0,
                target_volume_per_week=0.0,
                volume_deviation_pct=0.0,
                missed_sessions_pattern=[],
                data_quality=DataQuality.INSUFFICIENT,
                confidence=0.0,
            )

        # Extract plan targets
        plan_json = plan_data.get("data", {}) if plan_data else {}
        training_program = plan_json.get("training_program", {})
        sessions_per_week = training_program.get("sessions_per_week", 4)
        weeks_elapsed = days_elapsed / 7

        # Calculate planned sessions
        total_sessions_planned = int(sessions_per_week * weeks_elapsed)

        # Count completed sessions (activities with type "workout" or similar)
        workout_activities = [
            a for a in activities_data
            if a.get("activity_type", "").lower() in ["workout", "training", "resistance"]
        ]
        total_sessions_completed = len(workout_activities)

        adherence_rate = (
            total_sessions_completed / total_sessions_planned
            if total_sessions_planned > 0
            else 0.0
        )

        # Calculate volume (total sets across all workouts)
        total_volume = 0
        for activity in workout_activities:
            # Assuming activities have a volume field or we calculate from exercises
            total_volume += activity.get("total_sets", 0)

        avg_volume_per_week = total_volume / weeks_elapsed if weeks_elapsed > 0 else 0.0

        # Target volume (sum of all muscle group volumes)
        weekly_volume_per_muscle = training_program.get("weekly_volume_per_muscle", {})
        target_volume_per_week = sum(weekly_volume_per_muscle.values())

        volume_deviation = (
            ((avg_volume_per_week / target_volume_per_week) - 1) * 100
            if target_volume_per_week > 0
            else 0.0
        )

        # Determine data quality
        if adherence_rate >= 0.8:
            data_quality = DataQuality.HIGH
            confidence = 0.9
        elif adherence_rate >= 0.6:
            data_quality = DataQuality.MEDIUM
            confidence = 0.7
        elif adherence_rate >= 0.4:
            data_quality = DataQuality.LOW
            confidence = 0.5
        else:
            data_quality = DataQuality.INSUFFICIENT
            confidence = 0.3

        return TrainingAdherence(
            total_sessions_planned=total_sessions_planned,
            total_sessions_completed=total_sessions_completed,
            adherence_rate=adherence_rate,
            avg_volume_per_week=avg_volume_per_week,
            target_volume_per_week=target_volume_per_week,
            volume_deviation_pct=volume_deviation,
            missed_sessions_pattern=[],  # TODO: Analyze which days are missed
            data_quality=data_quality,
            confidence=confidence,
        )

    def _calculate_body_metrics_trend(
        self, body_metrics_data: List[Dict], plan_data: Dict, days_elapsed: int
    ) -> BodyMetricsTrend:
        """Calculate body metrics trends (weight, measurements)"""
        if not body_metrics_data or len(body_metrics_data) < 2:
            return BodyMetricsTrend(
                start_weight_kg=0.0,
                current_weight_kg=0.0,
                weight_change_kg=0.0,
                weight_change_pct=0.0,
                weeks_elapsed=days_elapsed / 7,
                actual_rate_kg_per_week=0.0,
                target_rate_kg_per_week=0.0,
                trend_direction=TrendDirection.STALLED,
                measurements={},
                data_quality=DataQuality.INSUFFICIENT,
                confidence=0.0,
            )

        # Sort by date
        sorted_metrics = sorted(body_metrics_data, key=lambda x: x["recorded_at"])

        # Get start and current weight
        start_weight = sorted_metrics[0].get("weight_kg", 0.0)
        current_weight = sorted_metrics[-1].get("weight_kg", 0.0)
        weight_change = current_weight - start_weight
        weight_change_pct = (weight_change / start_weight) * 100 if start_weight > 0 else 0.0

        weeks_elapsed = days_elapsed / 7
        actual_rate = weight_change / weeks_elapsed if weeks_elapsed > 0 else 0.0

        # Extract target rate from plan
        plan_json = plan_data.get("data", {}) if plan_data else {}
        target_rate = plan_json.get("rate_of_change_kg_per_week", 0.0)

        # Determine trend direction
        if abs(actual_rate) < 0.1:  # Less than 0.1 kg/week = stalled
            trend_direction = TrendDirection.STALLED
        elif target_rate > 0:  # Gaining weight (muscle gain goal)
            if actual_rate > target_rate * 1.3:
                trend_direction = TrendDirection.EXCEEDING
            elif actual_rate >= target_rate * 0.7:
                trend_direction = TrendDirection.ON_TRACK
            elif actual_rate >= target_rate * 0.3:
                trend_direction = TrendDirection.SLOW
            else:
                trend_direction = TrendDirection.STALLED
        elif target_rate < 0:  # Losing weight (fat loss goal)
            if actual_rate < target_rate * 1.3:  # More negative = faster loss
                trend_direction = TrendDirection.EXCEEDING
            elif actual_rate <= target_rate * 0.7:
                trend_direction = TrendDirection.ON_TRACK
            elif actual_rate <= target_rate * 0.3:
                trend_direction = TrendDirection.SLOW
            else:
                trend_direction = TrendDirection.STALLED
        else:  # Maintenance
            if abs(actual_rate) < 0.2:
                trend_direction = TrendDirection.ON_TRACK
            else:
                trend_direction = TrendDirection.EXCEEDING

        # Extract measurements (waist, chest, etc.)
        latest_measurements = sorted_metrics[-1].get("measurements", {})

        # Data quality based on frequency
        measurements_count = len(body_metrics_data)
        expected_measurements = weeks_elapsed  # Expect weekly weigh-ins
        measurement_rate = measurements_count / expected_measurements if expected_measurements > 0 else 0.0

        if measurement_rate >= 0.8:
            data_quality = DataQuality.HIGH
            confidence = 0.9
        elif measurement_rate >= 0.5:
            data_quality = DataQuality.MEDIUM
            confidence = 0.7
        else:
            data_quality = DataQuality.LOW
            confidence = 0.5

        return BodyMetricsTrend(
            start_weight_kg=start_weight,
            current_weight_kg=current_weight,
            weight_change_kg=weight_change,
            weight_change_pct=weight_change_pct,
            weeks_elapsed=weeks_elapsed,
            actual_rate_kg_per_week=actual_rate,
            target_rate_kg_per_week=target_rate,
            trend_direction=trend_direction,
            measurements=latest_measurements,
            data_quality=data_quality,
            confidence=confidence,
        )

    def _calculate_overall_confidence(
        self,
        meal_adherence: MealAdherence,
        training_adherence: TrainingAdherence,
        body_metrics: BodyMetricsTrend,
    ) -> float:
        """Calculate overall confidence score (weighted average)"""
        weights = {
            "meal": 0.3,
            "training": 0.3,
            "body_metrics": 0.4,  # Weight progress is most important
        }

        overall = (
            meal_adherence.confidence * weights["meal"]
            + training_adherence.confidence * weights["training"]
            + body_metrics.confidence * weights["body_metrics"]
        )

        return round(overall, 2)

    def _detect_red_flags(
        self,
        meal_adherence: MealAdherence,
        training_adherence: TrainingAdherence,
        body_metrics: BodyMetricsTrend,
    ) -> List[str]:
        """Detect issues requiring immediate attention"""
        red_flags = []

        # Meal adherence issues
        if meal_adherence.adherence_rate < 0.5:
            red_flags.append(
                f"Low meal logging adherence ({meal_adherence.adherence_rate:.1%}). "
                "Adjust goals to be more achievable or increase support."
            )

        if abs(meal_adherence.calorie_deviation_pct) > 20:
            red_flags.append(
                f"Calories {meal_adherence.calorie_deviation_pct:+.0f}% off target. "
                "Plan may be too restrictive or user needs guidance."
            )

        # Training adherence issues
        if training_adherence.adherence_rate < 0.6:
            red_flags.append(
                f"Low training adherence ({training_adherence.adherence_rate:.1%}). "
                "Consider reducing frequency or addressing barriers."
            )

        # Progress issues
        if body_metrics.trend_direction == TrendDirection.STALLED:
            red_flags.append(
                "Weight has stalled for 2+ weeks. Calorie adjustment needed."
            )

        if body_metrics.trend_direction == TrendDirection.EXCEEDING:
            if body_metrics.target_rate_kg_per_week < 0:  # Fat loss
                red_flags.append(
                    f"Losing weight too fast ({body_metrics.actual_rate_kg_per_week:.2f} kg/week). "
                    "Risk of muscle loss. Increase calories."
                )
            else:  # Muscle gain
                red_flags.append(
                    f"Gaining weight too fast ({body_metrics.actual_rate_kg_per_week:.2f} kg/week). "
                    "Excessive fat gain likely. Reduce calories."
                )

        # Data quality issues
        if body_metrics.data_quality == DataQuality.INSUFFICIENT:
            red_flags.append(
                "Insufficient body weight data (<50% of expected check-ins). "
                "Cannot accurately assess progress."
            )

        return red_flags

    def _generate_recommendations(
        self,
        meal_adherence: MealAdherence,
        training_adherence: TrainingAdherence,
        body_metrics: BodyMetricsTrend,
    ) -> List[str]:
        """Generate adjustment recommendations"""
        recommendations = []

        # Meal plan adjustments
        if meal_adherence.adherence_rate < 0.7:
            recommendations.append(
                "Consider simplifying meal plan (fewer meals per day, easier recipes)."
            )

        # Training adjustments
        if training_adherence.adherence_rate < 0.7:
            recommendations.append(
                f"Reduce training frequency from current target. "
                "User completing {training_adherence.adherence_rate:.0%} of sessions."
            )

        # Progress-based adjustments
        if body_metrics.trend_direction == TrendDirection.STALLED:
            if body_metrics.target_rate_kg_per_week < 0:
                recommendations.append(
                    "Increase calorie deficit by 10-15% to resume fat loss."
                )
            elif body_metrics.target_rate_kg_per_week > 0:
                recommendations.append(
                    "Increase calorie surplus by 10% to resume muscle gain."
                )

        if body_metrics.trend_direction == TrendDirection.SLOW:
            recommendations.append(
                f"Progress is slow but present. Consider small calorie adjustment (5-10%)."
            )

        if body_metrics.trend_direction == TrendDirection.ON_TRACK:
            recommendations.append(
                "Progress is on track. Maintain current plan with minor volume progression."
            )

        return recommendations
