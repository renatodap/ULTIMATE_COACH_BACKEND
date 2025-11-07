"""
Tests for LanguageDetector service.

Tests language detection from multiple sources with caching.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from app.services.coach.language_detector import LanguageDetector


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    return MagicMock()


@pytest.fixture
def mock_i18n():
    """Mock I18n service."""
    mock = Mock()
    mock.detect_language = Mock(return_value=("en", 0.9))
    return mock


@pytest.fixture
def mock_cache():
    """Mock cache service."""
    cache = Mock()
    cache.get = Mock(return_value=None)
    cache.set = Mock()
    return cache


@pytest.fixture
def detector(mock_supabase, mock_i18n, mock_cache):
    """Create LanguageDetector instance."""
    return LanguageDetector(mock_supabase, mock_i18n, mock_cache)


class TestLanguageDetector:
    """Tests for LanguageDetector."""

    @pytest.mark.asyncio
    async def test_detect_from_cache(self, detector, mock_cache):
        """Test detection returns cached value."""
        mock_cache.get.return_value = "es"

        result = await detector.detect("user_123", "Hello world")

        assert result == "es"
        mock_cache.get.assert_called_once_with("user_lang:user_123")

    @pytest.mark.asyncio
    async def test_detect_from_profile(self, detector, mock_supabase, mock_cache):
        """Test detection from user profile."""
        mock_cache.get.return_value = None

        mock_response = Mock()
        mock_response.data = {"language": "fr"}
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response

        result = await detector.detect("user_123", "Hello world")

        assert result == "fr"
        mock_supabase.table.assert_called_once_with("profiles")
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_from_message_high_confidence(
        self,
        detector,
        mock_supabase,
        mock_i18n,
        mock_cache
    ):
        """Test detection from message with high confidence."""
        mock_cache.get.return_value = None

        # No profile data
        mock_profile_response = Mock()
        mock_profile_response.data = None
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_profile_response

        # High confidence detection
        mock_i18n.detect_language.return_value = ("es", 0.85)

        # Mock update
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        result = await detector.detect("user_123", "Hola mundo")

        assert result == "es"
        mock_i18n.detect_language.assert_called_once_with("Hola mundo")

        # Should update profile
        update_calls = [
            call for call in mock_supabase.table.call_args_list
            if call[0][0] == "profiles"
        ]
        assert len(update_calls) >= 1

        # Should cache result
        cache_set_calls = mock_cache.set.call_args_list
        assert any("es" in str(call) for call in cache_set_calls)

    @pytest.mark.asyncio
    async def test_detect_from_message_low_confidence(
        self,
        detector,
        mock_supabase,
        mock_i18n,
        mock_cache
    ):
        """Test detection defaults to English on low confidence."""
        mock_cache.get.return_value = None

        # No profile data
        mock_profile_response = Mock()
        mock_profile_response.data = None
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_profile_response

        # Low confidence detection
        mock_i18n.detect_language.return_value = ("es", 0.5)

        result = await detector.detect("user_123", "Maybe Spanish?")

        assert result == "en"  # Should default to English

    @pytest.mark.asyncio
    async def test_detect_profile_query_error(
        self,
        detector,
        mock_supabase,
        mock_i18n,
        mock_cache
    ):
        """Test detection handles profile query errors gracefully."""
        mock_cache.get.return_value = None

        # Profile query raises error
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("DB error")

        # Should fall back to message detection
        mock_i18n.detect_language.return_value = ("en", 0.9)

        result = await detector.detect("user_123", "Hello")

        assert result == "en"

    @pytest.mark.asyncio
    async def test_detect_no_auto_update_profile(
        self,
        detector,
        mock_supabase,
        mock_i18n,
        mock_cache
    ):
        """Test detection skips profile update when disabled."""
        mock_cache.get.return_value = None

        # No profile data
        mock_profile_response = Mock()
        mock_profile_response.data = None
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_profile_response

        # High confidence detection
        mock_i18n.detect_language.return_value = ("es", 0.85)

        result = await detector.detect(
            "user_123",
            "Hola mundo",
            auto_update_profile=False
        )

        assert result == "es"

        # Should NOT update profile
        update_calls = [
            call for call in mock_supabase.table.call_args_list
            if str(call).find("update") != -1
        ]
        # Only SELECT calls should exist, no UPDATE
        assert len([c for c in mock_supabase.table.call_args_list if c[0][0] == "profiles"]) == 1

    @pytest.mark.asyncio
    async def test_detect_message_analysis_error(
        self,
        detector,
        mock_supabase,
        mock_i18n,
        mock_cache
    ):
        """Test detection defaults to English on analysis error."""
        mock_cache.get.return_value = None

        # No profile data
        mock_profile_response = Mock()
        mock_profile_response.data = None
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_profile_response

        # Detection raises error
        mock_i18n.detect_language.side_effect = Exception("Detection error")

        result = await detector.detect("user_123", "Hello")

        assert result == "en"  # Should default to English

    @pytest.mark.asyncio
    async def test_update_profile_language_success(self, detector, mock_supabase):
        """Test profile language update succeeds."""
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        # Should not raise
        await detector._update_profile_language("user_123", "es")

        mock_supabase.table.assert_called_with("profiles")

    @pytest.mark.asyncio
    async def test_update_profile_language_error(self, detector, mock_supabase):
        """Test profile language update handles errors."""
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("Update failed")

        # Should not raise, just log warning
        await detector._update_profile_language("user_123", "es")

    @pytest.mark.asyncio
    async def test_cache_ttl(self, detector, mock_cache):
        """Test cache uses 5-minute TTL."""
        await detector._set_in_cache("user_123", "es")

        mock_cache.set.assert_called_once_with("user_lang:user_123", "es", ttl=300)
