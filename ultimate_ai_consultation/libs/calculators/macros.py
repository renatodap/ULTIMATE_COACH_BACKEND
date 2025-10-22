"""
Macro Calculator - Protein, Carbs, Fat distribution

Evidence-based macro calculations with goal-specific adjustments.

References:
- Helms et al. (2014): "Evidence-based recommendations for natural bodybuilding contest preparation"
- Phillips & Van Loon (2011): "Dietary protein for athletes"
- Morton et al. (2018): "A systematic review, meta-analysis and meta-regression of protein intake"
- Aragon et al. (2017): "International society of sports nutrition position stand: diets and body composition"
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

from ultimate_ai_consultation.config import settings

logger = logging.getLogger(__name__)


class Goal(str, Enum):
    """Primary fitness goals."""

    FAT_LOSS = "fat_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"
    RECOMP = "recomp"  # Simultaneous fat loss + muscle gain (advanced)
    PERFORMANCE = "performance"  # Sport-specific


@dataclass
class MacroTargets:
    """
    Macro nutrient targets with flexibility ranges.

    All values in grams per day unless specified.
    """

    # Daily targets
    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int

    # Flexibility ranges (±5% by default)
    protein_min: int
    protein_max: int
    carbs_min: int
    carbs_max: int
    fat_min: int
    fat_max: int

    # Per kg bodyweight (for reference)
    protein_per_kg: float
    carbs_per_kg: float
    fat_per_kg: float

    # Rationale
    goal: str
    rationale: list[str]

    # Meal distribution suggestions
    meals_per_day: int
    protein_per_meal_g: int
    pre_workout_carbs_g: Optional[int] = None
    post_workout_carbs_g: Optional[int] = None


class MacroCalculator:
    """
    Calculate macro distribution based on goal, training, and individual factors.

    Priority hierarchy:
    1. Protein (non-negotiable minimum for goal)
    2. Fat (hormonal floor, never below 0.6 g/kg)
    3. Carbs (fill remaining calories, periodize around training)
    """

    def __init__(self):
        """Initialize calculator with configuration."""
        self.flexibility_pct = settings.MACRO_FLEXIBILITY_PERCENT / 100  # Convert to decimal

    def calculate(
        self,
        tdee: int,
        goal: Goal,
        weight_kg: float,
        body_fat_percent: Optional[float],
        training_sessions_per_week: int,
        training_intensity: str = "moderate",  # "light", "moderate", "high"
        age: int = 30,
        sex_at_birth: str = "male",
    ) -> MacroTargets:
        """
        Calculate macro targets for given parameters.

        Args:
            tdee: Total daily energy expenditure (kcal)
            goal: Primary fitness goal
            weight_kg: Current body weight (kg)
            body_fat_percent: Body fat % (optional, improves accuracy)
            training_sessions_per_week: Training frequency
            training_intensity: Training intensity level
            age: Age in years
            sex_at_birth: Biological sex

        Returns:
            MacroTargets with complete macro distribution

        Raises:
            ValueError: If parameters are invalid
        """
        self._validate_inputs(tdee, weight_kg, body_fat_percent, training_sessions_per_week)

        # Calculate lean body mass (estimate if BF% not available)
        lean_mass_kg = self._estimate_lean_mass(weight_kg, body_fat_percent, sex_at_birth)

        # Determine calorie target based on goal
        calorie_target, calorie_rationale = self._calculate_calorie_target(tdee, goal, body_fat_percent)

        # Calculate protein (priority #1)
        protein_g, protein_rationale = self._calculate_protein(
            goal=goal,
            weight_kg=weight_kg,
            lean_mass_kg=lean_mass_kg,
            training_sessions_per_week=training_sessions_per_week,
            calorie_deficit_pct=((tdee - calorie_target) / tdee) if calorie_target < tdee else 0,
            age=age,
        )

        # Calculate fat (priority #2 - hormonal floor)
        fat_g, fat_rationale = self._calculate_fat(
            weight_kg=weight_kg, goal=goal, sex_at_birth=sex_at_birth
        )

        # Calculate carbs (priority #3 - fill remaining)
        carbs_g, carbs_rationale = self._calculate_carbs(
            calorie_target=calorie_target,
            protein_g=protein_g,
            fat_g=fat_g,
            training_sessions_per_week=training_sessions_per_week,
            training_intensity=training_intensity,
        )

        # Verify calorie math (4 kcal/g protein, 4 kcal/g carbs, 9 kcal/g fat)
        calculated_calories = (protein_g * 4) + (carbs_g * 4) + (fat_g * 9)
        if abs(calculated_calories - calorie_target) > calorie_target * 0.02:  # Allow 2% variance
            # Adjust carbs to hit exact target
            calorie_diff = calorie_target - calculated_calories
            carbs_adjustment = round(calorie_diff / 4)
            carbs_g += carbs_adjustment
            logger.info(f"Adjusted carbs by {carbs_adjustment}g to hit calorie target exactly")

        # Calculate flexibility ranges
        protein_min = round(protein_g * (1 - self.flexibility_pct))
        protein_max = round(protein_g * (1 + self.flexibility_pct))
        carbs_min = round(carbs_g * (1 - self.flexibility_pct))
        carbs_max = round(carbs_g * (1 + self.flexibility_pct))
        fat_min = round(fat_g * (1 - self.flexibility_pct))
        fat_max = round(fat_g * (1 + self.flexibility_pct))

        # Meal distribution recommendations
        meals_per_day = self._recommend_meal_frequency(goal, training_sessions_per_week)
        protein_per_meal = round(protein_g / meals_per_day)

        # Workout nutrition (if training)
        pre_workout_carbs = None
        post_workout_carbs = None
        if training_sessions_per_week > 0:
            pre_workout_carbs, post_workout_carbs = self._calculate_workout_nutrition(
                carbs_g, training_intensity
            )

        # Compile rationale
        all_rationale = [
            calorie_rationale,
            *protein_rationale,
            *fat_rationale,
            *carbs_rationale,
        ]

        logger.info(
            f"Macros calculated: {calorie_target} kcal = "
            f"{protein_g}P/{carbs_g}C/{fat_g}F "
            f"({protein_g/weight_kg:.1f}g/kg protein)"
        )

        return MacroTargets(
            calories=calorie_target,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            protein_min=protein_min,
            protein_max=protein_max,
            carbs_min=carbs_min,
            carbs_max=carbs_max,
            fat_min=fat_min,
            fat_max=fat_max,
            protein_per_kg=round(protein_g / weight_kg, 2),
            carbs_per_kg=round(carbs_g / weight_kg, 2),
            fat_per_kg=round(fat_g / weight_kg, 2),
            goal=goal.value,
            rationale=all_rationale,
            meals_per_day=meals_per_day,
            protein_per_meal_g=protein_per_meal,
            pre_workout_carbs_g=pre_workout_carbs,
            post_workout_carbs_g=post_workout_carbs,
        )

    def _calculate_calorie_target(
        self, tdee: int, goal: Goal, body_fat_percent: Optional[float]
    ) -> tuple[int, str]:
        """
        Calculate calorie target based on goal.

        Deficit/surplus size depends on:
        - Goal (fat loss vs muscle gain)
        - Body fat % (leaner = smaller deficit tolerated)
        - Rate of change desired
        """
        if goal == Goal.FAT_LOSS:
            # Deficit size: 10-25% based on body fat
            if body_fat_percent is not None:
                if body_fat_percent > 25:
                    deficit_pct = 0.25  # Aggressive deficit OK at higher BF
                elif body_fat_percent > 18:
                    deficit_pct = 0.20  # Moderate deficit
                else:
                    deficit_pct = 0.15  # Conservative deficit when lean
            else:
                deficit_pct = 0.20  # Default moderate

            calories = round(tdee * (1 - deficit_pct))
            rationale = f"Fat loss: {int(deficit_pct*100)}% deficit from TDEE ({tdee} kcal)"

        elif goal == Goal.MUSCLE_GAIN:
            # Surplus: 5-15% based on training age (conservative)
            surplus_pct = 0.10  # Default 10% surplus
            calories = round(tdee * (1 + surplus_pct))
            rationale = f"Muscle gain: {int(surplus_pct*100)}% surplus from TDEE ({tdee} kcal)"

        elif goal == Goal.MAINTENANCE:
            calories = tdee
            rationale = f"Maintenance: at TDEE ({tdee} kcal)"

        elif goal == Goal.RECOMP:
            # At TDEE or slight deficit
            calories = round(tdee * 0.95)
            rationale = f"Recomp: slight deficit (5%) from TDEE ({tdee} kcal)"

        elif goal == Goal.PERFORMANCE:
            # At TDEE or slight surplus
            calories = round(tdee * 1.05)
            rationale = f"Performance: slight surplus (5%) from TDEE ({tdee} kcal)"

        else:
            calories = tdee
            rationale = f"Default: at TDEE ({tdee} kcal)"

        return calories, rationale

    def _calculate_protein(
        self,
        goal: Goal,
        weight_kg: float,
        lean_mass_kg: float,
        training_sessions_per_week: int,
        calorie_deficit_pct: float,
        age: int,
    ) -> tuple[int, list[str]]:
        """
        Calculate protein target.

        Evidence-based protein targets (g/kg bodyweight):
        - Fat loss: 2.0-2.4 g/kg (higher in deficit to preserve muscle)
        - Muscle gain: 1.6-2.2 g/kg
        - Maintenance: 1.6-2.0 g/kg
        - Older adults: +0.2 g/kg (sarcopenia prevention)
        """
        rationale = []

        # Base protein target
        if goal == Goal.FAT_LOSS:
            # Higher protein in deficit (muscle sparing)
            if calorie_deficit_pct > 0.20:
                protein_per_kg = 2.3  # Aggressive deficit
                rationale.append("High protein (2.3g/kg) for muscle preservation in deficit")
            else:
                protein_per_kg = 2.0
                rationale.append("Moderate-high protein (2.0g/kg) for fat loss")

        elif goal == Goal.MUSCLE_GAIN:
            protein_per_kg = 1.8  # Sufficient for muscle protein synthesis
            rationale.append("Protein at 1.8g/kg for muscle growth (Morton et al., 2018)")

        elif goal == Goal.RECOMP:
            protein_per_kg = 2.2  # Higher for simultaneous goals
            rationale.append("High protein (2.2g/kg) for recomposition")

        elif goal == Goal.PERFORMANCE:
            protein_per_kg = 1.6  # Adequate for performance
            rationale.append("Protein at 1.6g/kg for performance (sufficient for recovery)")

        else:  # MAINTENANCE
            protein_per_kg = 1.8
            rationale.append("Protein at 1.8g/kg for maintenance")

        # Age adjustment (older adults need more)
        if age >= 65:
            protein_per_kg += 0.2
            rationale.append("Age 65+: +0.2g/kg protein for sarcopenia prevention")
        elif age >= 50:
            protein_per_kg += 0.1
            rationale.append("Age 50+: +0.1g/kg protein for muscle maintenance")

        # Training volume adjustment (minimal - protein needs plateau)
        if training_sessions_per_week >= 6:
            protein_per_kg += 0.1
            rationale.append("High training volume: +0.1g/kg protein")

        # Calculate total protein
        protein_g = round(weight_kg * protein_per_kg)

        # Safety bounds
        min_protein = round(weight_kg * settings.MIN_PROTEIN_G_PER_KG)
        max_protein = round(weight_kg * settings.MAX_PROTEIN_G_PER_KG)

        if protein_g < min_protein:
            protein_g = min_protein
            rationale.append(f"Increased to minimum {settings.MIN_PROTEIN_G_PER_KG}g/kg")
        elif protein_g > max_protein:
            protein_g = max_protein
            rationale.append(f"Capped at maximum {settings.MAX_PROTEIN_G_PER_KG}g/kg")

        return protein_g, rationale

    def _calculate_fat(
        self, weight_kg: float, goal: Goal, sex_at_birth: str
    ) -> tuple[int, list[str]]:
        """
        Calculate fat target.

        Minimum: 0.6 g/kg (hormonal health floor)
        Typical: 0.8-1.2 g/kg
        Higher fat for: women, low-carb preference, older adults
        """
        rationale = []

        # Base fat target
        if goal == Goal.FAT_LOSS:
            fat_per_kg = 0.8  # Moderate fat
            rationale.append("Moderate fat (0.8g/kg) to support hormones during deficit")
        elif goal == Goal.MUSCLE_GAIN:
            fat_per_kg = 0.9  # Slightly higher
            rationale.append("Fat at 0.9g/kg (energy-dense for surplus)")
        else:
            fat_per_kg = 1.0  # Default
            rationale.append("Fat at 1.0g/kg for general health")

        # Sex adjustment (women need slightly higher fat)
        if sex_at_birth.lower() == "female":
            fat_per_kg += 0.2
            rationale.append("Female: +0.2g/kg fat for hormonal health")

        # Calculate total fat
        fat_g = round(weight_kg * fat_per_kg)

        # Safety floor (hormonal health)
        min_fat = round(weight_kg * settings.MIN_FAT_G_PER_KG)
        if fat_g < min_fat:
            fat_g = min_fat
            rationale.append(f"Increased to hormonal floor ({settings.MIN_FAT_G_PER_KG}g/kg)")

        return fat_g, rationale

    def _calculate_carbs(
        self,
        calorie_target: int,
        protein_g: int,
        fat_g: int,
        training_sessions_per_week: int,
        training_intensity: str,
    ) -> tuple[int, list[str]]:
        """
        Calculate carbs from remaining calories after protein and fat.

        Carbs are most flexible macro - periodize around training.
        """
        rationale = []

        # Calculate remaining calories
        protein_calories = protein_g * 4
        fat_calories = fat_g * 9
        remaining_calories = calorie_target - protein_calories - fat_calories

        if remaining_calories < 0:
            raise ValueError(
                f"Protein + fat exceed calorie target! "
                f"P: {protein_calories} kcal, F: {fat_calories} kcal, Target: {calorie_target} kcal"
            )

        # Convert to carbs (4 kcal/g)
        carbs_g = round(remaining_calories / 4)

        # Validate carb target makes sense for training
        carbs_per_kg = carbs_g / (protein_g / 1.8)  # Rough weight estimate
        if training_sessions_per_week >= 4 and carbs_per_kg < 2.0:
            rationale.append(
                "⚠️ Low carbs for training volume - consider reducing protein or fat"
            )
        elif training_sessions_per_week == 0 and carbs_per_kg > 4.0:
            rationale.append("High carbs with no training - consider increasing activity")
        else:
            rationale.append(f"Carbs fill remaining calories ({carbs_g}g = {remaining_calories} kcal)")

        return carbs_g, rationale

    def _recommend_meal_frequency(self, goal: Goal, training_sessions_per_week: int) -> int:
        """
        Recommend meal frequency based on goal and training.

        Evidence: 3-6 meals/day, protein every 3-5 hours for MPS.
        """
        if goal == Goal.MUSCLE_GAIN:
            return 4  # More frequent for anabolism
        elif goal == Goal.FAT_LOSS:
            return 3  # Less frequent (personal preference, no metabolic advantage)
        elif training_sessions_per_week >= 5:
            return 4  # More meals for higher training volume
        else:
            return 3  # Default

    def _calculate_workout_nutrition(
        self, total_carbs_g: int, training_intensity: str
    ) -> tuple[int, int]:
        """
        Calculate pre/post workout carb targets.

        Pre-workout: 15-20% of daily carbs (1-2 hours before)
        Post-workout: 25-35% of daily carbs (within 2 hours after)
        """
        if training_intensity == "high":
            pre_workout_pct = 0.20
            post_workout_pct = 0.35
        elif training_intensity == "moderate":
            pre_workout_pct = 0.15
            post_workout_pct = 0.30
        else:  # light
            pre_workout_pct = 0.10
            post_workout_pct = 0.25

        pre_workout_carbs = round(total_carbs_g * pre_workout_pct)
        post_workout_carbs = round(total_carbs_g * post_workout_pct)

        return pre_workout_carbs, post_workout_carbs

    def _estimate_lean_mass(
        self, weight_kg: float, body_fat_percent: Optional[float], sex_at_birth: str
    ) -> float:
        """
        Estimate lean body mass.

        If body fat % known: LBM = weight * (1 - BF%)
        If unknown: use population averages (male: 85% LBM, female: 75% LBM)
        """
        if body_fat_percent is not None:
            return weight_kg * (1 - body_fat_percent / 100)
        else:
            # Population average estimates
            if sex_at_birth.lower() == "male":
                return weight_kg * 0.85  # ~15% body fat average
            else:
                return weight_kg * 0.75  # ~25% body fat average

    def _validate_inputs(
        self,
        tdee: int,
        weight_kg: float,
        body_fat_percent: Optional[float],
        training_sessions_per_week: int,
    ) -> None:
        """Validate input parameters."""
        if not 1000 <= tdee <= 10000:
            raise ValueError(f"TDEE must be between 1000 and 10000 kcal, got {tdee}")

        if not 30 <= weight_kg <= 300:
            raise ValueError(f"Weight must be between 30 and 300 kg, got {weight_kg}")

        if body_fat_percent is not None and not 3 <= body_fat_percent <= 60:
            raise ValueError(f"Body fat % must be between 3 and 60%, got {body_fat_percent}")

        if not 0 <= training_sessions_per_week <= 14:
            raise ValueError(
                f"Training sessions must be between 0 and 14/week, got {training_sessions_per_week}"
            )
