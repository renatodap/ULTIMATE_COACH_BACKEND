"""
Coach AI Service

Handles AI-powered message classification and structured data extraction
for quick entry logs (meals, activities, measurements).
"""

import logging
from typing import Dict, Any, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
from app.config import settings

logger = logging.getLogger(__name__)


class CoachAIService:
    """AI service for coach message processing."""

    def __init__(self):
        """Initialize AI service with Anthropic client."""
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY not configured - AI features will be limited")
            self.client = None
        else:
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        # Thread pool for running sync Anthropic calls in async context
        self.executor = ThreadPoolExecutor(max_workers=3)

    async def classify_and_extract(
        self,
        message: str
    ) -> Tuple[str, Optional[Dict[str, Any]], float]:
        """
        Classify message and extract structured data.

        Args:
            message: User's message text

        Returns:
            Tuple of (classification, structured_data, confidence)
            - classification: "meal", "activity", "measurement", or "chat"
            - structured_data: Extracted data dict (None if chat)
            - confidence: 0.0-1.0 confidence score
        """
        if not self.client:
            # No AI available - default to chat
            return ("chat", None, 1.0)

        try:
            # Build system prompt
            system_prompt = self._build_classification_prompt()

            # Call Claude in thread pool (since SDK is synchronous)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                lambda: self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    temperature=0.1,  # Low temperature for consistent classification
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": message}
                    ]
                )
            )

            # Parse response
            response_text = response.content[0].text
            logger.info(f"[CoachAI] Claude response: {response_text[:200]}...")

            # Extract classification and data
            classification, structured_data, confidence = self._parse_ai_response(response_text)

            # Calculate cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost_usd = self._calculate_cost(input_tokens, output_tokens)

            logger.info(
                f"[CoachAI] Classification: {classification}, "
                f"Confidence: {confidence:.2f}, "
                f"Cost: ${cost_usd:.4f}"
            )

            return (classification, structured_data, confidence)

        except Exception as e:
            logger.error(f"[CoachAI] Classification failed: {e}", exc_info=True)
            # Fallback to chat on error
            return ("chat", None, 0.0)

    def _build_classification_prompt(self) -> str:
        """Build system prompt for classification."""
        return """You are a fitness coach AI assistant. Your job is to classify user messages and extract structured data.

**Note:** Focus ONLY on classification and data extraction. Do not use user context or preferences for this task - those are for personalized coaching responses, not log detection.

**Message Types:**
1. **meal** - User is logging food they ate/drank
   - Examples: "I ate 3 eggs", "Had chicken and rice for lunch", "Drinking protein shake"

2. **activity** - User is logging a workout or physical activity
   - Examples: "I ran 5km", "Did 3 sets of bench press", "Played basketball for 1 hour"

3. **measurement** - User is logging body measurements
   - Examples: "I weigh 185 lbs", "My weight is 84kg", "Body fat is 15%"

4. **chat** - General conversation, questions, or anything else
   - Examples: "What should I eat?", "How's my progress?", "Tell me about protein"

**Your Task:**
Classify the message and extract structured data in this EXACT JSON format:

```json
{
  "type": "meal|activity|measurement|chat",
  "confidence": 0.95,
  "data": {
    // For meals:
    "meal_type": "breakfast|lunch|dinner|snack",
    "items": [
      {"name": "eggs", "quantity": 3, "unit": "whole"},
      {"name": "oatmeal", "quantity": 1, "unit": "cup"}
    ],
    "notes": "optional user notes"

    // For activities:
    "category": "cardio_steady_state|strength_training|sports|other",
    "activity_name": "Morning Run",
    "duration_minutes": 30,
    "calories_burned": 250,  // estimate if not provided
    "intensity_mets": 8.0,  // estimate based on activity
    "metrics": {
      "distance_km": 5.0  // activity-specific metrics
    }

    // For measurements:
    "weight_kg": 84.0,  // convert from lbs if needed
    "body_fat_percentage": 15.0  // if provided
  }
}
```

**Important Rules:**
1. Use metric units (kg, km, etc.)
2. Estimate missing calories/intensity for activities
3. Infer meal type from time/context (default to "snack" if unclear)
4. Be generous with classification - if it might be a log, classify it as such
5. Confidence: 0.9+ for clear logs, 0.7-0.9 for likely logs, <0.7 for uncertain

**Return ONLY the JSON, no other text.**"""

    def _parse_ai_response(self, response_text: str) -> Tuple[str, Optional[Dict[str, Any]], float]:
        """Parse AI response into classification, data, and confidence."""
        import json
        import re

        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Try to find raw JSON
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")

            # Parse JSON
            result = json.loads(json_text)

            classification = result.get("type", "chat")
            confidence = result.get("confidence", 0.5)
            data = result.get("data") if classification != "chat" else None

            return (classification, data, confidence)

        except Exception as e:
            logger.error(f"[CoachAI] Failed to parse response: {e}", exc_info=True)
            return ("chat", None, 0.0)

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD for Claude API call."""
        # Claude 3.5 Sonnet pricing (as of 2024):
        # $3 per million input tokens
        # $15 per million output tokens
        input_cost = (input_tokens / 1_000_000) * 3.0
        output_cost = (output_tokens / 1_000_000) * 15.0
        return input_cost + output_cost


# Global service instance
coach_ai_service = CoachAIService()
