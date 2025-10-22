"""
TDEE (Total Daily Energy Expenditure) Calculator

Uses ensemble of validated equations to estimate daily calorie needs with
statistical confidence intervals.

Formulas implemented:
- Katch-McArdle (requires body fat %)
- Cunningham (requires lean body mass)
- Mifflin-St Jeor (most validated for general population)
- Revised Harris-Benedict

References:
- Mifflin et al. (1990): "A new predictive equation for resting energy expenditure"
- Katch & McArdle (1996): "Exercise Physiology: Energy, Nutrition, and Human Performance"
- Cunningham (1991): "Body composition as a determinant of energy expenditure"
"""

import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ultimate_ai_consultation.config import settings

logger = logging.getLogger(__name__)


class ActivityFactor(float, Enum):
    """PAL (Physical Activity Level) multipliers for TDEE calculation."""

    SEDENTARY = 1.2  # Little to no exercise
    LIGHTLY_ACTIVE = 1.375  # Light exercise 1-3 days/week
    MODERATELY_ACTIVE = 1.55  # Moderate exercise 3-5 days/week
    VERY_ACTIVE = 1.725  # Hard exercise 6-7 days/week
    EXTRA_ACTIVE = 1.9  # Very hard exercise, physical job, training 2x/day


@dataclass
class TDEEResult:
    """
    TDEE calculation result with confidence intervals.

    Attributes:
        tdee_mean: Mean TDEE estimate (kcal/day)
        tdee_ci_lower: Lower bound of confidence interval
        tdee_ci_upper: Upper bound of confidence interval
        confidence: Statistical confidence (0.0-1.0)
        source_equations: List of equations used
        activity_factor: PAL multiplier applied
        notes: Additional context or warnings
    """

    tdee_mean: int
    tdee_ci_lower: int
    tdee_ci_upper: int
    confidence: float
    source_equations: list[str]
    activity_factor: float
    notes: list[str]


