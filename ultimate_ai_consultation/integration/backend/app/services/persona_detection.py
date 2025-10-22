"""
Persona Detection Service

Detects user persona from consultation data and returns personalized adaptations.

Supports 10 personas:
1. The 9-to-5 Hustler
2. The Busy Parent
3. The College Athlete
4. The Homebody Lifter
5. The Long-Haul Trucker
6. The Elderly Upgrader
7. The Young Biohacker
8. The Consistency Struggler
9. The Social Starter
10. The Medical Referral
"""

import logging
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PersonaDefinition:
    """Definition of a user persona with detection criteria and adaptations."""
    name: str
    keywords: List[str]
    age_range: Tuple[int, int]  # (min, max)
    schedule_pattern: str
    adaptations: Dict[str, Any]


# ============================================================================
# PERSONA DEFINITIONS
# ============================================================================

PERSONAS = {
    "9-to-5 Hustler": PersonaDefinition(
        name="9-to-5 Hustler",
        keywords=[
            "office", "desk job", "sedentary", "work lunch", "takeout",
            "weekend", "sit all day", "corporate", "9-5", "work from office"
        ],
        age_range=(25, 45),
        schedule_pattern="weekday_constrained",
        adaptations={
            "sessions_per_week": 4,
            "session_duration_minutes": 45,
            "exercises_per_session": 6,
            "intensity_target": "RPE 6-8",
            "equipment": ["gym", "dumbbells", "barbell", "machines"],
            "workout_timing": "early_morning_or_evening",
            "weekend_focus": True,
            "office_movement": True,
            "meal_strategy": "takeout_tracking",
            "system_prompt_additions": """
            This user has a demanding desk job with limited weekday time.
            - Prioritize efficient compound movements
            - Include weekend longer sessions if possible
            - Suggest office-friendly movement breaks
            - Make takeout logging easy and non-judgmental
            - Focus on consistency over perfection
            """
        }
    ),

    "Busy Parent": PersonaDefinition(
        name="Busy Parent",
        keywords=[
            "kids", "children", "family", "home gym", "early morning",
            "late night", "no time", "childcare", "parent", "baby", "toddler"
        ],
        age_range=(30, 50),
        schedule_pattern="highly_variable",
        adaptations={
            "sessions_per_week": 3-4,
            "session_duration_minutes": 25,
            "exercises_per_session": 4,
            "intensity_target": "RPE 6-8",
            "equipment": ["home_gym", "dumbbells", "bands", "bodyweight"],
            "workout_timing": "flexible",
            "flexibility_required": True,
            "skip_friendly": True,
            "family_meals": True,
            "system_prompt_additions": """
            This user is a busy parent with unpredictable schedule.
            - Create short 20-30min workouts
            - ALL workouts must be home-friendly
            - Build in flexibility for missed sessions
            - Include "10min express" backup options
            - Meal plans should be kid-friendly
            - Use encouraging, non-guilt language
            - Celebrate ANY activity, even if brief
            """
        }
    ),

    "College Athlete": PersonaDefinition(
        name="College Athlete",
        keywords=[
            "college", "varsity", "team", "practice", "season", "athlete",
            "competition", "campus", "dorm", "student", "ncaa"
        ],
        age_range=(18, 24),
        schedule_pattern="structured_but_variable",
        adaptations={
            "sessions_per_week": 4-5,
            "session_duration_minutes": 60,
            "exercises_per_session": 7,
            "intensity_target": "RPE 7-9",
            "equipment": ["full_gym", "athletic_facilities"],
            "workout_timing": "around_practice",
            "competition_taper": True,
            "travel_adaptation": True,
            "campus_dining": True,
            "system_prompt_additions": """
            This is a competitive athlete with structured training.
            - Program around their sport practice schedule
            - Include competition tapers (reduce volume before games)
            - Add injury prevention and mobility work
            - Account for travel (provide bodyweight alternatives)
            - Nutrition should account for campus dining hall
            - Use performance-focused language
            - Track sport-specific metrics
            """
        }
    ),

    "Homebody Lifter": PersonaDefinition(
        name="Homebody Lifter",
        keywords=[
            "home gym", "remote", "work from home", "basement", "garage",
            "alone", "introverted", "dumbbells", "minimal equipment"
        ],
        age_range=(25, 45),
        schedule_pattern="flexible",
        adaptations={
            "sessions_per_week": 5,
            "session_duration_minutes": 60,
            "exercises_per_session": 7,
            "intensity_target": "RPE 7-9",
            "equipment": ["home_gym", "dumbbells", "barbell", "bench", "rack"],
            "workout_timing": "flexible",
            "meal_prep": True,
            "detailed_tracking": True,
            "system_prompt_additions": """
            This user trains at home with dedicated equipment.
            - Design for home gym setup (no machines)
            - Include detailed progression schemes
            - Provide evidence-based rationale
            - Suggest meal prep strategies
            - Focus on long-term strength building
            - Use technical, precise language
            """
        }
    ),

    "Long-Haul Trucker": PersonaDefinition(
        name="Long-Haul Trucker",
        keywords=[
            "truck", "driver", "road", "travel", "no gym", "truck stop",
            "driving", "highway", "irregular schedule", "on the road"
        ],
        age_range=(35, 60),
        schedule_pattern="irregular",
        adaptations={
            "sessions_per_week": 3,
            "session_duration_minutes": 20,
            "exercises_per_session": 4,
            "intensity_target": "RPE 5-7",
            "equipment": ["bodyweight", "resistance_bands"],
            "workout_timing": "rest_stops",
            "bodyweight_only": True,
            "road_food_guidance": True,
            "system_prompt_additions": """
            This user has irregular schedule and limited gym access.
            - ALL exercises must be bodyweight or resistance bands
            - Workouts should fit in parking lots/rest stops
            - Keep duration short (15-25min)
            - Provide truck-stop meal guidance
            - Focus on health markers (blood pressure, weight)
            - Use simple, encouraging language
            - Avoid any gym-dependent exercises
            """
        }
    ),

    "Elderly Upgrader": PersonaDefinition(
        name="Elderly Upgrader",
        keywords=[
            "retired", "senior", "elderly", "balance", "mobility", "fall",
            "bone density", "arthritis", "medication", "doctor"
        ],
        age_range=(60, 85),
        schedule_pattern="flexible",
        adaptations={
            "sessions_per_week": 3,
            "session_duration_minutes": 35,
            "exercises_per_session": 4,
            "intensity_target": "RPE 4-6",
            "equipment": ["bodyweight", "light_dumbbells", "chair"],
            "workout_timing": "flexible",
            "safety_first": True,
            "balance_focus": True,
            "medical_screening": True,
            "system_prompt_additions": """
            This is an older adult focused on maintaining independence.
            - Safety and proper form are HIGHEST priority
            - Start with VERY manageable volume (2 sets, 10-12 reps)
            - Include balance and mobility work in EVERY session
            - Use chair-assisted exercises where appropriate
            - Emphasize how exercises help daily living
            - Progression should be slow (2-3 week blocks)
            - Use encouraging, respectful, non-intimidating language
            - Avoid any "beast mode" or aggressive terminology
            - Include explicit rest days
            """
        }
    ),

    "Young Biohacker": PersonaDefinition(
        name="Young Biohacker",
        keywords=[
            "optimize", "data", "metrics", "biohack", "tracking", "wearable",
            "science", "study", "research", "performance", "recovery"
        ],
        age_range=(22, 35),
        schedule_pattern="flexible",
        adaptations={
            "sessions_per_week": 6,
            "session_duration_minutes": 75,
            "exercises_per_session": 9,
            "intensity_target": "RPE 7-9",
            "equipment": ["full_gym", "advanced_equipment"],
            "workout_timing": "optimized",
            "detailed_metrics": True,
            "scientific_explanations": True,
            "periodization": True,
            "system_prompt_additions": """
            This is an advanced, data-driven trainee who values science.
            - Use scientific terminology and cite studies where relevant
            - Provide detailed metrics (volume, intensity, frequency)
            - Include periodization rationale (why deloads, why this split)
            - Offer optional advanced techniques (drop sets, tempo work)
            - Explain adaptations at cellular/physiological level
            - Track volume landmarks and 1RM estimates
            - Assume high training IQ - don't oversimplify
            """
        }
    ),

    "Consistency Struggler": PersonaDefinition(
        name="Consistency Struggler",
        keywords=[
            "off and on", "restart", "again", "guilt", "failed", "anxiety",
            "stress eating", "emotional", "ups and downs", "inconsistent"
        ],
        age_range=(25, 50),
        schedule_pattern="variable",
        adaptations={
            "sessions_per_week": 3,
            "session_duration_minutes": 35,
            "exercises_per_session": 5,
            "intensity_target": "RPE 5-7",
            "equipment": ["gym", "home_gym", "bodyweight"],
            "workout_timing": "flexible",
            "mental_health_check_ins": True,
            "non_judgmental": True,
            "small_wins": True,
            "system_prompt_additions": """
            This user struggles with consistency and emotional eating.
            - Use ONLY positive, non-judgmental language
            - Never use guilt or shame
            - Celebrate ANY activity, no matter how small
            - Include mental health check-ins in messages
            - When user misses workouts, respond with understanding
            - Focus on "progress not perfection"
            - Provide sentiment-driven nudges (not pressure)
            - Make it easy to restart without feeling behind
            """
        }
    ),

    "Social Starter": PersonaDefinition(
        name="Social Starter",
        keywords=[
            "friends", "group", "social", "together", "accountability",
            "challenge", "share", "wedding", "event", "fun"
        ],
        age_range=(24, 35),
        schedule_pattern="flexible",
        adaptations={
            "sessions_per_week": 4,
            "session_duration_minutes": 50,
            "exercises_per_session": 6,
            "intensity_target": "RPE 6-8",
            "equipment": ["gym", "group_classes"],
            "workout_timing": "social_hours",
            "gamification": True,
            "social_features": True,
            "celebration": True,
            "system_prompt_additions": """
            This user is motivated by social interaction and external accountability.
            - Celebrate wins enthusiastically
            - Suggest group-friendly workouts
            - Use positive, energetic language
            - Track streaks and milestones
            - Make progress shareable
            - Include motivational language
            - Focus on fun and enjoyment
            """
        }
    ),

    "Medical Referral": PersonaDefinition(
        name="Medical Referral",
        keywords=[
            "doctor", "pre-diabetes", "diabetes", "blood pressure", "cholesterol",
            "medical", "health", "prescribed", "condition", "labs"
        ],
        age_range=(40, 70),
        schedule_pattern="flexible",
        adaptations={
            "sessions_per_week": 3,
            "session_duration_minutes": 30,
            "exercises_per_session": 4,
            "intensity_target": "RPE 4-6",
            "equipment": ["gym", "home_gym", "bodyweight"],
            "workout_timing": "flexible",
            "medical_safety": True,
            "phase_in_progression": True,
            "food_education": True,
            "system_prompt_additions": """
            This user was referred by a doctor for lifestyle changes.
            - Safety is HIGHEST priority
            - Start VERY gradually (phase-in over 4 weeks)
            - Avoid any "gym bro" culture or intimidating language
            - Provide food education (not just tracking)
            - Explain why each exercise helps their health goals
            - Check for contraindications (heart rate, blood pressure)
            - Use supportive, educational tone
            - Focus on health markers, not aesthetics
            """
        }
    )
}


