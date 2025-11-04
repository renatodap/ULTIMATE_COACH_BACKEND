"""
Language Detector Service

Detects user's preferred language from multiple sources.

Priority:
1. User profile (cached)
2. Message analysis (auto-detect)
3. Default to English

Features:
- Caching (5min TTL)
- Auto-detection with confidence threshold
- Profile update on high-confidence detection
- Fallback to English
"""

import structlog
from typing import Optional, Tuple

logger = structlog.get_logger()


class LanguageDetector:
    """
    Detects and manages user language preferences.

    Provides intelligent language detection with caching and
    automatic profile updates.
    """

    def __init__(self, supabase_client, i18n_service, cache_service):
        """
        Initialize language detector.

        Args:
            supabase_client: Supabase client for database access
            i18n_service: I18n service for language detection
            cache_service: Cache service for performance
        """
        self.supabase = supabase_client
        self.i18n = i18n_service
        self.cache = cache_service
        self.logger = logger

    async def detect(
        self,
        user_id: str,
        message: str,
        auto_update_profile: bool = True
    ) -> str:
        """
        Detect user's preferred language.

        Checks:
        1. Cache (5min TTL)
        2. User profile
        3. Message analysis (with confidence threshold)
        4. Default to English

        Args:
            user_id: User UUID
            message: User's message for analysis
            auto_update_profile: Whether to update profile on detection

        Returns:
            Language code (e.g., "en", "es", "fr")
        """
        # Check cache first (fast path)
        cached_lang = await self._get_from_cache(user_id)
        if cached_lang:
            self.logger.debug(
                "language_cache_hit",
                user_id=user_id,
                language=cached_lang
            )
            return cached_lang

        # Check user profile
        profile_lang = await self._get_profile_language(user_id)
        if profile_lang:
            # Cache for next time
            await self._set_in_cache(user_id, profile_lang)
            self.logger.info(
                "language_from_profile",
                user_id=user_id,
                language=profile_lang
            )
            return profile_lang

        # Auto-detect from message
        detected_lang = await self._detect_from_message(
            user_id,
            message,
            auto_update_profile
        )

        return detected_lang

    async def _get_from_cache(self, user_id: str) -> Optional[str]:
        """Get language from cache."""
        cache_key = f"user_lang:{user_id}"
        return self.cache.get(cache_key)

    async def _set_in_cache(self, user_id: str, language: str, ttl: int = 300):
        """Set language in cache (5min TTL)."""
        cache_key = f"user_lang:{user_id}"
        self.cache.set(cache_key, language, ttl=ttl)

    async def _get_profile_language(self, user_id: str) -> Optional[str]:
        """
        Get language from user profile.

        Returns:
            Language code or None if not found
        """
        try:
            result = self.supabase.table("profiles")\
                .select("language")\
                .eq("id", user_id)\
                .single()\
                .execute()

            if result.data and result.data.get("language"):
                return result.data["language"]

        except Exception as e:
            self.logger.warning(
                "profile_language_query_failed",
                user_id=user_id,
                error=str(e)
            )

        return None

    async def _detect_from_message(
        self,
        user_id: str,
        message: str,
        update_profile: bool = True
    ) -> str:
        """
        Detect language from message content.

        Uses I18n service for detection. If confidence > 0.7,
        updates user profile and cache.

        Args:
            user_id: User UUID
            message: Message to analyze
            update_profile: Whether to update profile on high confidence

        Returns:
            Detected language code or 'en' default
        """
        try:
            detected_lang, confidence = self.i18n.detect_language(message)

            self.logger.info(
                "language_detected",
                user_id=user_id,
                language=detected_lang,
                confidence=confidence
            )

            # High confidence detection
            if confidence > 0.7:
                # Update profile if enabled
                if update_profile:
                    await self._update_profile_language(user_id, detected_lang)

                # Cache the result
                await self._set_in_cache(user_id, detected_lang)

                return detected_lang

            # Low confidence - default to English
            self.logger.info(
                "language_detection_low_confidence",
                user_id=user_id,
                detected=detected_lang,
                confidence=confidence,
                defaulting_to="en"
            )
            return 'en'

        except Exception as e:
            self.logger.error(
                "language_detection_failed",
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            return 'en'

    async def _update_profile_language(self, user_id: str, language: str):
        """
        Update user profile with detected language.

        Args:
            user_id: User UUID
            language: Language code to set
        """
        try:
            self.supabase.table("profiles").update({
                "language": language
            }).eq("id", user_id).execute()

            self.logger.info(
                "profile_language_updated",
                user_id=user_id,
                language=language
            )

        except Exception as e:
            self.logger.warning(
                "profile_language_update_failed",
                user_id=user_id,
                language=language,
                error=str(e)
            )


# Factory function for easy initialization
def get_language_detector(supabase_client, i18n_service, cache_service):
    """
    Create LanguageDetector instance.

    Args:
        supabase_client: Supabase client
        i18n_service: I18n service
        cache_service: Cache service

    Returns:
        LanguageDetector instance
    """
    return LanguageDetector(supabase_client, i18n_service, cache_service)