class TDEECalculator:
    """
    Calculate TDEE using ensemble of validated equations.

    Provides statistical confidence intervals based on:
    1. Number of equations available (more = higher confidence)
    2. Agreement between equations (closer = higher confidence)
    3. Data quality (body composition known = higher confidence)
    """

    def __init__(self):
        """Initialize calculator with configuration."""
        self.ci_width = settings.TDEE_CONFIDENCE_INTERVAL  # ±15% by default

    def calculate(
        self,
        age: int,
        sex_at_birth: str,  # "male" or "female"
        weight_kg: float,
        height_cm: float,
        activity_level: ActivityFactor,
        body_fat_percent: Optional[float] = None,
        lean_mass_kg: Optional[float] = None,
    ) -> TDEEResult:
        """
        Calculate TDEE using ensemble approach.

        Args:
            age: Age in years
            sex_at_birth: Biological sex ("male" or "female")
            weight_kg: Body weight in kilograms
            height_cm: Height in centimeters
            activity_level: Physical activity level
            body_fat_percent: Body fat percentage (optional, improves accuracy)
            lean_mass_kg: Lean body mass in kg (optional)

        Returns:
            TDEEResult with mean, confidence intervals, and metadata

        Raises:
            ValueError: If inputs are invalid
        """
        # Validate inputs
        self._validate_inputs(age, sex_at_birth, weight_kg, height_cm, body_fat_percent)

        # Calculate lean mass if not provided but body fat is
        if lean_mass_kg is None and body_fat_percent is not None:
            lean_mass_kg = weight_kg * (1 - body_fat_percent / 100)

        # Calculate RMR (Resting Metabolic Rate) using all applicable equations
        rmr_estimates = []
        equations_used = []
        notes = []

        # 1. Mifflin-St Jeor (most validated, works for everyone)
        rmr_msj = self._mifflin_st_jeor(age, sex_at_birth, weight_kg, height_cm)
        rmr_estimates.append(rmr_msj)
        equations_used.append("Mifflin-St Jeor")

        # 2. Revised Harris-Benedict (good baseline)
        rmr_hb = self._harris_benedict_revised(age, sex_at_birth, weight_kg, height_cm)
        rmr_estimates.append(rmr_hb)
        equations_used.append("Harris-Benedict (Revised)")

        # 3. Katch-McArdle (if we have body composition)
        if lean_mass_kg is not None:
            rmr_km = self._katch_mcardle(lean_mass_kg)
            rmr_estimates.append(rmr_km)
            equations_used.append("Katch-McArdle")
            notes.append(f"Body composition data available (LBM: {lean_mass_kg:.1f} kg)")

        # 4. Cunningham (alternative if we have lean mass)
        if lean_mass_kg is not None:
            rmr_cunningham = self._cunningham(lean_mass_kg)
            rmr_estimates.append(rmr_cunningham)
            equations_used.append("Cunningham")

        # Calculate ensemble statistics
        rmr_mean = sum(rmr_estimates) / len(rmr_estimates)
        rmr_std = self._calculate_std(rmr_estimates, rmr_mean)

        # Apply activity factor to get TDEE
        tdee_mean = round(rmr_mean * activity_level.value)

        # Calculate confidence interval
        # Base CI width from config, adjusted by:
        # 1. Equation agreement (low std = tighter CI)
        # 2. Number of equations (more = higher confidence)
        agreement_factor = min(1.0, rmr_std / rmr_mean) if rmr_mean > 0 else 1.0
        equation_count_bonus = len(equations_used) / 4  # Max 4 equations
        adjusted_ci_width = self.ci_width * agreement_factor * (2 - equation_count_bonus)

        tdee_ci_lower = round(tdee_mean * (1 - adjusted_ci_width))
        tdee_ci_upper = round(tdee_mean * (1 + adjusted_ci_width))

        # Calculate confidence score
        confidence = self._calculate_confidence(
            len(equations_used), agreement_factor, body_fat_percent is not None
        )

        # Add context notes
        if rmr_std > rmr_mean * 0.10:
            notes.append("Equations show moderate disagreement (>10% variance)")
        if body_fat_percent is None:
            notes.append("No body composition data - using population averages")
        if age < 18:
            notes.append("Growing individual - TDEE may be higher than estimated")
        if age > 65:
            notes.append("Older adult - metabolic rate may be lower")

        logger.info(
            f"TDEE calculated: {tdee_mean} kcal/day "
            f"(CI: {tdee_ci_lower}-{tdee_ci_upper}, "
            f"confidence: {confidence:.2f}, "
            f"equations: {len(equations_used)})"
        )

        return TDEEResult(
            tdee_mean=tdee_mean,
            tdee_ci_lower=tdee_ci_lower,
            tdee_ci_upper=tdee_ci_upper,
            confidence=confidence,
            source_equations=equations_used,
            activity_factor=activity_level.value,
            notes=notes,
        )

    def _mifflin_st_jeor(
        self, age: int, sex_at_birth: str, weight_kg: float, height_cm: float
    ) -> float:
        """
        Mifflin-St Jeor equation (1990).

        Most validated equation for general population.
        RMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) + s
        where s = +5 for males, -161 for females
        """
        s = 5 if sex_at_birth.lower() == "male" else -161
        rmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + s
        return rmr

    def _harris_benedict_revised(
        self, age: int, sex_at_birth: str, weight_kg: float, height_cm: float
    ) -> float:
        """
        Revised Harris-Benedict equation (1984).

        Men: RMR = 88.362 + (13.397 × weight_kg) + (4.799 × height_cm) - (5.677 × age)
        Women: RMR = 447.593 + (9.247 × weight_kg) + (3.098 × height_cm) - (4.330 × age)
        """
        if sex_at_birth.lower() == "male":
            rmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
        else:
            rmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
        return rmr

    def _katch_mcardle(self, lean_mass_kg: float) -> float:
        """
        Katch-McArdle equation.

        Most accurate when body composition is known.
        RMR = 370 + (21.6 × lean_mass_kg)
        """
        rmr = 370 + (21.6 * lean_mass_kg)
        return rmr

    def _cunningham(self, lean_mass_kg: float) -> float:
        """
        Cunningham equation (1991).

        Alternative body composition-based equation.
        RMR = 500 + (22 × lean_mass_kg)
        """
        rmr = 500 + (22 * lean_mass_kg)
        return rmr

    def _calculate_std(self, values: list[float], mean: float) -> float:
        """Calculate standard deviation."""
        if len(values) <= 1:
            return 0.0
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance**0.5

    def _calculate_confidence(
        self, num_equations: int, agreement_factor: float, has_body_comp: bool
    ) -> float:
        """
        Calculate statistical confidence in TDEE estimate.

        Factors:
        - Number of equations used (more = better)
        - Agreement between equations (closer = better)
        - Body composition data available (yes = better)

        Returns:
            Confidence score from 0.0 to 1.0
        """
        # Base confidence from equation count (0.5-0.9)
        equation_confidence = 0.5 + (num_equations / 4) * 0.4

        # Agreement bonus (low disagreement = higher confidence)
        agreement_confidence = max(0, 1.0 - agreement_factor)

        # Body composition bonus
        body_comp_bonus = 0.10 if has_body_comp else 0.0

        # Combine factors
        confidence = (equation_confidence * 0.6 + agreement_confidence * 0.3) + body_comp_bonus

        # Cap at 0.95 (never 100% certain)
        return min(0.95, confidence)

    def _validate_inputs(
        self,
        age: int,
        sex_at_birth: str,
        weight_kg: float,
        height_cm: float,
        body_fat_percent: Optional[float],
    ) -> None:
        """Validate input parameters."""
        if not 10 <= age <= 120:
            raise ValueError(f"Age must be between 10 and 120, got {age}")

        if sex_at_birth.lower() not in ["male", "female"]:
            raise ValueError(f"sex_at_birth must be 'male' or 'female', got '{sex_at_birth}'")

        if not 30 <= weight_kg <= 300:
            raise ValueError(f"Weight must be between 30 and 300 kg, got {weight_kg}")

        if not 100 <= height_cm <= 250:
            raise ValueError(f"Height must be between 100 and 250 cm, got {height_cm}")

        if body_fat_percent is not None and not 3 <= body_fat_percent <= 60:
            raise ValueError(
                f"Body fat percent must be between 3 and 60%, got {body_fat_percent}"
            )