# ============================================================================
# PERSONA DETECTION
# ============================================================================

def detect_persona(consultation_data: Dict[str, Any]) -> Tuple[str, float]:
    """
    Detect user persona from consultation data.

    Args:
        consultation_data: Dict containing user's consultation answers
            Expected keys: age, goals, training_experience, schedule, equipment, etc.

    Returns:
        Tuple of (persona_name, confidence_score)
    """

    scores = {}

    for persona_name, persona_def in PERSONAS.items():
        score = 0

        # Check age range (heavy weight)
        age = consultation_data.get("age", 30)
        min_age, max_age = persona_def.age_range
        if min_age <= age <= max_age:
            score += 5  # Age is a strong signal
        elif abs(age - min_age) <= 5 or abs(age - max_age) <= 5:
            score += 2  # Close to age range

        # Check keywords in all text responses
        text_to_search = " ".join([
            str(v).lower() for v in consultation_data.values()
            if isinstance(v, str)
        ])

        for keyword in persona_def.keywords:
            if keyword.lower() in text_to_search:
                score += 1

        # Special checks for specific personas
        if persona_name == "Elderly Upgrader":
            if age >= 65:
                score += 5
            if any(word in text_to_search for word in ["balance", "fall", "medication"]):
                score += 3

        elif persona_name == "Busy Parent":
            if any(word in text_to_search for word in ["kid", "children", "family"]):
                score += 4
            if "home gym" in text_to_search or "no time" in text_to_search:
                score += 2

        elif persona_name == "Medical Referral":
            if any(word in text_to_search for word in ["doctor", "diabetes", "blood pressure"]):
                score += 5

        elif persona_name == "College Athlete":
            if 18 <= age <= 24 and any(word in text_to_search for word in ["college", "varsity", "team"]):
                score += 6

        scores[persona_name] = score

    # Get best match
    best_persona = max(scores, key=scores.get)
    max_score = scores[best_persona]

    # Calculate confidence (normalize to 0-1)
    confidence = min(max_score / 15, 1.0)  # 15 points = 100% confidence

    logger.info(f"Detected persona: {best_persona} (confidence: {confidence:.2f})")
    logger.debug(f"All scores: {scores}")

    return best_persona, confidence


