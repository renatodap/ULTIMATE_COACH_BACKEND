"""
UnifiedCoachService Enhancements for Program Integration

Drop-in file for: ULTIMATE_COACH_BACKEND/app/services/unified_coach_enhancements.py

Extends existing UnifiedCoachService with:
1. Structured data extraction from conversational inputs
2. Meal logging from natural language
3. Workout completion tracking
4. Quick logging format parsing
5. Automatic database storage

Integration:
- Import these functions in existing UnifiedCoachService
- Call after each user message to extract structured data
- No changes to existing conversation flow required
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from anthropic import Anthropic
import os
import re
import json


# =============================================================================
# Configuration
# =============================================================================

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

# Quick logging regex patterns
QUICK_CALORIE_PATTERN = re.compile(
    r'(\d{3,4})\s*(?:cal|kcal|calories?)',
    re.IGNORECASE
)
QUICK_PROTEIN_PATTERN = re.compile(
    r'(\d{2,3})\s*(?:p|pro|protein)',
    re.IGNORECASE
)
QUICK_WEIGHT_PATTERN = re.compile(
    r'(\d{2,3}(?:\.\d)?)\s*(?:kg|kgs|kilos?)',
    re.IGNORECASE
)


# =============================================================================
# Structured Data Extraction
# =============================================================================


async def extract_structured_data_from_message(
    user_message: str,
    user_id: str,
    active_plan: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Extract structured data from user's conversational input.

    Looks for:
    - Meal logging ("I had chicken and rice for lunch")
    - Workout completion ("Finished today's workout, felt great!")
    - Weight updates ("Weighed in at 82.5 kg this morning")
    - Quick logs ("2500 cal, 180p")

    Returns dict with extracted data:
    {
        "meal_log": {...} or None,
        "workout_log": {...} or None,
        "weight_log": {...} or None,
        "extraction_confidence": float,
    }
    """

    # First, try quick logging patterns (instant, no LLM)
    quick_data = _try_quick_logging_patterns(user_message)
    if quick_data["found_quick_log"]:
        return quick_data

    # If no quick log, use LLM to extract structured data
    extraction_prompt = _build_extraction_prompt(user_message, active_plan)

    try:
        response = anthropic.messages.create(
            model="claude-3-5-haiku-20241022",  # Fast and cheap for extraction
            max_tokens=1000,
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0.0,  # Deterministic extraction
        )

        # Parse LLM response
        extracted_data = _parse_extraction_response(response.content[0].text)
        return extracted_data

    except Exception as e:
        print(f"Error in structured extraction: {e}")
        return {
            "meal_log": None,
            "workout_log": None,
            "weight_log": None,
            "extraction_confidence": 0.0,
            "error": str(e),
        }


def _try_quick_logging_patterns(message: str) -> Dict[str, Any]:
    """
    Try to extract data using regex patterns for quick logging.

    Supports formats like:
    - "2500 cal"
    - "180p" or "180 protein"
    - "82.5 kg"
    - "2500 cal, 180p" (combo)

    Returns immediately if patterns found (no LLM call needed).
    """

    result = {
        "found_quick_log": False,
        "meal_log": None,
        "workout_log": None,
        "weight_log": None,
        "extraction_confidence": 0.0,
    }

    # Check for calories
    cal_match = QUICK_CALORIE_PATTERN.search(message)
    if cal_match:
        calories = int(cal_match.group(1))
        result["meal_log"] = {"calories": calories, "quick_log": True}
        result["found_quick_log"] = True
        result["extraction_confidence"] = 0.95

    # Check for protein
    protein_match = QUICK_PROTEIN_PATTERN.search(message)
    if protein_match:
        protein = int(protein_match.group(1))
        if result["meal_log"]:
            result["meal_log"]["protein_g"] = protein
        else:
            result["meal_log"] = {"protein_g": protein, "quick_log": True}
        result["found_quick_log"] = True
        result["extraction_confidence"] = 0.95

    # Check for weight
    weight_match = QUICK_WEIGHT_PATTERN.search(message)
    if weight_match:
        weight = float(weight_match.group(1))
        result["weight_log"] = {"weight_kg": weight, "quick_log": True}
        result["found_quick_log"] = True
        result["extraction_confidence"] = 0.95

    return result


