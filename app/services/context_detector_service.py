"""
Context Detector Service - Safety Intelligence

Detects special contexts that require adapted coaching responses:
- Injury/pain mentions → Healing-focused response
- Rest day → Recovery-focused response
- Under-eating → Fueling-focused response
- Over-training → Rest-focused response

5% of interactions need this - the rest get FULL INTENSITY!
"""

import logging
from typing import Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


# Pattern matching for context detection
INJURY_PATTERNS = [
    r'\b(hurt|pain|painful|sore|injured|injury|strain|sprain|tear|torn)\b',
    r'\b(doctor|physical therapy|pt|chiropractor)\b',
    r'\b(cant (walk|run|lift)|can\'t (walk|run|lift))\b'
]

REST_PATTERNS = [
    r'\b(rest day|recovery day|off day|taking a break)\b',
    r'\b(feeling tired|exhausted|burned out|need rest)\b',
    r'\b(taking it easy|light (day|workout))\b'
]

UNDEREATING_PATTERNS = [
    r'\b(not hungry|skipping (meals|breakfast|lunch|dinner))\b',
    r'\b(eating very little|barely eating|not eating enough)\b',
    r'\b(cutting calories|very low calorie)\b'
]

OVERTRAINING_PATTERNS = [
    r'\b(training every day|no rest days|7 days a week)\b',
    r'\b(constant(ly)? sore|always tired|never recover)\b',
    r'\b(can\'t sleep|insomnia|poor sleep)\b'
]


class ContextDetectorService:
    """
    Detects special contexts that require coaching adaptation.

    Prevents injury encouragement and promotes smart training.
    """

    def __init__(self):
        # Compile patterns for performance
        self.injury_re = [re.compile(p, re.IGNORECASE) for p in INJURY_PATTERNS]
        self.rest_re = [re.compile(p, re.IGNORECASE) for p in REST_PATTERNS]
        self.undereating_re = [re.compile(p, re.IGNORECASE) for p in UNDEREATING_PATTERNS]
        self.overtraining_re = [re.compile(p, re.IGNORECASE) for p in OVERTRAINING_PATTERNS]

    async def detect_context(
        self,
        user_id: str,
        message: str,
        recent_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect special context from message and recent user data.

        Args:
            user_id: User UUID
            message: Current user message
            recent_data: Recent meals/activities for pattern detection

        Returns:
            {
                "context_type": "injury" | "rest" | "undereating" | "overtraining" | "normal",
                "adaptation_needed": bool,
                "reasoning": str,
                "confidence": float
            }
        """
        message_lower = message.lower()

        # Check for injury mentions
        injury_matches = sum(1 for pattern in self.injury_re if pattern.search(message_lower))
        if injury_matches > 0:
            logger.info(f"[ContextDetector] 🏥 Injury context detected for user {user_id[:8]}...")
            return {
                "context_type": "injury",
                "adaptation_needed": True,
                "reasoning": "User mentioned pain/injury - prioritize healing",
                "confidence": min(1.0, injury_matches * 0.4)
            }

        # Check for rest day mentions
        rest_matches = sum(1 for pattern in self.rest_re if pattern.search(message_lower))
        if rest_matches > 0:
            logger.info(f"[ContextDetector] 😴 Rest context detected for user {user_id[:8]}...")
            return {
                "context_type": "rest",
                "adaptation_needed": True,
                "reasoning": "User is taking rest day - encourage recovery",
                "confidence": min(1.0, rest_matches * 0.4)
            }

        # Check for under-eating mentions
        undereating_matches = sum(1 for pattern in self.undereating_re if pattern.search(message_lower))
        if undereating_matches > 0:
            logger.info(f"[ContextDetector] 🍽️ Under-eating context detected for user {user_id[:8]}...")
            return {
                "context_type": "undereating",
                "adaptation_needed": True,
                "reasoning": "User may be under-eating - encourage proper fueling",
                "confidence": min(1.0, undereating_matches * 0.4)
            }

        # Check for over-training mentions
        overtraining_matches = sum(1 for pattern in self.overtraining_re if pattern.search(message_lower))
        if overtraining_matches > 0:
            logger.info(f"[ContextDetector] 😰 Over-training context detected for user {user_id[:8]}...")
            return {
                "context_type": "overtraining",
                "adaptation_needed": True,
                "reasoning": "User may be over-training - encourage recovery",
                "confidence": min(1.0, overtraining_matches * 0.4)
            }

        # TODO: Add data-driven detection using recent_data
        # Example: Check if user has 7+ consecutive high-intensity days

        # Normal context - FULL INTENSITY MODE
        return {
            "context_type": "normal",
            "adaptation_needed": False,
            "reasoning": "No special context detected - full intensity coaching",
            "confidence": 1.0
        }


# Singleton
_context_detector: Optional[ContextDetectorService] = None

def get_context_detector() -> ContextDetectorService:
    """Get singleton ContextDetectorService instance."""
    global _context_detector
    if _context_detector is None:
        _context_detector = ContextDetectorService()
    return _context_detector