# ============================================================================
# ADAPTATION RETRIEVAL
# ============================================================================

def get_persona_adaptations(persona_type: str) -> Dict[str, Any]:
    """
    Get program adaptations for detected persona.

    Args:
        persona_type: Name of detected persona

    Returns:
        Dict of adaptations for program generation
    """

    if persona_type not in PERSONAS:
        logger.warning(f"Unknown persona: {persona_type}, using default")
        persona_type = "9-to-5 Hustler"  # Default fallback

    return PERSONAS[persona_type].adaptations


# ============================================================================
# ADAPTATION LIST EXTRACTION
# ============================================================================

def get_adaptation_flags(persona_type: str) -> List[str]:
    """
    Get list of adaptation flags for storage in user_profiles_extended.

    Args:
        persona_type: Name of detected persona

    Returns:
        List of string flags (e.g., ['flexible_schedule', 'home_gym', 'short_workouts'])
    """

    if persona_type not in PERSONAS:
        return []

    adaptations = PERSONAS[persona_type].adaptations
    flags = []

    # Extract boolean flags
    if adaptations.get("flexibility_required"):
        flags.append("flexible_schedule")
    if adaptations.get("skip_friendly"):
        flags.append("skip_friendly")
    if adaptations.get("bodyweight_only"):
        flags.append("bodyweight_only")
    if adaptations.get("safety_first"):
        flags.append("safety_first")
    if adaptations.get("medical_safety"):
        flags.append("medical_safety")
    if adaptations.get("non_judgmental"):
        flags.append("non_judgmental")

    # Extract equipment preferences
    equipment = adaptations.get("equipment", [])
    if "home_gym" in equipment or "bodyweight" in equipment:
        flags.append("home_gym")
    if "full_gym" in equipment:
        flags.append("gym_access")

    # Extract meal strategies
    if adaptations.get("meal_strategy") == "takeout_tracking":
        flags.append("takeout_tracking")
    if adaptations.get("family_meals"):
        flags.append("family_meals")
    if adaptations.get("campus_dining"):
        flags.append("campus_dining")
    if adaptations.get("road_food_guidance"):
        flags.append("road_food")
    if adaptations.get("meal_prep"):
        flags.append("meal_prep")

    # Extract training preferences
    if adaptations.get("session_duration_minutes", 60) <= 30:
        flags.append("short_workouts")
    if adaptations.get("competition_taper"):
        flags.append("competition_taper")
    if adaptations.get("detailed_tracking"):
        flags.append("detailed_tracking")

    return flags


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Busy Parent
    example_consultation = {
        "age": 38,
        "goals": "Get back in shape after having kids",
        "training_experience": "Used to train before kids, now very limited time",
        "schedule": "Early morning or late night only, very unpredictable",
        "equipment": "Have dumbbells at home",
        "dietary_notes": "Cook for family, need kid-friendly meals"
    }

    persona, confidence = detect_persona(example_consultation)
    print(f"Detected: {persona} ({confidence:.0%} confidence)")

    adaptations = get_persona_adaptations(persona)
    print(f"Adaptations: {adaptations}")

    flags = get_adaptation_flags(persona)
    print(f"Flags: {flags}")