def _build_extraction_prompt(
    user_message: str,
    active_plan: Optional[Dict[str, Any]]
) -> str:
    """
    Build prompt for Claude to extract structured data.

    Provides context about user's active plan if available.
    """

    plan_context = ""
    if active_plan:
        plan_context = f"""
User's Active Plan Context:
- Daily calorie target: {active_plan.get('daily_calories', 'unknown')} kcal
- Daily protein target: {active_plan.get('daily_protein_g', 'unknown')} g
- Workouts per week: {active_plan.get('workouts_per_week', 'unknown')}
- Today's workout: {active_plan.get('todays_workout_name', 'unknown')}
"""

    return f"""
You are a data extraction assistant. Extract structured data from the user's message.

Look for:
1. **Meal logging**: Food eaten, estimated calories, macros, meal timing
2. **Workout completion**: Which workout they did, how it went, RPE, notes
3. **Body weight**: Weight measurements in kg

{plan_context}

User's message:
"{user_message}"

Return a JSON object with this EXACT structure:
{{
  "meal_log": {{
    "foods_mentioned": ["food1", "food2"],
    "meal_name": "breakfast|lunch|dinner|snack|unknown",
    "estimated_calories": number or null,
    "estimated_protein_g": number or null,
    "estimated_carbs_g": number or null,
    "estimated_fat_g": number or null,
    "confidence": 0.0-1.0,
    "notes": "any additional context"
  }} or null,

  "workout_log": {{
    "workout_completed": true|false,
    "workout_name": "name of workout or null",
    "exercises_mentioned": ["exercise1", "exercise2"],
    "estimated_sets": number or null,
    "duration_minutes": number or null,
    "rpe": 1-10 or null,
    "sentiment": "positive|neutral|negative",
    "notes": "any additional context"
  }} or null,

  "weight_log": {{
    "weight_kg": number or null,
    "confidence": 0.0-1.0
  }} or null
}}

Rules:
- If no meal data mentioned, set meal_log to null
- If no workout data mentioned, set workout_log to null
- If no weight mentioned, set weight_log to null
- Be conservative with estimates - only provide if reasonably confident
- Use confidence scores to indicate certainty

Return ONLY valid JSON, no other text.
""".strip()


def _parse_extraction_response(response_text: str) -> Dict[str, Any]:
    """
    Parse Claude's extraction response into structured dict.

    Handles errors and validates extracted data.
    """

    try:
        # Extract JSON from response (in case Claude added explanation)
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            raise ValueError("No JSON found in response")

        extracted = json.loads(json_match.group(0))

        # Validate structure
        result = {
            "meal_log": extracted.get("meal_log"),
            "workout_log": extracted.get("workout_log"),
            "weight_log": extracted.get("weight_log"),
            "extraction_confidence": 0.0,
        }

        # Calculate overall confidence
        confidences = []
        if result["meal_log"] and "confidence" in result["meal_log"]:
            confidences.append(result["meal_log"]["confidence"])
        if result["workout_log"] and "confidence" in result["workout_log"]:
            confidences.append(result["workout_log"].get("confidence", 0.7))
        if result["weight_log"] and "confidence" in result["weight_log"]:
            confidences.append(result["weight_log"]["confidence"])

        if confidences:
            result["extraction_confidence"] = sum(confidences) / len(confidences)

        return result

    except Exception as e:
        print(f"Error parsing extraction response: {e}")
        return {
            "meal_log": None,
            "workout_log": None,
            "weight_log": None,
            "extraction_confidence": 0.0,
            "parse_error": str(e),
        }


# =============================================================================
# Database Storage Functions
# =============================================================================


async def store_extracted_meal_log(
    user_id: str,
    meal_data: Dict[str, Any],
    supabase_client: Any,
) -> Optional[str]:
    """
    Store extracted meal data to meals table.

    Returns meal_id if successful, None if failed.
    """

    try:
        # Build meal record
        meal_record = {
            "user_id": user_id,
            "logged_at": datetime.utcnow().isoformat(),
            "meal_name": meal_data.get("meal_name", "unknown"),
            "foods_text": ", ".join(meal_data.get("foods_mentioned", [])),
            "total_calories": meal_data.get("estimated_calories"),
            "total_protein_g": meal_data.get("estimated_protein_g"),
            "total_carbs_g": meal_data.get("estimated_carbs_g"),
            "total_fat_g": meal_data.get("estimated_fat_g"),
            "confidence": meal_data.get("confidence", 0.5),
            "source": "conversational_coach",
            "notes": meal_data.get("notes"),
        }

        # Insert to database
        result = supabase_client.table("meals").insert(meal_record).execute()

        if result.data:
            meal_id = result.data[0]["id"]
            print(f"Stored meal log: {meal_id}")
            return meal_id

        return None

    except Exception as e:
        print(f"Error storing meal log: {e}")
        return None


async def store_extracted_workout_log(
    user_id: str,
    workout_data: Dict[str, Any],
    supabase_client: Any,
) -> Optional[str]:
    """
    Store extracted workout data to activities table.

    Returns activity_id if successful, None if failed.
    """

    try:
        # Build activity record
        activity_record = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "activity_type": "workout",
            "activity_name": workout_data.get("workout_name", "Workout"),
            "duration_minutes": workout_data.get("duration_minutes"),
            "total_sets": workout_data.get("estimated_sets"),
            "notes": workout_data.get("notes"),
            "rpe": workout_data.get("rpe"),
            "source": "conversational_coach",
            "exercises_text": ", ".join(workout_data.get("exercises_mentioned", [])),
        }

        # Insert to database
        result = supabase_client.table("activities").insert(activity_record).execute()

        if result.data:
            activity_id = result.data[0]["id"]
            print(f"Stored workout log: {activity_id}")
            return activity_id

        return None

    except Exception as e:
        print(f"Error storing workout log: {e}")
        return None


