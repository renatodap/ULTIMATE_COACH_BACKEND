"""
Context Extraction Service

Extracts life context, informal activities, and sentiment from coach chat messages.
This is the KEY service that makes ULTIMATE COACH truly adaptive and context-aware.

Features:
- Detects informal activities ("played tennis", "walked the dog")
- Detects life context (stress, travel, energy, illness, injury)
- Scores sentiment on every message
- Auto-matches activities to templates
- Suggests adaptations based on context
"""

import anthropic
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from supabase import  create_client, Client

logger = logging.getLogger(__name__)

# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)


# ============================================================================
# INFORMAL ACTIVITY EXTRACTION
# ============================================================================

async def extract_informal_activity(
    message: str,
    user_id: str,
    message_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Extract informal physical activities from chat messages.

    Examples:
    - "Played tennis today" → creates tennis activity
    - "Walked the dog for 30 mins" → creates walking activity
    - "Did some yoga this morning" → creates yoga activity

    Args:
        message: User's chat message
        user_id: User UUID
        message_id: Original message UUID (for reference)

    Returns:
        Dict with activity data if detected, None otherwise
    """

    prompt = f"""Analyze this message for informal physical activity:

"{message}"

Determine if the user is describing a physical activity they did (past tense or today).

If YES, extract:
1. activity_type: specific activity name (e.g., "tennis", "walking", "yoga", "basketball")
2. category: map to one of these:
   - cardio_steady_state (walking, jogging, cycling, swimming)
   - cardio_interval (HIIT, sprints, sports)
   - strength_training (weights, calisthenics)
   - sports (tennis, basketball, soccer, etc.)
   - flexibility (yoga, stretching)
   - other
3. intensity: low / moderate / high
4. duration_estimate_minutes: best guess (15-180 range typical)
5. calories_estimate: rough estimate based on intensity and duration
6. should_count_as_workout: true if this was intentional exercise, false if just daily activity
7. confidence: 0.0-1.0 confidence score

If NO activity detected, return: {{"activity_detected": false}}

Return ONLY valid JSON, no explanations."""

    try:
        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        result = json.loads(response.content[0].text)

        if not result.get("activity_detected"):
            return None

        # Only create activity if confidence is reasonable and should count as workout
        if result.get("confidence", 0) < 0.6 or not result.get("should_count_as_workout"):
            return None

        # Map intensity to RPE
        intensity_to_rpe = {
            "low": 4,
            "moderate": 6,
            "high": 8
        }

        # Create activity record
        activity_data = {
            "user_id": user_id,
            "category": result["category"],
            "activity_name": f"{result['activity_type'].title()} (Informal)",
            "start_time": datetime.now().isoformat(),
            "duration_minutes": result["duration_estimate_minutes"],
            "calories_burned": result["calories_estimate"],
            "perceived_exertion": intensity_to_rpe.get(result["intensity"], 6),
            "notes": f"Auto-extracted from chat: {message[:100]}",
            "source": "coach_chat",
            "metrics": {
                "informal_log": True,
                "extraction_confidence": result["confidence"],
                "intensity": result["intensity"],
                "original_message": message
            }
        }

        activity = supabase.table("activities").insert(activity_data).execute()

        # Log to context table
        supabase.table("user_context_log").insert({
            "user_id": user_id,
            "context_type": "informal_activity",
            "description": f"{result['activity_type']} - {result['duration_estimate_minutes']}min",
            "original_message": message,
            "affects_training": True,  # Informal activities affect training volume
            "suggested_adaptation": "Consider this extra volume when calculating weekly total",
            "extracted_from_message_id": message_id,
            "extraction_confidence": result["confidence"],
            "extraction_model": "claude-3-haiku-20240307",
            "activity_created_id": activity.data[0]["id"] if activity.data else None
        }).execute()

        logger.info(f"Extracted informal activity: {result['activity_type']} for user {user_id}")

        return {
            "activity_id": activity.data[0]["id"] if activity.data else None,
            "activity_type": result["activity_type"],
            "duration_minutes": result["duration_estimate_minutes"],
            "confidence": result["confidence"]
        }

    except Exception as e:
        logger.error(f"Error extracting informal activity: {e}")
        return None


# ============================================================================
# LIFE CONTEXT EXTRACTION
# ============================================================================

async def extract_life_context(
    message: str,
    user_id: str,
    message_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Extract life context that might affect training or nutrition.

    Examples:
    - "Feeling super stressed this week" → stress context
    - "Traveling for work next week" → travel context
    - "Haven't been sleeping well" → sleep context
    - "Tweaked my shoulder yesterday" → injury context

    Args:
        message: User's chat message
        user_id: User UUID
        message_id: Original message UUID

    Returns:
        Dict with context data if detected, None otherwise
    """

    prompt = f"""Analyze this message for life context that might affect fitness training:

"{message}"

Detect any of these contexts:
1. stress - work stress, life stress, feeling overwhelmed
2. energy - low energy, fatigue, exhaustion, feeling tired
3. sleep - poor sleep, insomnia, not sleeping well
4. travel - traveling for work/vacation, on the road, away from home
5. injury - tweaked something, pain, soreness beyond normal
6. illness - sick, cold, flu, not feeling well
7. motivation - lack of motivation, feeling discouraged, losing interest
8. life_event - major life changes (moving, new job, relationship, etc.)

If context detected, extract:
- context_type: one of the above
- severity: low / moderate / high
- sentiment_score: -1.0 (very negative) to 1.0 (very positive)
- affects_training: true/false
- affects_nutrition: true/false
- suggested_adaptation: brief suggestion for how to adapt program
- confidence: 0.0-1.0

If NO context detected, return: {{"context_detected": false}}

Return ONLY valid JSON."""

    try:
        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        result = json.loads(response.content[0].text)

        if not result.get("context_detected"):
            return None

        # Only log if confidence is reasonable
        if result.get("confidence", 0) < 0.5:
            return None

        # Store in context log
        context_data = {
            "user_id": user_id,
            "context_type": result["context_type"],
            "severity": result.get("severity"),
            "sentiment_score": result.get("sentiment_score"),
            "description": message[:200],  # Truncate for storage
            "original_message": message,
            "affects_training": result.get("affects_training", False),
            "affects_nutrition": result.get("affects_nutrition", False),
            "suggested_adaptation": result.get("suggested_adaptation"),
            "extracted_from_message_id": message_id,
            "extraction_confidence": result["confidence"],
            "extraction_model": "claude-3-haiku-20240307"
        }

        context = supabase.table("user_context_log").insert(context_data).execute()

        logger.info(f"Extracted context: {result['context_type']} ({result.get('severity')}) for user {user_id}")

        return {
            "context_id": context.data[0]["id"] if context.data else None,
            "context_type": result["context_type"],
            "severity": result.get("severity"),
            "sentiment_score": result.get("sentiment_score"),
            "confidence": result["confidence"]
        }

    except Exception as e:
        logger.error(f"Error extracting life context: {e}")
        return None


# ============================================================================
# SENTIMENT SCORING
# ============================================================================

async def extract_sentiment_score(message: str) -> float:
    """
    Extract sentiment score from message.

    Args:
        message: User's chat message

    Returns:
        Float from -1.0 (very negative) to 1.0 (very positive)
    """

    prompt = f"""Rate the sentiment of this message on a scale from -1.0 to 1.0:
-1.0 = very negative, discouraged, defeated
 0.0 = neutral
 1.0 = very positive, motivated, excited

Message: "{message}"

Return ONLY a single number (e.g., 0.7 or -0.3), no explanation."""

    try:
        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )

        score = float(response.content[0].text.strip())
        return max(-1.0, min(1.0, score))  # Clamp to [-1, 1]

    except Exception as e:
        logger.error(f"Error extracting sentiment: {e}")
        return 0.0  # Default to neutral


