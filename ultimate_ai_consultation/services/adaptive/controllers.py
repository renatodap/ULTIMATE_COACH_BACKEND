"""
PID Controllers for Adaptive Adjustments

Implements Proportional-Integral-Derivative controllers for:
1. Calorie adjustment (based on weight change rate)
2. Volume adjustment (based on adherence and fatigue)
3. Intensity modulation (based on performance trends)

PID controllers provide smooth, automatic adjustments that prevent
overcorrection while responding quickly to trends.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class AdjustmentType(str, Enum):
    """Type of adjustment being made"""

    CALORIE_INCREASE = "calorie_increase"
    CALORIE_DECREASE = "calorie_decrease"
    VOLUME_INCREASE = "volume_increase"
    VOLUME_DECREASE = "volume_decrease"
    DELOAD = "deload"
    MAINTAIN = "maintain"


@dataclass
class PIDParameters:
    """PID controller tuning parameters"""

    Kp: float  # Proportional gain
    Ki: float  # Integral gain
    Kd: float  # Derivative gain
    min_output: float  # Minimum adjustment
    max_output: float  # Maximum adjustment
    integral_windup_limit: float  # Prevent integral term explosion


@dataclass
class ControllerState:
    """State of PID controller over time"""

    previous_error: float = 0.0
    integral_accumulator: float = 0.0
    last_adjustment: float = 0.0


@dataclass
class CalorieAdjustment:
    """Recommended calorie adjustment"""

    adjustment_type: AdjustmentType
    current_calories: int
    recommended_calories: int
    adjustment_amount: int
    adjustment_percentage: float
    rationale: str
    confidence: float


@dataclass
class VolumeAdjustment:
    """Recommended training volume adjustment"""

    adjustment_type: AdjustmentType
    current_volume_per_week: int
    recommended_volume_per_week: int
    adjustment_amount: int
    adjustment_percentage: float
    rationale: str
    confidence: float


class CaloriePIDController:
    """
    PID controller for calorie adjustments based on weight change rate.

    Tuned for:
    - Fast response to sustained deviations (Kp)
    - Gradual correction of accumulated error (Ki)
    - Damping of rapid fluctuations (Kd)
    """

    def __init__(self):
        # Conservative PID parameters for calorie adjustment
        # Tuned to prevent large swings while responding to trends
        self.params = PIDParameters(
            Kp=200.0,  # 200 kcal per 0.1 kg/week deviation
            Ki=50.0,  # 50 kcal per accumulated error unit
            Kd=100.0,  # 100 kcal damping on rapid changes
            min_output=-500.0,  # Max decrease per adjustment
            max_output=500.0,  # Max increase per adjustment
            integral_windup_limit=3.0,  # Limit integral to ±3 units
        )
        self.state = ControllerState()

    def calculate_adjustment(
        self,
        target_rate_kg_per_week: float,
        actual_rate_kg_per_week: float,
        current_calories: int,
        weeks_elapsed: float,
        confidence: float,
    ) -> CalorieAdjustment:
        """
        Calculate recommended calorie adjustment.

        Args:
            target_rate_kg_per_week: Target weight change (negative for loss, positive for gain)
            actual_rate_kg_per_week: Actual weight change rate
            current_calories: Current daily calorie target
            weeks_elapsed: Time since last adjustment
            confidence: Data quality confidence (0.0-1.0)

        Returns:
            CalorieAdjustment with recommendation
        """
        # Calculate error (target - actual)
        # Positive error = losing slower than target (or gaining faster)
        # Negative error = losing faster than target (or gaining slower)
        error = target_rate_kg_per_week - actual_rate_kg_per_week

        # Proportional term
        P = self.params.Kp * error

        # Integral term (accumulated error over time)
        self.state.integral_accumulator += error * weeks_elapsed
        # Prevent integral windup
        self.state.integral_accumulator = max(
            min(self.state.integral_accumulator, self.params.integral_windup_limit),
            -self.params.integral_windup_limit,
        )
        I = self.params.Ki * self.state.integral_accumulator

        # Derivative term (rate of change of error)
        derivative = (error - self.state.previous_error) / weeks_elapsed if weeks_elapsed > 0 else 0.0
        D = self.params.Kd * derivative

        # Calculate raw adjustment
        raw_adjustment = P + I + D

        # Apply confidence scaling (reduce adjustment if data quality is poor)
        scaled_adjustment = raw_adjustment * confidence

        # Clamp to min/max
        clamped_adjustment = max(
            min(scaled_adjustment, self.params.max_output), self.params.min_output
        )

        # Round to nearest 50 kcal for practicality
        final_adjustment = round(clamped_adjustment / 50) * 50

        # Calculate new calorie target
        recommended_calories = current_calories + final_adjustment

        # Safety bounds (never go below 1200 for women, 1500 for men - assume worst case)
        recommended_calories = max(recommended_calories, 1200)

        # Determine adjustment type
        if abs(final_adjustment) < 50:
            adjustment_type = AdjustmentType.MAINTAIN
        elif final_adjustment > 0:
            adjustment_type = AdjustmentType.CALORIE_INCREASE
        else:
            adjustment_type = AdjustmentType.CALORIE_DECREASE

        # Generate rationale
        rationale = self._generate_calorie_rationale(
            error, final_adjustment, target_rate_kg_per_week, actual_rate_kg_per_week
        )

        # Update state
        self.state.previous_error = error
        self.state.last_adjustment = final_adjustment

        return CalorieAdjustment(
            adjustment_type=adjustment_type,
            current_calories=current_calories,
            recommended_calories=int(recommended_calories),
            adjustment_amount=int(final_adjustment),
            adjustment_percentage=(final_adjustment / current_calories) * 100,
            rationale=rationale,
            confidence=confidence,
        )

    def _generate_calorie_rationale(
        self,
        error: float,
        adjustment: float,
        target_rate: float,
        actual_rate: float,
    ) -> str:
        """Generate human-readable rationale for adjustment"""
        if abs(adjustment) < 50:
            return (
                f"Progress is on track (target: {target_rate:+.2f} kg/week, "
                f"actual: {actual_rate:+.2f} kg/week). Maintaining current calories."
            )

        if target_rate < 0:  # Fat loss
            if error > 0:  # Losing slower than target
                return (
                    f"Fat loss is slower than target ({actual_rate:.2f} vs {target_rate:.2f} kg/week). "
                    f"Decreasing calories by {abs(adjustment):.0f} kcal/day to increase deficit."
                )
            else:  # Losing faster than target
                return (
                    f"Fat loss is faster than target ({actual_rate:.2f} vs {target_rate:.2f} kg/week). "
                    f"Increasing calories by {adjustment:.0f} kcal/day to preserve muscle."
                )
        else:  # Muscle gain
            if error > 0:  # Gaining slower than target
                return (
                    f"Muscle gain is slower than target ({actual_rate:+.2f} vs {target_rate:+.2f} kg/week). "
                    f"Increasing calories by {adjustment:.0f} kcal/day to increase surplus."
                )
            else:  # Gaining faster than target
                return (
                    f"Weight gain is faster than target ({actual_rate:+.2f} vs {target_rate:+.2f} kg/week). "
                    f"Decreasing calories by {abs(adjustment):.0f} kcal/day to minimize fat gain."
                )

    def reset(self):
        """Reset controller state (call when starting new plan)"""
        self.state = ControllerState()


class VolumePIDController:
    """
    PID controller for training volume adjustments based on adherence and fatigue.

    Manages:
    - Progressive overload (gradual volume increase)
    - Deload detection (fatigue accumulation)
    - Adherence-based scaling (reduce volume if compliance is low)
    """

    def __init__(self):
        # Conservative PID parameters for volume
        self.params = PIDParameters(
            Kp=10.0,  # 10 sets per 10% adherence deviation
            Ki=3.0,  # 3 sets per accumulated adherence error
            Kd=5.0,  # 5 sets damping on rapid changes
            min_output=-20.0,  # Max decrease per adjustment
            max_output=10.0,  # Max increase per adjustment (asymmetric for safety)
            integral_windup_limit=2.0,
        )
        self.state = ControllerState()

    def calculate_adjustment(
        self,
        current_volume_per_week: int,
        target_adherence: float,
        actual_adherence: float,
        weeks_since_deload: int,
        confidence: float,
    ) -> VolumeAdjustment:
        """
        Calculate recommended volume adjustment.

        Args:
            current_volume_per_week: Current total weekly volume (sets across all muscles)
            target_adherence: Target adherence rate (typically 0.85-0.9)
            actual_adherence: Actual adherence rate (0.0-1.0)
            weeks_since_deload: Weeks since last deload
            confidence: Data quality confidence

        Returns:
            VolumeAdjustment with recommendation
        """
        # Check if deload is needed (every 4-6 weeks)
        if weeks_since_deload >= 5:
            return VolumeAdjustment(
                adjustment_type=AdjustmentType.DELOAD,
                current_volume_per_week=current_volume_per_week,
                recommended_volume_per_week=int(current_volume_per_week * 0.5),
                adjustment_amount=int(-current_volume_per_week * 0.5),
                adjustment_percentage=-50.0,
                rationale=(
                    f"Planned deload after {weeks_since_deload} weeks of progressive overload. "
                    "Reducing volume by 50% to dissipate fatigue and reveal fitness."
                ),
                confidence=1.0,  # High confidence in planned deloads
            )

        # Calculate adherence error
        adherence_error = target_adherence - actual_adherence

        # PID calculation
        P = self.params.Kp * adherence_error
        self.state.integral_accumulator += adherence_error
        self.state.integral_accumulator = max(
            min(self.state.integral_accumulator, self.params.integral_windup_limit),
            -self.params.integral_windup_limit,
        )
        I = self.params.Ki * self.state.integral_accumulator
        derivative = adherence_error - self.state.previous_error
        D = self.params.Kd * derivative

        raw_adjustment = P + I + D
        scaled_adjustment = raw_adjustment * confidence

        # Clamp
        clamped_adjustment = max(
            min(scaled_adjustment, self.params.max_output), self.params.min_output
        )

        # Round to nearest 2 sets
        final_adjustment = round(clamped_adjustment / 2) * 2

        # Progressive overload: If adherence is high, allow small increases
        if actual_adherence >= 0.85 and weeks_since_deload < 4:
            # Add 1-2 sets per week as progressive overload
            final_adjustment = max(final_adjustment, 2)

        recommended_volume = current_volume_per_week + final_adjustment
        recommended_volume = max(recommended_volume, 30)  # Minimum volume floor

        # Determine adjustment type
        if abs(final_adjustment) < 2:
            adjustment_type = AdjustmentType.MAINTAIN
        elif final_adjustment > 0:
            adjustment_type = AdjustmentType.VOLUME_INCREASE
        else:
            adjustment_type = AdjustmentType.VOLUME_DECREASE

        # Generate rationale
        rationale = self._generate_volume_rationale(
            adherence_error, final_adjustment, actual_adherence, weeks_since_deload
        )

        # Update state
        self.state.previous_error = adherence_error
        self.state.last_adjustment = final_adjustment

        return VolumeAdjustment(
            adjustment_type=adjustment_type,
            current_volume_per_week=current_volume_per_week,
            recommended_volume_per_week=int(recommended_volume),
            adjustment_amount=int(final_adjustment),
            adjustment_percentage=(final_adjustment / current_volume_per_week) * 100,
            rationale=rationale,
            confidence=confidence,
        )

    def _generate_volume_rationale(
        self,
        adherence_error: float,
        adjustment: int,
        actual_adherence: float,
        weeks_since_deload: int,
    ) -> str:
        """Generate human-readable rationale"""
        if adjustment == 0:
            return (
                f"Training adherence is good ({actual_adherence:.1%}). "
                "Maintaining current volume."
            )

        if adjustment > 0:
            if actual_adherence >= 0.85:
                return (
                    f"High adherence ({actual_adherence:.1%}) and week {weeks_since_deload} of mesocycle. "
                    f"Increasing volume by {adjustment} sets/week for progressive overload."
                )
            else:
                return (
                    f"Adherence has improved to {actual_adherence:.1%}. "
                    f"Cautiously increasing volume by {adjustment} sets/week."
                )
        else:
            return (
                f"Adherence is low ({actual_adherence:.1%}). "
                f"Reducing volume by {abs(adjustment)} sets/week to improve compliance. "
                "Quality over quantity."
            )

    def reset(self):
        """Reset controller state"""
        self.state = ControllerState()


class AdaptiveController:
    """
    Main controller orchestrating calorie and volume adjustments.

    Uses both CaloriePIDController and VolumePIDController to
    generate comprehensive adjustment recommendations.
    """

    def __init__(self):
        self.calorie_controller = CaloriePIDController()
        self.volume_controller = VolumePIDController()

    def calculate_adjustments(
        self,
        # Calorie adjustment inputs
        target_rate_kg_per_week: float,
        actual_rate_kg_per_week: float,
        current_calories: int,
        # Volume adjustment inputs
        current_volume_per_week: int,
        target_adherence: float,
        actual_adherence: float,
        weeks_since_deload: int,
        # Common inputs
        weeks_elapsed: float,
        overall_confidence: float,
    ) -> Tuple[CalorieAdjustment, VolumeAdjustment]:
        """
        Calculate both calorie and volume adjustments.

        Returns:
            (CalorieAdjustment, VolumeAdjustment)
        """
        calorie_adj = self.calorie_controller.calculate_adjustment(
            target_rate_kg_per_week=target_rate_kg_per_week,
            actual_rate_kg_per_week=actual_rate_kg_per_week,
            current_calories=current_calories,
            weeks_elapsed=weeks_elapsed,
            confidence=overall_confidence,
        )

        volume_adj = self.volume_controller.calculate_adjustment(
            current_volume_per_week=current_volume_per_week,
            target_adherence=target_adherence,
            actual_adherence=actual_adherence,
            weeks_since_deload=weeks_since_deload,
            confidence=overall_confidence,
        )

        return calorie_adj, volume_adj

    def reset_all(self):
        """Reset all controllers (call when starting new plan)"""
        self.calorie_controller.reset()
        self.volume_controller.reset()


def generate_adjustment_summary(
    calorie_adj: CalorieAdjustment, volume_adj: VolumeAdjustment
) -> Dict[str, any]:
    """Generate human-readable summary of adjustments"""
    summary = {
        "calories": {
            "action": calorie_adj.adjustment_type.value,
            "current": calorie_adj.current_calories,
            "recommended": calorie_adj.recommended_calories,
            "change": f"{calorie_adj.adjustment_percentage:+.1f}%",
            "rationale": calorie_adj.rationale,
        },
        "volume": {
            "action": volume_adj.adjustment_type.value,
            "current": volume_adj.current_volume_per_week,
            "recommended": volume_adj.recommended_volume_per_week,
            "change": f"{volume_adj.adjustment_percentage:+.1f}%",
            "rationale": volume_adj.rationale,
        },
        "overall_recommendation": _generate_overall_recommendation(calorie_adj, volume_adj),
    }

    return summary


def _generate_overall_recommendation(
    calorie_adj: CalorieAdjustment, volume_adj: VolumeAdjustment
) -> str:
    """Generate high-level recommendation"""
    if volume_adj.adjustment_type == AdjustmentType.DELOAD:
        return (
            "Time for a deload week. Reduce training volume by 50% while maintaining intensity. "
            f"Also {'increase' if calorie_adj.adjustment_amount > 0 else 'decrease'} "
            f"calories to {calorie_adj.recommended_calories} kcal/day."
        )

    if (
        calorie_adj.adjustment_type == AdjustmentType.MAINTAIN
        and volume_adj.adjustment_type == AdjustmentType.MAINTAIN
    ):
        return (
            "Progress is on track. Continue current plan with no changes. "
            "Keep monitoring adherence and body weight."
        )

    changes = []
    if calorie_adj.adjustment_type != AdjustmentType.MAINTAIN:
        changes.append(
            f"{'Increase' if calorie_adj.adjustment_amount > 0 else 'Decrease'} "
            f"calories to {calorie_adj.recommended_calories} kcal/day"
        )

    if volume_adj.adjustment_type != AdjustmentType.MAINTAIN:
        changes.append(
            f"{'Increase' if volume_adj.adjustment_amount > 0 else 'Decrease'} "
            f"training volume to {volume_adj.recommended_volume_per_week} sets/week"
        )

    return "Adjustments needed: " + "; ".join(changes) + "."
