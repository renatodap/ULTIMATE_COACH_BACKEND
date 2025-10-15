"""
Calorie Calculator Service

Calculates calories burned based on METs (Metabolic Equivalent of Task),
user weight, and activity duration using the standard formula:

Calories = METs × Weight (kg) × Duration (hours)

Based on the Compendium of Physical Activities:
https://sites.google.com/site/compendiumofphysicalactivities/
"""

import structlog
from typing import Dict, Optional, Tuple

logger = structlog.get_logger()

# Comprehensive METs database organized by category
# Format: 'activity_key': (mets_value, description)
METS_DATABASE = {
    # CARDIO - STEADY STATE (3.0-15.0)
    'walking_slow': (2.5, 'Walking, slow pace (2 mph)'),
    'walking_moderate': (3.5, 'Walking, moderate pace (3 mph)'),
    'walking_brisk': (4.5, 'Walking, brisk pace (4 mph)'),
    'walking_very_brisk': (5.0, 'Walking, very brisk (4.5 mph)'),
    'jogging': (7.0, 'Jogging, general'),
    'running_5mph': (8.3, 'Running, 5 mph (12 min/mile)'),
    'running_6mph': (9.8, 'Running, 6 mph (10 min/mile)'),
    'running_7mph': (11.0, 'Running, 7 mph (8.5 min/mile)'),
    'running_8mph': (11.8, 'Running, 8 mph (7.5 min/mile)'),
    'running_10mph': (14.5, 'Running, 10 mph (6 min/mile)'),
    'cycling_leisure': (4.0, 'Cycling, leisure, <10 mph'),
    'cycling_moderate': (8.0, 'Cycling, moderate, 12-14 mph'),
    'cycling_vigorous': (10.0, 'Cycling, vigorous, 14-16 mph'),
    'cycling_racing': (12.0, 'Cycling, racing, 16-19 mph'),
    'swimming_freestyle_slow': (5.8, 'Swimming, freestyle, slow'),
    'swimming_freestyle_fast': (9.8, 'Swimming, freestyle, fast'),
    'swimming_breaststroke': (10.3, 'Swimming, breaststroke'),
    'swimming_backstroke': (9.5, 'Swimming, backstroke'),
    'rowing_moderate': (7.0, 'Rowing, moderate effort'),
    'rowing_vigorous': (8.5, 'Rowing, vigorous effort'),
    'elliptical_moderate': (5.0, 'Elliptical, moderate'),
    'elliptical_vigorous': (8.0, 'Elliptical, vigorous'),
    'stairmaster': (9.0, 'StairMaster/StairClimber'),

    # CARDIO - INTERVAL/HIIT (5.0-18.0)
    'hiit_moderate': (8.0, 'HIIT, moderate intensity'),
    'hiit_vigorous': (12.0, 'HIIT, vigorous intensity'),
    'sprint_intervals': (15.0, 'Sprint intervals'),
    'tabata': (12.5, 'Tabata training'),
    'circuit_training': (8.0, 'Circuit training'),
    'crossfit': (12.0, 'CrossFit'),
    'burpees': (8.0, 'Burpees'),
    'jump_rope_slow': (8.8, 'Jump rope, slow'),
    'jump_rope_moderate': (11.8, 'Jump rope, moderate'),
    'jump_rope_fast': (12.3, 'Jump rope, fast'),
    'jumping_jacks': (7.7, 'Jumping jacks'),
    'mountain_climbers': (8.0, 'Mountain climbers'),

    # STRENGTH TRAINING (3.0-8.0)
    'weight_lifting_light': (3.0, 'Weight lifting, light effort'),
    'weight_lifting_moderate': (5.0, 'Weight lifting, moderate'),
    'weight_lifting_vigorous': (6.0, 'Weight lifting, vigorous'),
    'weight_lifting_power': (6.0, 'Weight lifting, power lifting'),
    'bodyweight_light': (3.5, 'Bodyweight exercises, light'),
    'bodyweight_moderate': (5.5, 'Bodyweight exercises, moderate'),
    'bodyweight_vigorous': (8.0, 'Bodyweight exercises, vigorous'),
    'calisthenics': (3.8, 'Calisthenics, light'),
    'calisthenics_vigorous': (8.0, 'Calisthenics, vigorous'),
    'push_ups': (3.8, 'Push-ups'),
    'pull_ups': (8.0, 'Pull-ups'),
    'squats_bodyweight': (5.5, 'Squats, bodyweight'),
    'squats_weighted': (6.0, 'Squats, weighted'),
    'deadlifts': (6.0, 'Deadlifts'),
    'bench_press': (6.0, 'Bench press'),
    'olympic_lifts': (6.0, 'Olympic lifting (snatch, clean)'),

    # SPORTS (4.0-12.0)
    'basketball_game': (8.0, 'Basketball, game'),
    'basketball_shooting': (4.5, 'Basketball, shooting hoops'),
    'soccer_casual': (7.0, 'Soccer, casual'),
    'soccer_competitive': (10.0, 'Soccer, competitive'),
    'tennis_singles': (8.0, 'Tennis, singles'),
    'tennis_doubles': (6.0, 'Tennis, doubles'),
    'volleyball_casual': (4.0, 'Volleyball, casual'),
    'volleyball_competitive': (8.0, 'Volleyball, competitive'),
    'baseball_softball': (5.0, 'Baseball/Softball'),
    'football_casual': (8.0, 'Football, casual'),
    'football_competitive': (9.0, 'Football, competitive'),
    'rugby': (10.0, 'Rugby'),
    'hockey': (8.0, 'Hockey'),
    'lacrosse': (8.0, 'Lacrosse'),
    'boxing_sparring': (9.0, 'Boxing, sparring'),
    'boxing_punching_bag': (6.0, 'Boxing, punching bag'),
    'martial_arts_moderate': (6.0, 'Martial arts, moderate'),
    'martial_arts_vigorous': (10.3, 'Martial arts, vigorous (judo, karate)'),
    'rock_climbing': (11.0, 'Rock climbing, ascending'),
    'rock_climbing_rappelling': (8.0, 'Rock climbing, rappelling'),

    # FLEXIBILITY (1.5-4.0)
    'yoga_hatha': (2.5, 'Yoga, Hatha'),
    'yoga_vinyasa': (3.0, 'Yoga, Vinyasa/Flow'),
    'yoga_power': (4.0, 'Yoga, Power'),
    'yoga_bikram': (5.0, 'Yoga, Bikram/Hot'),
    'pilates': (3.0, 'Pilates'),
    'stretching_light': (2.3, 'Stretching, light'),
    'stretching_vigorous': (3.8, 'Stretching, vigorous'),
    'tai_chi': (3.0, 'Tai Chi'),
    'mobility_work': (2.5, 'Mobility work'),
    'foam_rolling': (2.0, 'Foam rolling'),

    # RECREATIONAL/OTHER
    'dancing_slow': (3.0, 'Dancing, slow (ballroom)'),
    'dancing_moderate': (4.5, 'Dancing, moderate'),
    'dancing_vigorous': (6.5, 'Dancing, vigorous (Zumba)'),
    'golf_with_cart': (3.5, 'Golf, using cart'),
    'golf_carrying_clubs': (5.5, 'Golf, carrying clubs'),
    'bowling': (3.0, 'Bowling'),
    'frisbee_casual': (3.0, 'Frisbee, casual'),
    'frisbee_ultimate': (8.0, 'Ultimate Frisbee'),
    'hiking_no_load': (6.0, 'Hiking, no load'),
    'hiking_with_load': (7.0, 'Hiking, with 10-20 lb load'),
    'skiing_downhill_moderate': (5.3, 'Skiing, downhill, moderate'),
    'skiing_downhill_vigorous': (8.0, 'Skiing, downhill, vigorous'),
    'skiing_cross_country': (9.0, 'Skiing, cross-country'),
    'snowboarding': (5.3, 'Snowboarding'),
    'skateboarding': (5.0, 'Skateboarding'),
    'roller_skating': (7.0, 'Roller skating'),
    'ice_skating': (7.0, 'Ice skating'),
}

