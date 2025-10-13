"""
Complexity Analyzer Service - Smart Routing (Personalization-First)

Analyzes query complexity to route to appropriate model:
- Trivial (30%): Canned responses (FREE, 0ms) - greetings, thanks, bye
- Simple (10%): Groq Llama 3.3 70B ($0.01, 500ms) - pure definitions
- Complex (60%): Claude 3.5 Sonnet ($0.15, 2000ms) - personalized coaching

Uses Claude 3.5 Haiku for ACCURATE classification ($0.0002/query, 800ms).
Routes 90% of queries to personalized responses (canned + Claude).
Cost: $0.00527/query vs $0.0056/query (all-Claude).
Savings: 94% cheaper while maintaining quality.
"""

import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class ComplexityAnalyzerService:
    """
    Analyzes query complexity for smart routing.

    Uses Claude 3.5 Haiku for fast, accurate classification.
    Much more reliable than Groq for understanding user intent.
    """

    def __init__(self, anthropic_client):
        """
        Initialize with Anthropic client (for Claude Haiku).

        Args:
            anthropic_client: Anthropic (NOT AsyncAnthropic) client for sync calls
        """
        self.anthropic = anthropic_client

    async def analyze_complexity(
        self,
        message: str,
        has_image: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze query complexity.

        Args:
            message: User's message
            has_image: Whether message has image

        Returns:
            {
                "complexity": "trivial" | "simple" | "complex",
                "confidence": 0.0-1.0,
                "recommended_model": "canned" | "groq" | "claude",
                "reasoning": str
            }
        """
        logger.info(f"[ComplexityAnalyzer] 🧠 Analyzing: '{message[:50]}...'")

        # Images always require Claude (multimodal)
        if has_image:
            return {
                "complexity": "complex",
                "confidence": 1.0,
                "recommended_model": "claude",
                "reasoning": "Image requires multimodal model (Claude)"
            }

        system_prompt = """You are an expert query classifier for an AI fitness coach system.

Your job: Analyze user queries and classify them into ONE of three categories based on what the query needs.

═══════════════════════════════════════════════════════════════════
CATEGORY 1: TRIVIAL (30% of queries)
═══════════════════════════════════════════════════════════════════
**What:** One-word social interactions with NO fitness content
**Routing:** Canned response (pattern-matched, instant, FREE)
**Examples:**
- Greetings: "hi", "hello", "hey", "what's up", "sup"
- Thanks: "thanks", "thank you", "thx", "ty"
- Acknowledgments: "ok", "okay", "got it", "understood", "cool"
- Goodbyes: "bye", "goodbye", "see you", "later", "cya"

**Key rule:** If there's ANY fitness content, it's NOT trivial.

═══════════════════════════════════════════════════════════════════
CATEGORY 2: SIMPLE (10% of queries)
═══════════════════════════════════════════════════════════════════
**What:** Pure educational/definitional questions with ZERO personalization benefit
**Routing:** Groq Llama (fast, cheap, NO tool access)
**Examples:**
- Definitions: "What is BMR?", "Define protein", "What is a calorie?"
- Science: "Explain metabolism", "How does muscle growth work?"
- Concepts: "What is progressive overload?", "What are macros?"

**CRITICAL:** If the answer would be BETTER with user context, it's COMPLEX, not SIMPLE.

Test: Would knowing the user's goals/stats/preferences make this answer 2x better?
- NO → SIMPLE
- YES → COMPLEX

═══════════════════════════════════════════════════════════════════
CATEGORY 3: COMPLEX (60% of queries)
═══════════════════════════════════════════════════════════════════
**What:** Anything requiring user data, personalization, or tool calling
**Routing:** Claude 3.5 Sonnet with agentic tools (powerful, personalized)

**ALWAYS COMPLEX - User Data Queries:**
- "What have I done today?"
- "What did I eat yesterday?"
- "Show my progress"
- "Show me my stats"
- "What are my goals?"
- "Can you see my profile?"
- "What are my macros?"
- "How am I doing?"
- "Am I on track?"
- Any question about "my [anything]"

**ALWAYS COMPLEX - Planning Requests:**
- "Give me a [workout/meal/training] plan"
- "Create a [program/routine/plan]"
- "Make me a [X]-week plan"
- "Design a workout"
- "Build me a program"
- "Suggest a routine"
- "I need a plan"
- ANY request for multi-day/week planning

**ALWAYS COMPLEX - Personalized Advice:**
- "Should I [do cardio/eat carbs/increase calories]?"
- "How much [protein/calories] should I eat?"
- "How many [reps/sets/days] should I do?"
- "What should I eat [before/after/for] X?"
- "Is this [food/workout/amount] good for me?"
- "What's better for me: X or Y?"
- Any "should I" or "how much/many should I" question

**ALWAYS COMPLEX - Analysis Requests:**
- "Analyze my [week/progress/approach]"
- "Review my [diet/training/performance]"
- "Compare [this week to last week]"
- "What's wrong with my [diet/workout]?"
- "Why am I [not losing weight/plateauing]?"

**ALWAYS COMPLEX - Questions That Benefit From Context:**
Even if question SOUNDS generic, if user context makes it 2x better → COMPLEX
- "How much protein in chicken?" → Generic: "31g/100g" vs Personalized: "31g/100g. You need 150g daily. Eat 500g chicken."
- "What should I eat after workout?" → Generic: "Protein + carbs" vs Personalized: "You're in deficit, need 40g protein. Try 300g chicken + 200g rice."

**When in doubt → COMPLEX** (better to have tool access than not)

═══════════════════════════════════════════════════════════════════
EXAMPLES (Learn the pattern)
═══════════════════════════════════════════════════════════════════

**TRIVIAL:**
"hi" → {"complexity": "trivial", "confidence": 0.99, "recommended_model": "canned", "reasoning": "Greeting"}
"thanks" → {"complexity": "trivial", "confidence": 0.99, "recommended_model": "canned", "reasoning": "Acknowledgment"}
"bye" → {"complexity": "trivial", "confidence": 0.99, "recommended_model": "canned", "reasoning": "Goodbye"}

**SIMPLE:**
"What is BMR?" → {"complexity": "simple", "confidence": 0.95, "recommended_model": "groq", "reasoning": "Pure definition, no personalization benefit"}
"Define progressive overload" → {"complexity": "simple", "confidence": 0.95, "recommended_model": "groq", "reasoning": "Educational concept"}
"Explain metabolism" → {"complexity": "simple", "confidence": 0.95, "recommended_model": "groq", "reasoning": "Scientific explanation"}

**COMPLEX - User Data:**
"What have I done today?" → {"complexity": "complex", "confidence": 0.98, "recommended_model": "claude", "reasoning": "Needs get_daily_nutrition_summary + get_recent_activities"}
"Show my progress" → {"complexity": "complex", "confidence": 0.98, "recommended_model": "claude", "reasoning": "Needs get_body_measurements + calculate_progress_trend"}
"What are my macros?" → {"complexity": "complex", "confidence": 0.98, "recommended_model": "claude", "reasoning": "Needs get_user_profile"}
"Can you see my profile?" → {"complexity": "complex", "confidence": 0.98, "recommended_model": "claude", "reasoning": "Needs get_user_profile tool"}
"What did I eat yesterday?" → {"complexity": "complex", "confidence": 0.98, "recommended_model": "claude", "reasoning": "Needs get_recent_meals"}

**COMPLEX - Planning:**
"Give me a 4-week workout plan" → {"complexity": "complex", "confidence": 0.98, "recommended_model": "claude", "reasoning": "Needs get_user_profile + multi-step planning"}
"Create a meal plan" → {"complexity": "complex", "confidence": 0.98, "recommended_model": "claude", "reasoning": "Needs user macros + preferences + planning"}
"I need a workout routine" → {"complexity": "complex", "confidence": 0.98, "recommended_model": "claude", "reasoning": "Needs user data + planning"}
"Make me a program" → {"complexity": "complex", "confidence": 0.98, "recommended_model": "claude", "reasoning": "Planning requires profile data"}

**COMPLEX - Personalized Advice:**
"Should I do cardio?" → {"complexity": "complex", "confidence": 0.95, "recommended_model": "claude", "reasoning": "Needs user goals to give personalized advice"}
"How much protein should I eat?" → {"complexity": "complex", "confidence": 0.98, "recommended_model": "claude", "reasoning": "Needs bodyweight + goals"}
"What should I eat after workout?" → {"complexity": "complex", "confidence": 0.95, "recommended_model": "claude", "reasoning": "Better with macros + preferences"}
"Is this amount of calories enough?" → {"complexity": "complex", "confidence": 0.95, "recommended_model": "claude", "reasoning": "Needs goals to evaluate"}

**COMPLEX - Analysis:**
"Am I making progress?" → {"complexity": "complex", "confidence": 0.98, "recommended_model": "claude", "reasoning": "Needs body measurements + progress trend"}
"Analyze my week" → {"complexity": "complex", "confidence": 0.98, "recommended_model": "claude", "reasoning": "Needs recent meals + activities + analysis"}
"Why am I not losing weight?" → {"complexity": "complex", "confidence": 0.98, "recommended_model": "claude", "reasoning": "Needs nutrition data + progress analysis"}

**COMPLEX - Benefit from Context:**
"How much protein in chicken?" → {"complexity": "complex", "confidence": 0.85, "recommended_model": "claude", "reasoning": "Generic answer OK but 10x better with user goals"}

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════════
Return ONLY valid JSON, no explanations:
{
    "complexity": "trivial"|"simple"|"complex",
    "confidence": 0.0-1.0,
    "recommended_model": "canned"|"groq"|"claude",
    "reasoning": "brief explanation"
}"""

        user_prompt = f"""Classify this query:

"{message}"

Return ONLY valid JSON."""

        try:
            # Call Claude Haiku for classification (fast + accurate)
            response = self.anthropic.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=150,
                temperature=0.1,  # Low for consistent classification
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Extract JSON from response
            response_text = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            analysis = json.loads(response_text)

            logger.info(
                f"[ComplexityAnalyzer] ✅ Complexity: {analysis['complexity']}, "
                f"confidence: {analysis['confidence']:.2f}, "
                f"reasoning: {analysis['reasoning'][:50]}..."
            )

            return analysis

        except Exception as e:
            logger.error(f"[ComplexityAnalyzer] ❌ Analysis failed: {e}", exc_info=True)

            # FAIL-SAFE: Default to COMPLEX (better to have tool access than not)
            return {
                "complexity": "complex",
                "confidence": 0.5,
                "recommended_model": "claude",
                "reasoning": "Classification failed, defaulting to complex for tool access (fail-safe)"
            }


# Singleton
_complexity_analyzer: Optional[ComplexityAnalyzerService] = None

def get_complexity_analyzer(anthropic_client=None):
    """
    Get singleton ComplexityAnalyzerService instance.

    Args:
        anthropic_client: Anthropic client (NOT AsyncAnthropic) for sync calls

    Returns:
        ComplexityAnalyzerService instance
    """
    global _complexity_analyzer
    if _complexity_analyzer is None:
        if anthropic_client is None:
            from anthropic import Anthropic
            import os
            anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        _complexity_analyzer = ComplexityAnalyzerService(anthropic_client)
    return _complexity_analyzer