async def store_extracted_weight_log(
    user_id: str,
    weight_data: Dict[str, Any],
    supabase_client: Any,
) -> Optional[str]:
    """
    Store extracted weight data to body_metrics table.

    Returns metric_id if successful, None if failed.
    """

    try:
        # Build body metrics record
        metric_record = {
            "user_id": user_id,
            "recorded_at": datetime.utcnow().isoformat(),
            "weight_kg": weight_data.get("weight_kg"),
            "confidence": weight_data.get("confidence", 0.9),
            "source": "conversational_coach",
        }

        # Insert to database
        result = supabase_client.table("body_metrics").insert(metric_record).execute()

        if result.data:
            metric_id = result.data[0]["id"]
            print(f"Stored weight log: {metric_id}")
            return metric_id

        return None

    except Exception as e:
        print(f"Error storing weight log: {e}")
        return None


# =============================================================================
# Main Integration Function
# =============================================================================


async def process_message_for_structured_data(
    user_message: str,
    user_id: str,
    supabase_client: Any,
    active_plan: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Main function to call after each user message in UnifiedCoachService.

    Extracts structured data and stores to database automatically.

    Returns:
    {
        "extracted": bool,
        "meal_id": str or None,
        "activity_id": str or None,
        "metric_id": str or None,
        "confidence": float,
        "should_acknowledge": bool,  # Should coach acknowledge the log?
    }

    Usage in existing UnifiedCoachService:
    ```python
    async def process_user_message(self, user_id: str, message: str):
        # ... existing conversation logic ...

        # NEW: Extract and store structured data
        from services.unified_coach_enhancements import process_message_for_structured_data

        extraction_result = await process_message_for_structured_data(
            user_message=message,
            user_id=user_id,
            supabase_client=self.supabase,
            active_plan=await self._get_active_plan(user_id),
        )

        # If data was extracted, coach can acknowledge it
        if extraction_result["should_acknowledge"]:
            acknowledgment = self._build_acknowledgment(extraction_result)
            # Add to conversation context or send as system message

        # ... continue with conversation ...
    ```
    """

    # Extract structured data
    extracted_data = await extract_structured_data_from_message(
        user_message, user_id, active_plan
    )

    result = {
        "extracted": False,
        "meal_id": None,
        "activity_id": None,
        "metric_id": None,
        "confidence": extracted_data.get("extraction_confidence", 0.0),
        "should_acknowledge": False,
    }

    # Store meal log if found
    if extracted_data.get("meal_log"):
        meal_id = await store_extracted_meal_log(
            user_id, extracted_data["meal_log"], supabase_client
        )
        if meal_id:
            result["meal_id"] = meal_id
            result["extracted"] = True
            result["should_acknowledge"] = True

    # Store workout log if found
    if extracted_data.get("workout_log"):
        workout_id = await store_extracted_workout_log(
            user_id, extracted_data["workout_log"], supabase_client
        )
        if workout_id:
            result["activity_id"] = workout_id
            result["extracted"] = True
            result["should_acknowledge"] = True

    # Store weight log if found
    if extracted_data.get("weight_log"):
        metric_id = await store_extracted_weight_log(
            user_id, extracted_data["weight_log"], supabase_client
        )
        if metric_id:
            result["metric_id"] = metric_id
            result["extracted"] = True
            result["should_acknowledge"] = True

    return result


def build_acknowledgment_message(extraction_result: Dict[str, Any]) -> str:
    """
    Build a friendly acknowledgment message for extracted data.

    Used by coach to confirm what was logged.
    """

    parts = []

    if extraction_result.get("meal_id"):
        parts.append("✅ Meal logged")

    if extraction_result.get("activity_id"):
        parts.append("✅ Workout logged")

    if extraction_result.get("metric_id"):
        parts.append("✅ Weight recorded")

    if not parts:
        return ""

    confidence = extraction_result.get("confidence", 0.0)

    message = " | ".join(parts)

    # Add confidence note if low
    if confidence < 0.7:
        message += " (I made my best estimate - you can edit this in your logs if needed)"

    return message


# =============================================================================
# Helper: Get Active Plan
# =============================================================================


async def get_user_active_plan_summary(
    user_id: str,
    supabase_client: Any,
) -> Optional[Dict[str, Any]]:
    """
    Get summary of user's active plan for extraction context.

    Returns lightweight dict with key info (not full plan).
    """

    try:
        result = supabase_client.table("plan_versions") \
            .select("plan_data") \
            .eq("user_id", user_id) \
            .eq("status", "active") \
            .order("version", desc=True) \
            .limit(1) \
            .execute()

        if not result.data:
            return None

        plan_data = result.data[0]["plan_data"]

        # Extract summary info
        return {
            "daily_calories": plan_data.get("nutrition", {}).get("daily_calories"),
            "daily_protein_g": plan_data.get("nutrition", {}).get("protein_g"),
            "workouts_per_week": plan_data.get("training", {}).get("workouts_per_week"),
            "todays_workout_name": "Unknown",  # Would need to calculate from cycle day
        }

    except Exception as e:
        print(f"Error fetching active plan summary: {e}")
        return None
