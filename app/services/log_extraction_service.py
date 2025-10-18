"""
Log Extraction Service - Parse Meals & Activities from Natural Language

Uses Groq Llama 3.3 70B to detect and extract structured log data:
- Meals: "I ate 300g chicken breast and rice"
- Activities: "I ran 5km today"
- Measurements: "I weigh 80kg now"

This is used by the coach's log mode for quick data entry.
"""

import structlog
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

logger = structlog.get_logger()


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

Your job is to detect if a message contains loggable fitness data and extract it WITH COMMON UNITS.

**LOGGABLE DATA TYPES:**

1. **MEAL** - User ate/drank something
   Examples:
   - "I ate 300g chicken breast and 200g rice"
   - "Had a protein shake after workout"
   - "Just finished lunch: grilled salmon with veggies"
   - "I ate 2 bananas" ← COMMON UNIT (pieces)
   - "1 scoop protein powder" ← COMMON UNIT (scoops)
   - "1 cup rice" ← COMMON UNIT (cups)

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

For MEAL - ENHANCED WITH COMMON UNITS:
- Extract: meal_type (breakfast/lunch/dinner/snack), foods array with UNITS
- Each food must have: name, quantity, unit, estimated_grams
- Common units: pieces, scoops, cups, tablespoons (tbsp), slices, servings, grams (g)
- If user says grams: {"quantity": 300, "unit": "grams", "estimated_grams": 300}
- If user says pieces: {"quantity": 2, "unit": "pieces", "estimated_grams": 240} (estimate based on typical size)
- If user says "a banana": {"quantity": 1, "unit": "pieces", "estimated_grams": 120}
- If user says "some chicken": {"quantity": null, "unit": null, "estimated_grams": null, "note": "vague_quantity"}

Typical gram estimates for common units:
- banana (piece): 120g
- egg (piece): 50g
- chicken breast (piece): 200g
- rice (cup cooked): 200g
- rice (tbsp): 12g
- protein powder (scoop): 30g
- bread (slice): 30g

For ACTIVITY:
- Extract: category, activity_name, duration_minutes, metrics (distance, etc.)
- Categories: cardio_steady_state, cardio_interval, strength_training, sports, flexibility, other
- Be flexible: "ran" → cardio_steady_state, "lifted weights" → strength_training

For MEASUREMENT:
- Extract: weight_kg (convert lbs if needed), body_fat_percentage

**DUAL CONFIDENCE SCORING:**

classification_confidence: How sure is this a log? (0-1)
- 0.9-1.0: Definitely a log ("I ate...")
- 0.5-0.9: Probably a log but context unclear
- <0.5: Not a log (question or plan)

nutrition_confidence: How accurate is nutrition data? (0-1)
Multiply these factors:
1. Quantity precision (0-1):
   - 1.0: Exact grams ("300g chicken")
   - 0.8: Common unit with number ("2 bananas", "1 cup rice")
   - 0.6: Common unit vague ("a banana", "some eggs")
   - 0.3: Very vague ("some chicken", "a bit of rice")
   - 0.0: No quantity at all

2. Food identification (0-1):
   - 1.0: Specific + cooking method ("grilled chicken breast")
   - 0.8: Specific ("chicken breast")
   - 0.6: Generic ("chicken")
   - 0.4: Very generic ("meat")
   - 0.2: Unclear ("food")

3. Preparation detail (0-1):
   - 1.0: Cooking method specified ("grilled", "fried", "baked")
   - 0.7: Type specified ("breast" vs "thigh")
   - 0.5: No details (affects calorie accuracy!)

nutrition_confidence = (quantity_precision^0.5) × (food_id^0.3) × (preparation^0.2)

**OUTPUT FORMAT:**

If loggable data found:
```json
{
  "log_type": "meal",
  "classification_confidence": 0.95,
  "nutrition_confidence": 0.72,
  "confidence_breakdown": {
    "quantity_precision": 0.8,
    "food_identification": 0.9,
    "preparation_detail": 0.7
  },
  "structured_data": {
    "meal_type": "lunch",
    "foods": [
      {
        "name": "chicken breast",
        "quantity": 2,
        "unit": "pieces",
        "estimated_grams": 400,
        "cooking_method": "grilled",
        "estimated": false
      },
      {
        "name": "white rice",
        "quantity": 1,
        "unit": "cups",
        "estimated_grams": 200,
        "estimated": true
      }
    ],
    "notes": "User's original message"
  }
}
```

If NO loggable data:
```json
{
  "log_type": null,
  "classification_confidence": 0.0,
  "nutrition_confidence": 0.0,
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

            # Use classification_confidence for log detection threshold
            classification_conf = extraction.get("classification_confidence", 0)
            nutrition_conf = extraction.get("nutrition_confidence", 0)

            if classification_conf < 0.5:
                logger.info(
                    f"[LogExtraction] ⚠️ Classification confidence too low: {classification_conf}"
                )
                return None

            logger.info(
                f"[LogExtraction] ✅ Extracted {extraction['log_type']} "
                f"(classification: {classification_conf:.2f}, nutrition: {nutrition_conf:.2f})"
            )

            # Add original text
            extraction["original_text"] = message

            # For backward compatibility, keep generic "confidence" field
            extraction["confidence"] = classification_conf

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
