"""
Tests for UserProfileTool.

Tests the user profile retrieval tool including:
- Tool definition structure
- Caching behavior
- Error handling
- Database query logic
"""

import pytest
from unittest.mock import Mock, MagicMock
from app.services.tools.user_profile_tool import UserProfileTool


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_cache():
    """Mock cache service."""
    cache = Mock()
    cache.get = Mock(return_value=None)
    cache.set = Mock()
    return cache


@pytest.fixture
def user_profile_tool(mock_supabase, mock_cache):
    """Create UserProfileTool instance."""
    return UserProfileTool(mock_supabase, mock_cache)


@pytest.fixture
def sample_profile_data():
    """Sample profile data from database."""
    return {
        "id": "user_123",
        "full_name": "John Doe",
        "primary_goal": "weight_loss",
        "experience_level": "intermediate",
        "daily_calorie_goal": 2000,
        "daily_protein_goal": 150,
        "daily_carbs_goal": 200,
        "daily_fat_goal": 65,
        "unit_system": "imperial",
        "language": "en"
    }


class TestUserProfileTool:
    """Tests for UserProfileTool."""

    def test_get_definition(self, user_profile_tool):
        """Test tool definition structure."""
        definition = user_profile_tool.get_definition()

        assert definition["name"] == "get_user_profile"
        assert "profile" in definition["description"]
        assert "input_schema" in definition
        assert definition["input_schema"]["type"] == "object"

    def test_name_property(self, user_profile_tool):
        """Test name property."""
        assert user_profile_tool.name == "get_user_profile"

    @pytest.mark.asyncio
    async def test_execute_cache_hit(self, user_profile_tool, mock_cache, sample_profile_data):
        """Test execution returns cached data when available."""
        # Setup cache to return data
        mock_cache.get.return_value = sample_profile_data

        result = await user_profile_tool.execute("user_123", {})

        # Should return cached data
        assert result == sample_profile_data
        mock_cache.get.assert_called_once_with("user_profile:user_123")

    @pytest.mark.asyncio
    async def test_execute_cache_miss_success(
        self,
        user_profile_tool,
        mock_supabase,
        mock_cache,
        sample_profile_data
    ):
        """Test execution queries database on cache miss."""
        # Setup cache miss
        mock_cache.get.return_value = None

        # Setup database response
        mock_response = Mock()
        mock_response.data = sample_profile_data

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response

        result = await user_profile_tool.execute("user_123", {})

        # Verify database query
        mock_supabase.table.assert_called_once_with("profiles")

        # Verify result formatting
        assert result["full_name"] == "John Doe"
        assert result["primary_goal"] == "weight_loss"
        assert result["daily_calorie_goal"] == 2000

        # Verify caching
        mock_cache.set.assert_called_once()
        cache_call_args = mock_cache.set.call_args
        assert cache_call_args[0][0] == "user_profile:user_123"
        assert cache_call_args[1]["ttl"] == 300  # 5 minutes

    @pytest.mark.asyncio
    async def test_execute_profile_not_found(
        self,
        user_profile_tool,
        mock_supabase,
        mock_cache
    ):
        """Test execution handles missing profile."""
        # Setup cache miss
        mock_cache.get.return_value = None

        # Setup database response with no data
        mock_response = Mock()
        mock_response.data = None

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response

        result = await user_profile_tool.execute("user_123", {})

        # Should return error
        assert "error" in result
        assert result["error"] == "Profile not found"

    @pytest.mark.asyncio
    async def test_execute_database_error(
        self,
        user_profile_tool,
        mock_supabase,
        mock_cache
    ):
        """Test execution handles database errors."""
        # Setup cache miss
        mock_cache.get.return_value = None

        # Setup database to raise error
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("Database error")

        result = await user_profile_tool.execute("user_123", {})

        # Should return error
        assert "error" in result
        assert "Database error" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_formats_response_correctly(
        self,
        user_profile_tool,
        mock_supabase,
        mock_cache
    ):
        """Test execution formats response with all expected fields."""
        # Setup cache miss
        mock_cache.get.return_value = None

        # Setup database response with extra fields
        profile_with_extras = {
            "id": "user_123",
            "full_name": "John Doe",
            "primary_goal": "weight_loss",
            "experience_level": "intermediate",
            "daily_calorie_goal": 2000,
            "daily_protein_goal": 150,
            "daily_carbs_goal": 200,
            "daily_fat_goal": 65,
            "unit_system": "imperial",
            "language": "en",
            "created_at": "2024-01-01",  # Extra field
            "updated_at": "2024-01-02",  # Extra field
        }

        mock_response = Mock()
        mock_response.data = profile_with_extras

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response

        result = await user_profile_tool.execute("user_123", {})

        # Should only include expected fields
        expected_fields = {
            "full_name", "primary_goal", "experience_level",
            "daily_calorie_goal", "daily_protein_goal",
            "daily_carbs_goal", "daily_fat_goal",
            "unit_system", "language"
        }
        assert set(result.keys()) == expected_fields

    @pytest.mark.asyncio
    async def test_execute_with_default_values(
        self,
        user_profile_tool,
        mock_supabase,
        mock_cache
    ):
        """Test execution applies default values for missing fields."""
        # Setup cache miss
        mock_cache.get.return_value = None

        # Setup database response with minimal data
        minimal_profile = {
            "id": "user_123",
            "full_name": "John Doe",
            "primary_goal": "weight_loss",
            # Missing: unit_system, language
        }

        mock_response = Mock()
        mock_response.data = minimal_profile

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response

        result = await user_profile_tool.execute("user_123", {})

        # Should apply defaults
        assert result["unit_system"] == "imperial"  # Default
        assert result["language"] == "en"  # Default
