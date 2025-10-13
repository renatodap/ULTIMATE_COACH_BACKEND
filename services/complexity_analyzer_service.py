"""
Complexity Analyzer Service - Smart Routing

Analyzes query complexity to route to appropriate model:
- Trivial: Canned responses (FREE, 0ms)
- Simple: Groq Llama 3.3 70B ($0.01, 500ms)
- Complex: Claude 3.5 Sonnet ($0.15, 2000ms)

This is 77% cheaper than all-Claude approach!
"""

import logging
from typing import Dict, Any
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

**SIMPLE** (50% of queries):
- Basic nutrition questions: "How much protein in chicken?"
- Simple calculations: "How many calories did I burn?"
- Straightforward advice: "What should I eat post-workout?"
- Data lookups: "Show me my stats"
These can use Groq Llama 3.3 70B with tools ($0.01, 500ms).

**COMPLEX** (20% of queries):
- Multi-step planning: "Create a 4-week training plan"
- Deep analysis: "Analyze my progress and suggest changes"
- Nuanced coaching: "I'm plateauing, what should I do?"
- Long-form responses needed
- Requires advanced reasoning
These need Claude 3.5 Sonnet ($0.15, 2000ms).

Examples:

INPUT: "hi"
OUTPUT: {"complexity": "trivial", "confidence": 0.99, "recommended_model": "canned", "reasoning": "Simple greeting - canned response"}

INPUT: "What's the protein in chicken breast?"
OUTPUT: {"complexity": "simple", "confidence": 0.9, "recommended_model": "groq", "reasoning": "Simple nutrition lookup - Groq with food database tool"}

INPUT: "I want to build muscle but I'm plateauing. Can you analyze my approach and suggest a new program?"
OUTPUT: {"complexity": "complex", "confidence": 0.95, "recommended_model": "claude", "reasoning": "Multi-step analysis and planning - needs Claude's reasoning"}

INPUT: "How many calories in a banana?"
OUTPUT: {"complexity": "simple", "confidence": 0.9, "recommended_model": "groq", "reasoning": "Simple data lookup - Groq with food search"}

INPUT: "Create a detailed meal plan for the next week that hits my macros and includes variety"
OUTPUT: {"complexity": "complex", "confidence": 0.95, "recommended_model": "claude", "reasoning": "Complex planning task - needs Claude"}

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