# Category default METs (used as fallback)
CATEGORY_DEFAULT_METS = {
    'cardio_steady_state': 7.0,   # Moderate running
    'cardio_interval': 10.0,      # HIIT
    'strength_training': 5.0,     # Moderate weight training
    'sports': 7.0,                # General sports
    'flexibility': 3.0,           # Yoga/stretching
    'other': 5.0,                 # General moderate activity
}


def lookup_mets(activity_name: str, category: str) -> Tuple[float, str]:
    """
    Look up METs value for an activity.

    Args:
        activity_name: Name of the activity (e.g., "Running", "Yoga")
        category: Activity category (e.g., "cardio_steady_state")

    Returns:
        Tuple of (mets_value, matched_activity_description)
    """
    # Normalize activity name for lookup
    normalized = activity_name.lower().replace(' ', '_').replace('-', '_')

    # Try exact match first
    if normalized in METS_DATABASE:
        mets, description = METS_DATABASE[normalized]
        logger.info(
            "mets_exact_match",
            activity_name=activity_name,
            matched_key=normalized,
            mets=mets
        )
        return mets, description

    # Try partial match (e.g., "running" matches "running_5mph")
    for key, (mets, description) in METS_DATABASE.items():
        if normalized in key or key in normalized:
            logger.info(
                "mets_partial_match",
                activity_name=activity_name,
                matched_key=key,
                mets=mets
            )
            return mets, description

    # Fallback to category default
    default_mets = CATEGORY_DEFAULT_METS.get(category, 5.0)
    logger.warning(
        "mets_fallback_to_category",
        activity_name=activity_name,
        category=category,
        default_mets=default_mets
    )
    return default_mets, f"General {category.replace('_', ' ')}"