# ============================================================================
# EXERCISE NAME MATCHING
# ============================================================================

async def search_exercise_by_name(
    exercise_name: str,
    user_id: str
) -> Optional[str]:
    """
    Search exercises table for matching exercise.

    Handles fuzzy matching:
    - "squat" → "Barbell Back Squat"
    - "bench" → "Barbell Bench Press"
    - "deadlift" → "Conventional Deadlift"

    Args:
        exercise_name: User's description of exercise
        user_id: User UUID (for potential custom exercises)

    Returns:
        Exercise UUID if found, None otherwise
    """

    try:
        # First try exact match (case-insensitive)
        result = supabase.table("exercises")\
            .select("id, name")\
            .ilike("name", f"%{exercise_name}%")\
            .eq("is_public", True)\
            .limit(1)\
            .execute()

        if result.data:
            return result.data[0]["id"]

        # Try using AI to match common variations
        prompt = f"""Given the exercise name "{exercise_name}", what is the most likely standard exercise name?

Common mappings:
- "squat" → "Barbell Back Squat"
- "bench" → "Barbell Bench Press"
- "deadlift" → "Conventional Deadlift"
- "pull up" → "Pull-Up"
- "chin up" → "Chin-Up"
- "ohp" → "Barbell Overhead Press"
- "row" → "Barbell Bent-Over Row"

Return ONLY the standard exercise name, nothing else."""

        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=50,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )

        standard_name = response.content[0].text.strip()

        # Search again with AI-suggested name
        result = supabase.table("exercises")\
            .select("id, name")\
            .ilike("name", f"%{standard_name}%")\
            .eq("is_public", True)\
            .limit(1)\
            .execute()

        if result.data:
            logger.info(f"Matched '{exercise_name}' to '{result.data[0]['name']}'")
            return result.data[0]["id"]

        logger.warning(f"Could not match exercise: {exercise_name}")
        return None

    except Exception as e:
        logger.error(f"Error searching exercise: {e}")
        return None


