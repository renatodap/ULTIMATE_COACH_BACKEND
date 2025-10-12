"""
Macro Calculator Service

Scientific calculation of BMR, TDEE, and macro targets using:
- Mifflin-St Jeor equation for BMR (most accurate for general population)
- Standard activity multipliers for TDEE
- Goal-based calorie adjustments
- Evidence-based protein recommendations (1.6-2.2g/kg)

References:
- Mifflin et al. (1990) - BMR equation
- ISSN Position Stand (2017) - Protein recommendations
- Academy of Nutrition and Dietetics - TDEE multipliers
"""

import structlog
from typing import Dict, Literal
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

# ============================================================================
# CONSTANTS
# ============================================================================

# Activity level multipliers for TDEE calculation
# Source: Academy of Nutrition and Dietetics
ACTIVITY_MULTIPLIERS = {
    'sedentary': 1.2,  # Desk job, little to no exercise
    'lightly_active': 1.375,  # Light exercise 1-3 days/week
    'moderately_active': 1.55,  # Moderate exercise 3-5 days/week
    'very_active': 1.725,  # Hard exercise 6-7 days/week
    'extremely_active': 1.9,  # Hard exercise 2x/day or physical job
}

# Protein multipliers by goal (g/kg bodyweight)
# Source: ISSN Position Stand on Protein 2017
PROTEIN_MULTIPLIERS = {
    'lose_weight': 2.2,  # Higher protein for muscle preservation in deficit
    'build_muscle': 2.0,  # Optimal for hypertrophy
    'improve_performance': 1.8,  # Balanced for endurance/performance
    'maintain': 1.6,  # Maintenance minimum
}

# Calorie adjustments by goal
CALORIE_ADJUSTMENTS = {
    'lose_weight': -500,  # ~1lb/week loss (safe, sustainable)
    'build_muscle': +250,  # ~0.5lb/week gain (minimize fat gain)
    'improve_performance': +100,  # Slight surplus for performance
    'maintain': 0,  # Maintain current weight
}

# Fat percentage of total calories (recommended: 25-30%)
FAT_PERCENTAGE = 0.28

# Safety bounds
MIN_CALORIES = 1200  # Minimum safe intake for most adults
MAX_CALORIES = 4000  # Upper bound for sanity checking
MIN_PROTEIN = 50  # Minimum protein (g)
MAX_PROTEIN = 500  # Upper bound for sanity checking


# ============================================================================
# MODELS
# ============================================================================

class MacroTargets(BaseModel):
    """Complete macro calculation results with explanations."""

    bmr: int = Field(..., description="Basal Metabolic Rate (calories)")
    tdee: int = Field(..., description="Total Daily Energy Expenditure (calories)")
    daily_calories: int = Field(..., description="Daily calorie target")
    daily_protein_g: int = Field(..., description="Daily protein target (grams)")
    daily_carbs_g: int = Field(..., description="Daily carbs target (grams)")
    daily_fat_g: int = Field(..., description="Daily fat target (grams)")

    # Explanations for transparency
    explanation: Dict[str, str] = Field(
        ..., description="Human-readable explanations for each calculation"
    )


# ============================================================================
# BMR CALCULATION
# ============================================================================

