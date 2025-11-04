"""
Coach Services Package

Modular services extracted from unified_coach_service.py (2,658 lines).

Services:
- LanguageDetector: Language detection and management
- SystemPromptBuilder: System prompt construction (TODO)
- ConversationManager: Conversation operations (TODO)
- LogHandler: Log mode processing (TODO)
- ChatHandler: Chat mode processing (TODO)
- UnifiedCoachRouter: Main coordinator (TODO)

Usage:
    from app.services.coach import get_language_detector

    detector = get_language_detector(supabase, i18n, cache)
    language = await detector.detect(user_id, message)
"""

from app.services.coach.language_detector import (
    LanguageDetector,
    get_language_detector
)

__all__ = [
    "LanguageDetector",
    "get_language_detector",
]
