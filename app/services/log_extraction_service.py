"""
Log Extraction Service - Parse Meals & Activities from Natural Language

Uses Groq Llama 3.3 70B to detect and extract structured log data:
- Meals: "I ate 300g chicken breast and rice"
- Activities: "I ran 5km today"
- Measurements: "I weigh 80kg now"

This is used by the coach's log mode for quick data entry.
"""

import logging
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class LogExtractionService:
    """
    Extracts structured log data from natural language using Groq.

    Returns:
    - log_type: 'meal', 'activity', 'measurement', or None
    - confidence: 0.0-1.0
    - structured_data: Parsed data ready for database insertion
    """

    def __init__(self, groq_client):
        self.groq = groq_client

    async def extract_log_data(
        self,
        message: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze message and extract log data if present.

        Args:
            message: User's message
            user_id: User UUID (for context)

        Returns:
            {
                "log_type": "meal" | "activity" | "measurement",
                "confidence": 0.0-1.0,
                "structured_data": {...},
                "original_text": message
            }

            Returns None if no loggable data detected.
        """
        logger.info(f"[LogExtraction] 🔍 Analyzing: '{message[:50]}...'")

        system_prompt = """You are a log data extraction assistant for a fitness coach app.

Your job is to detect if a message contains loggable fitness data and extract it.

**LOGGABLE DATA TYPES:**

1. **MEAL** - User ate/drank something
   Examples:
   - "I ate 300g chicken breast and 200g rice"
   - "Had a protein shake after workout"
   - "Just finished lunch: grilled salmon with veggies"
   - "I'm eating an apple"

2. **ACTIVITY** - User did a workout/exercise
   Examples:
   - "I ran 5km in 30 minutes"
   - "Just finished leg day: squats, deadlifts, lunges"
   - "Did 45 min yoga session"
   - "Played basketball for 2 hours"

3. **MEASUREMENT** - User reports body measurement
   Examples:
   - "I weigh 80kg now"
   - "My weight is 175 lbs today"
   - "Body fat is 15%"

**NOT LOGGABLE:**
- Questions: "Should I eat chicken?" (NO - just asking)
- Plans: "I'm going to run tomorrow" (NO - future tense)
- General chat: "How are you?" (NO - no data)
- Advice requests: "What should I eat?" (NO - no actual consumption)

**EXTRACTION RULES:**

For MEAL:
- Extract: meal_type (breakfast/lunch/dinner/snack), foods array (name, quantity_g, estimated if not specified)
- Be flexible with quantities: "a chicken breast" ≈ 200g, "a banana" ≈ 120g
- If no meal_type mentioned, use "snack"

For ACTIVITY:
- Extract: category, activity_name, duration_minutes, estimated_calories, metrics (distance, etc.)
- Categories: cardio_steady_state, cardio_interval, strength_training, sports, flexibility, other
- Be flexible: "ran" → cardio_steady_state, "lifted weights" → strength_training

For MEASUREMENT:
- Extract: weight_kg (convert lbs if needed), body_fat_percentage

**CONFIDENCE SCORING:**
- 0.9-1.0: Very clear ("I ate 300g chicken")
- 0.7-0.9: Clear but some estimation ("I ate chicken breast")
- 0.5-0.7: Ambiguous ("had some food")
- <0.5: Too vague (don't extract)

**OUTPUT FORMAT:**

If loggable data found:
```json
{
  "log_type": "meal",
  "confidence": 0.85,
  "structured_data": {
    "meal_type": "lunch",
    "foods": [
      {"name": "chicken breast", "quantity_g": 300},
      {"name": "white rice", "quantity_g": 200, "estimated": true}
    ],
    "notes": "User's original message"
  }
}
```

If NO loggable data:
```json
{
  "log_type": null,
  "confidence": 0.0,
  "structured_data": null
}
```

Return ONLY valid JSON, no explanations."""

        user_prompt = f"""Analyze this message and extract any loggable fitness data:

"{message}"

Current time: {datetime.now().isoformat()}

Return JSON with log_type, confidence, and structured_data."""

        try:
            response = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            response_text = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            extraction = json.loads(response_text)

            # Validate response
            if not extraction.get("log_type"):
                logger.info("[LogExtraction] ❌ No loggable data detected")
                return None

            if extraction["confidence"] < 0.5:
                logger.info(
                    f"[LogExtraction] ⚠️ Confidence too low: {extraction['confidence']}"
                )
                return None

            logger.info(
                f"[LogExtraction] ✅ Extracted {extraction['log_type']} "
                f"(confidence: {extraction['confidence']:.2f})"
            )

            # Add original text
            extraction["original_text"] = message

            return extraction

        except json.JSONDecodeError as e:
            logger.error(f"[LogExtraction] ❌ JSON decode failed: {e}")
            logger.error(f"[LogExtraction] Raw response: {response_text[:200]}")
            return None
        except Exception as e:
            logger.error(f"[LogExtraction] ❌ Extraction failed: {e}", exc_info=True)
            return None

    async def extract_meal_details(
        self,
        structured_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Enhance meal data with nutrition lookup.

        Takes basic meal data and enriches it with nutrition info
        from the food database.

        Args:
            structured_data: Basic meal data from extract_log_data
            user_id: User UUID

        Returns:
            Enhanced structured_data with nutrition totals
        """
        logger.info("[LogExtraction] 🍽️ Enhancing meal data with nutrition")

        # TODO: Integrate with food database to get nutrition
        # For now, return as-is
        # Future: Look up each food in foods table, calculate totals

        return structured_data

    async def extract_activity_details(
        self,
        structured_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Enhance activity data with calorie estimation.

        Args:
            structured_data: Basic activity data from extract_log_data
            user_id: User UUID

        Returns:
            Enhanced structured_data with estimated calories
        """
        logger.info("[LogExtraction] 🏃 Enhancing activity data with calories")

        # TODO: Integrate with estimate_activity_calories tool
        # For now, return as-is
        # Future: Calculate calories based on user weight + METs

        return structured_data


# Singleton
_log_extraction_service: Optional[LogExtractionService] = None

def get_log_extraction_service(groq_client=None) -> LogExtractionService:
    """Get singleton LogExtractionService instance."""
    global _log_extraction_service
    if _log_extraction_service is None:
        if groq_client is None:
            from groq import Groq
            import os
            groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        _log_extraction_service = LogExtractionService(groq_client)
    return _log_extraction_service