# Convenience function
def calculate_tdee(
    age: int,
    sex_at_birth: str,
    weight_kg: float,
    height_cm: float,
    sessions_per_week: int,
    session_duration_minutes: int = 60,
    body_fat_percent: Optional[float] = None,
) -> TDEEResult:
    """
    Calculate TDEE with automatic activity level determination.

    Args:
        age: Age in years
        sex_at_birth: Biological sex
        weight_kg: Weight in kg
        height_cm: Height in cm
        sessions_per_week: Training sessions per week
        session_duration_minutes: Average session length
        body_fat_percent: Body fat % (optional)

    Returns:
        TDEEResult with calculations
    """
    # Determine activity factor from training volume
    weekly_training_minutes = sessions_per_week * session_duration_minutes

    if weekly_training_minutes == 0:
        activity = ActivityFactor.SEDENTARY
    elif weekly_training_minutes < 150:
        activity = ActivityFactor.LIGHTLY_ACTIVE
    elif weekly_training_minutes < 300:
        activity = ActivityFactor.MODERATELY_ACTIVE
    elif weekly_training_minutes < 450:
        activity = ActivityFactor.VERY_ACTIVE
    else:
        activity = ActivityFactor.EXTRA_ACTIVE

    calculator = TDEECalculator()
    return calculator.calculate(
        age=age,
        sex_at_birth=sex_at_birth,
        weight_kg=weight_kg,
        height_cm=height_cm,
        activity_level=activity,
        body_fat_percent=body_fat_percent,
    )