# ============================================================================
# AUTO-MATCH TO TEMPLATES
# ============================================================================

async def try_auto_match_to_template(
    activity_id: str,
    user_id: str,
    exercise_ids: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Try to match a completed activity to user's activity templates.

    Matching criteria:
    - Exercise overlap (did user do exercises from template?)
    - Time of day (did they train at usual time?)
    - Day of week (if template has preferred days)

    Args:
        activity_id: Activity UUID
        user_id: User UUID
        exercise_ids: List of exercise UUIDs completed

    Returns:
        Match result dict if matched, None otherwise
    """

    try:
        # Get user's active templates
        templates = supabase.table("activity_templates")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("is_active", True)\
            .eq("auto_match_enabled", True)\
            .execute()

        if not templates.data:
            return None

        best_match = None
        best_score = 0

        for template in templates.data:
            score = 0
            reasons = []

            # Check exercise overlap
            template_exercises = [e["exercise_id"] for e in template.get("default_exercises", [])]
            overlap = len(set(exercise_ids) & set(template_exercises))
            overlap_pct = (overlap / len(template_exercises)) * 100 if template_exercises else 0

            if overlap_pct > 0:
                score += overlap_pct
                reasons.append(f"Exercise match: {overlap_pct:.0f}%")

            # Store if best so far
            if score > best_score and score >= template["min_match_score"]:
                best_score = score
                best_match = {
                    "template_id": template["id"],
                    "template_name": template["template_name"],
                    "match_score": score,
                    "match_reasons": reasons
                }

        if best_match:
            # Update activity with template_id
            supabase.table("activities")\
                .update({"template_id": best_match["template_id"]})\
                .eq("id", activity_id)\
                .execute()

            # Record match
            supabase.table("activity_template_matches").insert({
                "activity_id": activity_id,
                "template_id": best_match["template_id"],
                "user_id": user_id,
                "match_score": best_match["match_score"],
                "match_method": "auto_suggested" if best_match["match_score"] < 90 else "auto_high_confidence",
                "match_reasons": best_match["match_reasons"],
                "user_action": "applied"
            }).execute()

            logger.info(f"Auto-matched activity {activity_id} to template {best_match['template_id']} (score: {best_match['match_score']:.1f})")

            return best_match

        return None

    except Exception as e:
        logger.error(f"Error auto-matching to template: {e}")
        return None


# ============================================================================
# COMBINED EXTRACTION
# ============================================================================

async def process_message_for_context(
    message: str,
    user_id: str,
    message_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a message for ALL types of context extraction.

    This is the main entry point called by unified_coach_enhancements.

    Args:
        message: User's chat message
        user_id: User UUID
        message_id: Original message UUID

    Returns:
        Dict containing all extracted data
    """

    results = {
        "informal_activity": None,
        "life_context": None,
        "sentiment_score": 0.0
    }

    # Extract sentiment (always)
    results["sentiment_score"] = await extract_sentiment_score(message)

    # Extract informal activity
    informal_activity = await extract_informal_activity(message, user_id, message_id)
    if informal_activity:
        results["informal_activity"] = informal_activity

    # Extract life context
    life_context = await extract_life_context(message, user_id, message_id)
    if life_context:
        results["life_context"] = life_context

    logger.info(f"Processed message for user {user_id}: activity={informal_activity is not None}, context={life_context is not None}, sentiment={results['sentiment_score']:.2f}")

    return results


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def estimate_calories_from_activity(
    activity_type: str,
    intensity: str,
    duration_minutes: int,
    user_weight_kg: float = 75  # Default average
) -> int:
    """Rough calorie estimation for informal activities."""

    # MET values by activity and intensity
    mets = {
        "walking": {"low": 2.5, "moderate": 3.5, "high": 5.0},
        "running": {"low": 6.0, "moderate": 9.0, "high": 12.0},
        "cycling": {"low": 4.0, "moderate": 7.0, "high": 10.0},
        "swimming": {"low": 5.0, "moderate": 7.0, "high": 10.0},
        "tennis": {"low": 5.0, "moderate": 7.0, "high": 8.0},
        "basketball": {"low": 6.0, "moderate": 8.0, "high": 10.0},
        "soccer": {"low": 6.0, "moderate": 8.0, "high": 10.0},
        "yoga": {"low": 2.0, "moderate": 3.0, "high": 4.0},
        "default": {"low": 3.0, "moderate": 5.0, "high": 7.0}
    }

    met_value = mets.get(activity_type.lower(), mets["default"])[intensity]

    # Calories = METs × weight_kg × hours
    calories = met_value * user_weight_kg * (duration_minutes / 60)

    return int(calories)
