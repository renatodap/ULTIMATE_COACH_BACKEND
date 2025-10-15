"""
Internationalization Service

Handles translations for:
- Canned responses
- System messages
- Error messages
- Log confirmations

Uses database translation_cache with fallback to English.
Auto-detects user language from first message.
"""

import logging
from typing import Optional, Dict, Any
from functools import lru_cache
import langdetect

logger = logging.getLogger(__name__)


class I18nService:
    """
    Internationalization service.

    Features:
    - Auto language detection from text
    - Translation cache (database + in-memory LRU)
    - Fallback to English
    - Parameter substitution
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        # In-memory cache for hot translations
        self._cache: Dict[str, Dict[str, str]] = {}
        self._load_common_translations()

    def _load_common_translations(self):
        """Preload common translations into memory cache."""
        try:
            # Load all verified translations
            result = self.supabase.table("translation_cache")\
                .select("*")\
                .eq("verified", True)\
                .execute()

            if result.data:
                for row in result.data:
                    key = row["translation_key"]
                    lang = row["language"]
                    text = row["translated_text"]

                    if key not in self._cache:
                        self._cache[key] = {}
                    self._cache[key][lang] = text

                logger.info(f"[I18n] ✅ Loaded {len(result.data)} verified translations into cache")
        except Exception as e:
            logger.error(f"[I18n] ❌ Failed to load translation cache: {e}")

    def detect_language(self, text: str) -> tuple[str, float]:
        """
        Auto-detect language from text.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (language_code, confidence)

        Example:
            >>> i18n.detect_language("Olá! Como vai?")
            ('pt', 0.95)
        """
        if not text or len(text.strip()) < 10:
            return ('en', 0.5)  # Default to English for short text

        try:
            lang = langdetect.detect(text)
            # langdetect doesn't provide confidence, estimate based on text length
            confidence = min(0.99, 0.7 + (len(text) / 200))

            logger.debug(f"[I18n] Detected language: {lang} (confidence: {confidence:.2f})")
            return (lang, confidence)
        except Exception as e:
            logger.warning(f"[I18n] Language detection failed: {e}")
            return ('en', 0.5)

    def t(
        self,
        key: str,
        language: str = 'en',
        params: Optional[Dict[str, Any]] = None,
        fallback: Optional[str] = None
    ) -> str:
        """
        Translate a key to specified language.

        Args:
            key: Translation key (e.g., 'canned.greeting')
            language: Target language code
            params: Parameters for substitution (e.g., {'calories': 450})
            fallback: Fallback text if translation not found

        Returns:
            Translated text with parameters substituted

        Example:
            >>> i18n.t('log.meal_confirmed', 'en', {'calories': 450, 'protein': 35})
            '✅ Meal logged! 450 cal, 35g protein. FUEL THE MACHINE! 🍽️'
        """
        # Try memory cache first
        translation = None
        if key in self._cache and language in self._cache[key]:
            translation = self._cache[key][language]

        # Fallback to English in memory cache
        if not translation and key in self._cache and 'en' in self._cache[key]:
            translation = self._cache[key]['en']

        # Query database if not in memory cache
        if not translation:
            try:
                # Try requested language
                result = self.supabase.table("translation_cache")\
                    .select("translated_text")\
                    .eq("translation_key", key)\
                    .eq("language", language)\
                    .limit(1)\
                    .execute()

                if result.data:
                    translation = result.data[0]["translated_text"]
                else:
                    # Fallback to English
                    result = self.supabase.table("translation_cache")\
                        .select("translated_text")\
                        .eq("translation_key", key)\
                        .eq("language", "en")\
                        .limit(1)\
                        .execute()

                    if result.data:
                        translation = result.data[0]["translated_text"]
                        logger.warning(f"[I18n] Translation not found for {key} in {language}, using English")
            except Exception as e:
                logger.error(f"[I18n] Database query failed for {key}: {e}")

        # Ultimate fallback
        if not translation:
            translation = fallback or key
            logger.warning(f"[I18n] No translation found for {key}, using fallback: {translation}")

        # Substitute parameters
        if params:
            for param_key, param_value in params.items():
                translation = translation.replace(f"{{{param_key}}}", str(param_value))

        return translation

    async def add_translation(
        self,
        key: str,
        language: str,
        text: str,
        translator: str = 'manual',
        verified: bool = False
    ) -> bool:
        """
        Add a new translation to the database and cache.

        Args:
            key: Translation key
            language: Language code
            text: Translated text
            translator: Translation source ('manual', 'deepl', 'google')
            verified: Whether translation is verified by human

        Returns:
            True if successful
        """
        try:
            # Insert or update database
            self.supabase.table("translation_cache").upsert({
                "translation_key": key,
                "language": language,
                "translated_text": text,
                "translator": translator,
                "verified": verified
            }).execute()

            # Update memory cache
            if key not in self._cache:
                self._cache[key] = {}
            self._cache[key][language] = text

            logger.info(f"[I18n] ✅ Added translation: {key} ({language})")
            return True
        except Exception as e:
            logger.error(f"[I18n] ❌ Failed to add translation: {e}")
            return False


# Singleton
_i18n_service: Optional[I18nService] = None

def get_i18n_service(supabase_client=None) -> I18nService:
    """Get singleton I18nService instance."""
    global _i18n_service
    if _i18n_service is None:
        if supabase_client is None:
            from app.services.supabase_service import get_service_client
            supabase_client = get_service_client()
        _i18n_service = I18nService(supabase_client)
    return _i18n_service