def calculate_calories(
    mets: float,
    weight_kg: float,
    duration_minutes: int
) -> int:
    """
    Calculate calories burned using the standard METs formula.

    Formula: Calories = METs × Weight (kg) × Duration (hours)

    Args:
        mets: Metabolic Equivalent of Task value
        weight_kg: User's body weight in kilograms
        duration_minutes: Activity duration in minutes

    Returns:
        Calories burned (rounded to nearest integer)

    Example:
        >>> calculate_calories(mets=8.0, weight_kg=70, duration_minutes=30)
        280  # calories
    """
    if weight_kg <= 0:
        raise ValueError(f"weight_kg must be positive, got {weight_kg}")
    if duration_minutes <= 0:
        raise ValueError(f"duration_minutes must be positive, got {duration_minutes}")
    if mets <= 0:
        raise ValueError(f"mets must be positive, got {mets}")

    # Convert minutes to hours
    duration_hours = duration_minutes / 60.0

    # Calculate calories
    calories = mets * weight_kg * duration_hours

    # Round to nearest integer
    calories_rounded = round(calories)

    logger.info(
        "calories_calculated",
        mets=mets,
        weight_kg=weight_kg,
        duration_minutes=duration_minutes,
        duration_hours=round(duration_hours, 2),
        calories=calories_rounded
    )

    return calories_rounded


def estimate_activity_calories(
    activity_name: str,
    category: str,
    duration_minutes: int,
    weight_kg: float,
    user_provided_mets: Optional[float] = None
) -> Dict[str, any]:
    """
    Estimate calories burned for an activity.

    This is the main entry point for calorie calculation. It:
    1. Looks up METs value (or uses user-provided value)
    2. Calculates calories burned
    3. Returns both for transparency

    Args:
        activity_name: Name of the activity
        category: Activity category
        duration_minutes: Duration in minutes
        weight_kg: User's weight in kg
        user_provided_mets: Optional user-provided METs value (overrides lookup)

    Returns:
        Dict with: {
            'calories': int,
            'mets': float,
            'method': str ('user_provided', 'database', or 'category_default'),
            'matched_activity': str (description of matched activity)
        }
    """
    # Determine METs value
    if user_provided_mets is not None:
        mets = user_provided_mets
        method = 'user_provided'
        matched_activity = f"User-specified METs for {activity_name}"
        logger.info(
            "using_user_provided_mets",
            activity_name=activity_name,
            mets=mets
        )
    else:
        mets, matched_activity = lookup_mets(activity_name, category)
        method = 'database' if activity_name.lower().replace(' ', '_') in METS_DATABASE else 'category_default'

    # Calculate calories
    calories = calculate_calories(mets, weight_kg, duration_minutes)

    return {
        'calories': calories,
        'mets': round(mets, 1),
        'method': method,
        'matched_activity': matched_activity
    }


def get_mets_for_category(category: str) -> float:
    """
    Get default METs value for a category (used for UI estimates).

    Args:
        category: Activity category

    Returns:
        Default METs value for that category
    """
    return CATEGORY_DEFAULT_METS.get(category, 5.0)


def list_activities_by_category(category: str) -> list[Dict[str, any]]:
    """
    List all activities in a category (for UI autocomplete).

    Args:
        category: Activity category

    Returns:
        List of dicts with 'key', 'mets', 'description'
    """
    category_prefix = category.split('_')[0]  # e.g., 'cardio' from 'cardio_steady_state'

    activities = []
    for key, (mets, description) in METS_DATABASE.items():
        if category_prefix in description.lower() or category_prefix in key:
            activities.append({
                'key': key,
                'mets': mets,
                'description': description
            })

    # Sort by METs (low to high)
    activities.sort(key=lambda x: x['mets'])

    return activities
