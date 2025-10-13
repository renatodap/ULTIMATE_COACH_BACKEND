"""
Complexity Analyzer Service - Smart Routing (Personalization-First)

Analyzes query complexity to route to appropriate model:
- Trivial (30%): Canned responses (FREE, 0ms) - greetings, thanks, bye
- Simple (10%): Groq Llama 3.3 70B ($0.01, 500ms) - pure definitions
- Complex (60%): Claude 3.5 Sonnet ($0.15, 2000ms) - personalized coaching

Routes 90% of queries to personalized responses (canned + Claude).
Cost: $0.00505/query vs $0.0056/query (all-Claude).
Savings: Negligible ($0.80 per 1000 queries), but optimizes for personalization.
"""

import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class ComplexityAnalyzerService:
    """
    Analyzes query complexity for smart routing.

    Uses Groq Llama 3.3 70B for fast, cheap classification.
    """

    def __init__(self, groq_client):
        self.groq = groq_client

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

        system_prompt = """You are a query complexity analyzer for an AI fitness coach.

Classify queries into three categories:

**TRIVIAL** (30% of queries):
- Single-word greetings: "hi", "hello", "hey"
- Simple acknowledgments: "thanks", "ok", "got it"
- Goodbyes: "bye", "see you later"
These should use canned responses (FREE, instant).

**SIMPLE** (10% of queries):
- Pure definitions: "What is BMR?", "Define protein", "What is a calorie?"
- Scientific terms: "Explain metabolism", "What are macros?"
- Basic concepts: "What is progressive overload?"
These use Groq Llama 3.3 70B - NO TOOL CALLING ($0.01, 500ms).
NOTE: ONLY use SIMPLE for purely educational questions with NO personalization benefit.
If question could benefit from user context (goals, preferences, stats), classify as COMPLEX.

**COMPLEX** (60% of queries):
- Queries requiring user data: "Can you see my profile?", "What are my goals?", "Show my stats"
- Multi-step planning: "Create a 4-week training plan"
- Deep analysis: "Analyze my progress and suggest changes"
- Nuanced coaching: "I'm plateauing, what should I do?"
- User-specific advice: "Should I increase my calories?" (needs user goals)
- Questions that benefit from personalization:
  - "How much protein in chicken?" → Better with context: "You need 150g daily, 300g chicken would provide 90g"
  - "What should I eat?" → Needs macros, preferences, allergies
  - "Should I do cardio?" → Needs goals, current routine
  - "How many calories should I eat?" → Needs bodyweight, goals, activity level
  - "Is this food good for me?" → Needs dietary preferences, goals
- Long-form responses needed
- Requires tool calling (get_user_profile, get_recent_meals, etc.)
These need Claude 3.5 Sonnet with tool calling ($0.15, 2000ms).
NOTE: Most fitness questions benefit from user context. When in doubt, classify as COMPLEX.

Examples:

INPUT: "hi"
OUTPUT: {"complexity": "trivial", "confidence": 0.99, "recommended_model": "canned", "reasoning": "Simple greeting - canned response"}

INPUT: "What is BMR?"
OUTPUT: {"complexity": "simple", "confidence": 0.9, "recommended_model": "groq", "reasoning": "Pure definition - no personalization benefit"}

INPUT: "Can you see my profile?"
OUTPUT: {"complexity": "complex", "confidence": 0.95, "recommended_model": "claude", "reasoning": "Requires get_user_profile tool to fetch user data"}

INPUT: "What are my macro goals?"
OUTPUT: {"complexity": "complex", "confidence": 0.95, "recommended_model": "claude", "reasoning": "Needs user data via get_user_profile tool"}

INPUT: "Show me my progress"
OUTPUT: {"complexity": "complex", "confidence": 0.95, "recommended_model": "claude", "reasoning": "Requires tools to fetch user stats and measurements"}

INPUT: "I want to build muscle but I'm plateauing. Can you analyze my approach and suggest a new program?"
OUTPUT: {"complexity": "complex", "confidence": 0.95, "recommended_model": "claude", "reasoning": "Multi-step analysis and planning - needs Claude's reasoning + tools"}

INPUT: "How much protein should I eat?"
OUTPUT: {"complexity": "complex", "confidence": 0.95, "recommended_model": "claude", "reasoning": "Needs bodyweight, goals, and activity level for personalized recommendation"}

INPUT: "Create a detailed meal plan for the next week that hits my macros and includes variety"
OUTPUT: {"complexity": "complex", "confidence": 0.95, "recommended_model": "claude", "reasoning": "Complex planning + needs user macros via tools"}

INPUT: "What should I eat after a workout?"
OUTPUT: {"complexity": "complex", "confidence": 0.9, "recommended_model": "claude", "reasoning": "Better personalized with macros, preferences, and dietary restrictions"}

INPUT: "Should I do cardio or lift weights?"
OUTPUT: {"complexity": "complex", "confidence": 0.9, "recommended_model": "claude", "reasoning": "Needs user goals, current routine, and preferences for personalized advice"}

INPUT: "How much protein is in chicken breast?"
OUTPUT: {"complexity": "complex", "confidence": 0.85, "recommended_model": "claude", "reasoning": "Can provide generic answer but 10x better with user context (daily goals, current progress)"}

INPUT: "Define progressive overload"
OUTPUT: {"complexity": "simple", "confidence": 0.95, "recommended_model": "groq", "reasoning": "Pure educational definition - no personalization needed"}

Return ONLY valid JSON:
{
    "complexity": "trivial"|"simple"|"complex",
    "confidence": 0.0-1.0,
    "recommended_model": "canned"|"groq"|"claude",
    "reasoning": "brief explanation"
}"""

        user_prompt = f"""Classify this query:

"{message}"

Return JSON classification."""

        try:
            response = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )

            response_text = response.choices[0].message.content.strip()
            analysis = json.loads(response_text)

            logger.info(
                f"[ComplexityAnalyzer] ✅ Complexity: {analysis['complexity']}, "
                f"confidence: {analysis['confidence']:.2f}"
            )

            return analysis

        except Exception as e:
            logger.error(f"[ComplexityAnalyzer] ❌ Analysis failed: {e}", exc_info=True)

            # Fallback: Default to simple (safe middle ground)
            return {
                "complexity": "simple",
                "confidence": 0.5,
                "recommended_model": "groq",
                "reasoning": "Analysis failed, defaulting to simple/groq"
            }


# Singleton
_complexity_analyzer: Optional[ComplexityAnalyzerService] = None

def get_complexity_analyzer(groq_client=None):
    """Get singleton ComplexityAnalyzerService instance."""
    global _complexity_analyzer
    if _complexity_analyzer is None:
        if groq_client is None:
            from groq import Groq
            import os
            groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        _complexity_analyzer = ComplexityAnalyzerService(groq_client)
    return _complexity_analyzer
