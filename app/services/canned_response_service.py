"""
Canned Response Service - MULTILINGUAL

Provides instant responses for trivial queries.
Supports multiple languages via i18n service.
"""

import structlog
import re
from typing import Optional

logger = structlog.get_logger()


# Pattern → Translation Key mapping
CANNED_PATTERNS = {
    r'\b(hi|hello|hey|sup|yo|oi|hola|salut)\b': 'canned.greeting',
    r'\b(thanks|thank you|thx|ty|obrigado|gracias|merci)\b': 'canned.thanks',
    r'\b(bye|goodbye|see you|later|cya|tchau|adios|au revoir)\b': 'canned.goodbye',
    r'\b(ok|okay|got it|understood|cool|entendi|vale|d\'accord)\b': 'canned.acknowledgment',
}


class CannedResponseService:
    """
    Instant canned responses for trivial queries.

    Features:
    - Pattern matching (regex)
    - Multilingual support (via i18n)
    - Zero cost, zero latency
    """

    def __init__(self, i18n_service):
        self.i18n = i18n_service
        # Compile regex patterns for performance
        self.patterns = {
            re.compile(pattern, re.IGNORECASE): key
            for pattern, key in CANNED_PATTERNS.items()
        }

    def get_response(
        self,
        message: str,
        language: str = 'en'
    ) -> Optional[str]:
        """
        Get canned response for trivial message.

        Args:
            message: User's message
            language: User's language preference

        Returns:
            Canned response or None if no match

        Example:
            >>> canned.get_response("hi", "en")
            "What's up! 💪 Ready to CRUSH IT?"

            >>> canned.get_response("oi", "pt")
            "E aí! 💪 Pronto para ARRASAR?"
        """
        message_lower = message.lower().strip()

        # Check each pattern
        for pattern, translation_key in self.patterns.items():
            if pattern.search(message_lower):
                response = self.i18n.t(translation_key, language)
                logger.info(f"[Canned] ⚡ Matched pattern for '{message[:20]}...' → {translation_key}")
                return response

        return None


# Singleton
_canned_service: Optional[CannedResponseService] = None

def get_canned_response(i18n_service=None) -> CannedResponseService:
    """Get singleton CannedResponseService instance."""
    global _canned_service
    if _canned_service is None:
        if i18n_service is None:
            from app.services.i18n_service import get_i18n_service
            i18n_service = get_i18n_service()
        _canned_service = CannedResponseService(i18n_service)
    return _canned_service
