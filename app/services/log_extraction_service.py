"""
Log Extraction Service - Parse Meals & Activities from Natural Language

Uses Claude 3.5 Haiku to detect and extract structured log data:
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
    Extracts structured log data from natural language using Claude 3.5 Haiku.

    Returns:
    - log_type: 'meal', 'activity', 'measurement', or None
    - confidence: 0.0-1.0
    - structured_data: Parsed data ready for database insertion
    """

    def __init__(self, anthropic_client):
        self.anthropic = anthropic_client

    async def extract_log_data(
        self,
        message: str,
        user_id: str,
        image_base64: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Analyze message and extract log data if present.

        SUPPORTS MULTI-LOGGING: Can extract multiple logs from one message.
        Example: "I ate eggs for breakfast and chicken for lunch" → returns 2 meal logs

        SUPPORTS PHOTO ANALYSIS: If image provided, uses Claude Vision to identify foods.
        Example: Photo of meal + "breakfast" → Claude identifies all foods in photo

        Args:
            message: User's message
            user_id: User UUID (for context)
            image_base64: Optional base64-encoded image for food photo analysis

        Returns:
            [
                {
                    "log_type": "meal" | "activity" | "measurement",
                    "confidence": 0.0-1.0,
                    "structured_data": {...},
                    "original_text": message,
                    "photo_analyzed": bool  # True if image was analyzed
                },
                {...}  # Additional logs if multi-logging detected
            ]

            Returns None if no loggable data detected.
            Returns list with single item for single logs.
            Returns list with multiple items for multi-logs.
        """
        logger.info(f"[LogExtraction] 🔍 Analyzing: '{message[:50]}...' (has_image={image_base64 is not None})")

        # Enhanced system prompt for photo analysis
        photo_instructions = ""
        if image_base64:
            photo_instructions = """

**PHOTO ANALYSIS MODE:**

You have been provided with an IMAGE of food. Analyze the photo carefully to identify:
1. All visible food items (be specific: "grilled chicken breast", not just "chicken")
2. Estimated quantities based on portion sizes visible
3. Cooking methods (grilled, fried, boiled, raw, etc.)
4. Serving sizes (estimate grams based on plate size and typical portions)

Common portion estimation guidelines:
- Palm-sized protein (chicken, steak) = ~150-200g
- Fist-sized carbs (rice, pasta) = ~150-200g
- Handful of nuts/snacks = ~30g
- Standard plate serving of vegetables = ~100-150g
- Large plate = portions may be 1.5x typical

Be thorough - list ALL visible foods, even condiments and garnishes.
Estimate quantities conservatively - better to underestimate than overestimate.

CRITICAL: If the image shows food, you MUST extract it as a meal log with all visible foods."""

        system_prompt = """You are a log data extraction assistant for a fitness coach app.

Your job is to detect if a message contains loggable fitness data and extract it WITH COMMON UNITS.""" + photo_instructions + """

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

**CRITICAL: MULTI-LOGGING SUPPORT**
If user mentions MULTIPLE distinct meals/activities in one message, extract ALL of them as separate logs.

Examples of multi-logging:
- "I ate eggs for breakfast and chicken for lunch" → 2 meal logs
- "I ran 5K and did 100 pushups" → 2 activity logs
- "I weigh 175 lbs and ate 3 eggs" → 1 measurement + 1 meal
- "Had breakfast (eggs) and went for a run" → 1 meal + 1 activity

**SINGLE LOG** (return as single-item array):
```json
[{
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
}]
```

**MULTI-LOG** (return multiple items in array):
```json
[
  {
    "log_type": "meal",
    "classification_confidence": 0.95,
    "nutrition_confidence": 0.75,
    "confidence_breakdown": {"quantity_precision": 0.8, "food_identification": 0.9, "preparation_detail": 0.7},
    "structured_data": {
      "meal_type": "breakfast",
      "foods": [{"name": "eggs", "quantity": 3, "unit": "pieces", "estimated_grams": 150}],
      "notes": "Breakfast part of message"
    }
  },
  {
    "log_type": "meal",
    "classification_confidence": 0.92,
    "nutrition_confidence": 0.68,
    "confidence_breakdown": {"quantity_precision": 0.6, "food_identification": 0.8, "preparation_detail": 0.5},
    "structured_data": {
      "meal_type": "lunch",
      "foods": [{"name": "chicken", "quantity": null, "unit": null, "estimated_grams": 200, "note": "estimated"}],
      "notes": "Lunch part of message"
    }
  }
]
```

**NO LOGGABLE DATA:**
Return null (not an array)

**CRITICAL RULES:**
- ALWAYS return an ARRAY when logs are found (even for single log)
- Return null (not array) when NO logs found
- Each log in array must be COMPLETE with all fields
- Confidence scores are PER LOG (not shared)
- For multi-logs, extract the relevant part of the message in "notes" field for each

Return ONLY valid JSON (array or null), no explanations."""

        # Build user prompt with optional image
        if image_base64:
            user_prompt_text = f"""Analyze the provided IMAGE and message to extract loggable fitness data.

Message: "{message}"

Current time: {datetime.now().isoformat()}

Identify ALL foods visible in the image with estimated quantities.
Return JSON with log_type, confidence, and structured_data."""

            user_content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_base64
                    }
                },
                {
                    "type": "text",
                    "text": user_prompt_text
                }
            ]
        else:
            user_prompt_text = f"""Analyze this message and extract any loggable fitness data:

"{message}"

Current time: {datetime.now().isoformat()}

Return JSON with log_type, confidence, and structured_data."""

            user_content = user_prompt_text

        try:
            response = self.anthropic.messages.create(
                model="claude-3-5-haiku-20241022" if not image_base64 else "claude-3-5-sonnet-20241022",  # Use Sonnet for vision
                max_tokens=1000 if image_base64 else 500,  # More tokens for photo analysis
                temperature=0.1,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_content}
                ]
            )

            response_text = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            extraction = json.loads(response_text)

            # Handle multi-logging response format
            if extraction is None or extraction == "null":
                logger.info("[LogExtraction] ❌ No loggable data detected (null response)")
                return None

            # Ensure it's an array (support both old single-dict and new array format)
            if isinstance(extraction, dict):
                # Old format: single log as dict → wrap in array
                logger.debug("[LogExtraction] Converting single-dict response to array format")
                extraction = [extraction]
            elif not isinstance(extraction, list):
                logger.error(f"[LogExtraction] ❌ Unexpected response type: {type(extraction)}")
                return None

            # Validate and filter each log
            valid_logs = []
            for idx, log in enumerate(extraction):
                log_type = log.get("log_type")
                if not log_type:
                    logger.debug(f"[LogExtraction] Skipping log {idx}: no log_type")
                    continue

                # Use classification_confidence for log detection threshold
                classification_conf = log.get("classification_confidence", 0)
                nutrition_conf = log.get("nutrition_confidence", 0)

                if classification_conf < 0.5:
                    logger.info(
                        f"[LogExtraction] ⚠️ Log {idx} ({log_type}): Classification confidence too low: {classification_conf:.2f}"
                    )
                    continue

                # Add original text
                log["original_text"] = message

                # Mark if photo was analyzed
                log["photo_analyzed"] = image_base64 is not None

                # For backward compatibility, keep generic "confidence" field
                log["confidence"] = classification_conf

                logger.info(
                    f"[LogExtraction] ✅ Log {idx+1}: {log_type} "
                    f"(classification: {classification_conf:.2f}, nutrition: {nutrition_conf:.2f})"
                )

                valid_logs.append(log)

            # Return valid logs or None if all filtered out
            if not valid_logs:
                logger.info("[LogExtraction] ❌ No valid logs after filtering")
                return None

            logger.info(f"[LogExtraction] ✅ Returning {len(valid_logs)} log(s)")
            return valid_logs

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

def get_log_extraction_service(anthropic_client=None) -> LogExtractionService:
    """Get singleton LogExtractionService instance."""
    global _log_extraction_service
    if _log_extraction_service is None:
        if anthropic_client is None:
            from anthropic import Anthropic
            import os
            anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        _log_extraction_service = LogExtractionService(anthropic_client)
    return _log_extraction_service
