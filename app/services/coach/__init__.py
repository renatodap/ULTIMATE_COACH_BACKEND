"""
Coach Services Package

Modular services extracted from unified_coach_service.py (2,658 lines).

Services:
- LanguageDetector: Language detection and management ✅
- SystemPromptBuilder: System prompt construction ✅
- ConversationManager: Conversation operations ✅
- LogHandler: Log mode processing (TODO)
- ChatHandler: Chat mode processing (TODO)
- UnifiedCoachRouter: Main coordinator (TODO)

Usage:
    from app.services.coach import LanguageDetector, SystemPromptBuilder, ConversationManager

    detector = LanguageDetector(supabase, i18n, cache)
    language = await detector.detect(user_id, message)

    builder = SystemPromptBuilder(supabase)
    prompt, version = await builder.build(user_id, language)

    manager = ConversationManager(supabase)
    conversation = await manager.get_or_create(user_id)
"""

from app.services.coach.language_detector import LanguageDetector
from app.services.coach.system_prompt_builder import SystemPromptBuilder
from app.services.coach.conversation_manager import ConversationManager

__all__ = [
    "LanguageDetector",
    "SystemPromptBuilder",
    "ConversationManager",
]