def calculate_bmr(
    age: int,
    sex: Literal['male', 'female'],
    height_cm: float,
    weight_kg: float
) -> int:
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.

    This is the most accurate BMR equation for general population.

    Formula:
    - Men: BMR = 10W + 6.25H - 5A + 5
    - Women: BMR = 10W + 6.25H - 5A - 161

    Where:
    - W = weight in kg
    - H = height in cm
    - A = age in years

    Args:
        age: Age in years (13-120)
        sex: Biological sex ('male' or 'female')
        height_cm: Height in centimeters (100-300)
        weight_kg: Weight in kilograms (30-300)

    Returns:
        BMR in calories per day (rounded to nearest calorie)

    Reference:
        Mifflin, M. D., et al. (1990). A new predictive equation for resting
        energy expenditure in healthy individuals. The American journal of
        clinical nutrition, 51(2), 241-247.
    """
    if sex == 'male':
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:  # female
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

    return round(bmr)


# ============================================================================
# MACRO CALCULATION
# ============================================================================

def calculate_targets(
    age: int,
    sex: Literal['male', 'female'],
    height_cm: float,
    current_weight_kg: float,
    goal_weight_kg: float,
    activity_level: str,
    primary_goal: str,
    experience_level: str = 'beginner'
) -> MacroTargets:
    """
    Calculate complete macro targets based on user profile.

    Process:
    1. Calculate BMR (Mifflin-St Jeor equation)
    2. Calculate TDEE (BMR × activity multiplier)
    3. Adjust calories based on goal (deficit/surplus/maintain)
    4. Calculate protein (goal-based multiplier × weight)
    5. Calculate fats (28% of calories)
    6. Calculate carbs (remaining calories)

    Args:
        age: Age in years
        sex: Biological sex ('male' or 'female')
        height_cm: Height in centimeters
        current_weight_kg: Current weight in kilograms
        goal_weight_kg: Goal weight in kilograms
        activity_level: Activity level key (sedentary, lightly_active, etc.)
        primary_goal: Primary goal (lose_weight, build_muscle, maintain, improve_performance)
        experience_level: Fitness experience (beginner, intermediate, advanced) - future use

    Returns:
        MacroTargets object with all calculations and explanations

    Raises:
        ValueError: If invalid inputs provided
    """

    # Validation
    if activity_level not in ACTIVITY_MULTIPLIERS:
        raise ValueError(f"Invalid activity_level: {activity_level}")

    if primary_goal not in CALORIE_ADJUSTMENTS:
        raise ValueError(f"Invalid primary_goal: {primary_goal}")

    # Step 1: Calculate BMR
    bmr = calculate_bmr(age, sex, height_cm, current_weight_kg)

    logger.info(
        "bmr_calculated",
        bmr=bmr,
        age=age,
        sex=sex,
        height_cm=height_cm,
        weight_kg=current_weight_kg
    )

    # Step 2: Calculate TDEE
    activity_multiplier = ACTIVITY_MULTIPLIERS[activity_level]
    tdee = round(bmr * activity_multiplier)

    logger.info(
        "tdee_calculated",
        tdee=tdee,
        bmr=bmr,
        activity_level=activity_level,
        multiplier=activity_multiplier
    )

    # Step 3: Adjust calories based on goal
    calorie_adjustment = CALORIE_ADJUSTMENTS[primary_goal]
    daily_calories = tdee + calorie_adjustment

    # Apply safety bounds
    daily_calories = max(MIN_CALORIES, min(MAX_CALORIES, daily_calories))

    # Step 4: Calculate Protein
    protein_multiplier = PROTEIN_MULTIPLIERS[primary_goal]
    daily_protein_g = round(current_weight_kg * protein_multiplier)

    # Apply safety bounds
    daily_protein_g = max(MIN_PROTEIN, min(MAX_PROTEIN, daily_protein_g))

    # Step 5: Calculate Fats (28% of calories)
    fat_calories = daily_calories * FAT_PERCENTAGE
    daily_fat_g = round(fat_calories / 9)  # 9 calories per gram of fat

    # Step 6: Calculate Carbs (remainder)
    protein_calories = daily_protein_g * 4  # 4 calories per gram
    fat_calories_actual = daily_fat_g * 9
    carb_calories = daily_calories - protein_calories - fat_calories_actual
    daily_carbs_g = round(carb_calories / 4)  # 4 calories per gram of carbs

    # Ensure carbs are non-negative
    daily_carbs_g = max(0, daily_carbs_g)

    logger.info(
        "macros_calculated",
        calories=daily_calories,
        protein=daily_protein_g,
        carbs=daily_carbs_g,
        fats=daily_fat_g,
        primary_goal=primary_goal
    )

    # Build explanation
    weight_diff = abs(current_weight_kg - goal_weight_kg)
    goal_direction = "lose" if goal_weight_kg < current_weight_kg else "gain"

    explanation = {
        'bmr': f'Calculated using Mifflin-St Jeor equation based on your age ({age}), sex ({sex}), height ({height_cm}cm), and weight ({current_weight_kg}kg)',
        'tdee': f'BMR ({bmr} cal) x {activity_multiplier} activity multiplier for {activity_level.replace("_", " ")} lifestyle',
        'calories': f'TDEE ({tdee} cal) {"-" if calorie_adjustment < 0 else "+"} {abs(calorie_adjustment)} cal adjustment for {primary_goal.replace("_", " ")} goal',
        'protein': f'{protein_multiplier}g per kg bodyweight ({current_weight_kg}kg) - optimal for {primary_goal.replace("_", " ")}',
        'fats': f'{int(FAT_PERCENTAGE * 100)}% of calories for hormone health and vitamin absorption',
        'carbs': f'Remaining calories after protein and fats - primary energy source',
        'goal_context': f'To {goal_direction} {weight_diff:.1f}kg, targeting {"deficit" if calorie_adjustment < 0 else "surplus" if calorie_adjustment > 0 else "maintenance"} of {abs(calorie_adjustment)} cal/day'
    }

    return MacroTargets(
        bmr=bmr,
        tdee=tdee,
        daily_calories=daily_calories,
        daily_protein_g=daily_protein_g,
        daily_carbs_g=daily_carbs_g,
        daily_fat_g=daily_fat_g,
        explanation=explanation
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_activity_multiplier(activity_level: str) -> float:
    """Get TDEE multiplier for activity level."""
    return ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)


def get_protein_multiplier(primary_goal: str) -> float:
    """Get protein multiplier (g/kg) for goal."""
    return PROTEIN_MULTIPLIERS.get(primary_goal, 1.6)


def estimate_time_to_goal(
    current_weight_kg: float,
    goal_weight_kg: float,
    daily_calories: int,
    tdee: int
) -> int:
    """
    Estimate weeks to reach goal weight.

    Assumes:
    - 1 lb = 3500 calories
    - 1 kg = 2.20462 lbs
    - Linear weight loss/gain (simplified model)

    Returns:
        Estimated weeks to goal (rounded)
    """
    weight_diff_kg = abs(goal_weight_kg - current_weight_kg)
    weight_diff_lbs = weight_diff_kg * 2.20462

    daily_deficit = abs(tdee - daily_calories)
    weekly_deficit = daily_deficit * 7

    # 3500 cal = 1 lb
    lbs_per_week = weekly_deficit / 3500

    if lbs_per_week == 0:
        return 0

    weeks_to_goal = weight_diff_lbs / lbs_per_week

    return round(weeks_to_goal)
