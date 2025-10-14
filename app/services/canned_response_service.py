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

        DISABLED: Canned responses are disabled because they interfere with contextual questions.
        For example, "hi. what did i eat today?" should NOT get a greeting response.
        All messages should go through the AI for proper context understanding.

        Args:
            message: User's message
            language: User's language preference

        Returns:
            Always returns None (canned responses disabled)
        """
        # DISABLED: Always return None to force AI processing
        logger.info(f"[Canned] ⏭️  Skipping canned response - all messages route to AI")
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
