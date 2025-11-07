"""
Tests for BaseTool abstract class.

Tests the foundational tool infrastructure including:
- Tool initialization
- Caching helpers
- Logging helpers
- Abstract method enforcement
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from app.services.tools.base_tool import BaseTool


class ConcreteTestTool(BaseTool):
    """Concrete implementation for testing BaseTool."""

    def get_definition(self):
        return {
            "name": "test_tool",
            "description": "A test tool",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

    async def execute(self, user_id: str, params: dict):
        return {"success": True, "user_id": user_id}


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    return Mock()


@pytest.fixture
def mock_cache():
    """Mock cache service."""
    cache = Mock()
    cache.get = Mock(return_value=None)
    cache.set = Mock()
    return cache


@pytest.fixture
def test_tool(mock_supabase, mock_cache):
    """Create test tool instance."""
    return ConcreteTestTool(mock_supabase, mock_cache)


class TestBaseTool:
    """Tests for BaseTool class."""

    def test_initialization(self, test_tool, mock_supabase, mock_cache):
        """Test tool initializes with dependencies."""
        assert test_tool.supabase == mock_supabase
        assert test_tool.cache == mock_cache
        assert test_tool.logger is not None

    def test_name_property(self, test_tool):
        """Test name property returns tool name from definition."""
        assert test_tool.name == "test_tool"

    def test_get_definition_abstract(self, mock_supabase):
        """Test get_definition must be implemented."""
        with pytest.raises(TypeError):
            # Should raise TypeError because get_definition is not implemented
            class IncompleteTool(BaseTool):
                async def execute(self, user_id, params):
                    pass

            IncompleteTool(mock_supabase)

    def test_execute_abstract(self, mock_supabase):
        """Test execute must be implemented."""
        with pytest.raises(TypeError):
            # Should raise TypeError because execute is not implemented
            class IncompleteTool(BaseTool):
                def get_definition(self):
                    return {"name": "test"}

            IncompleteTool(mock_supabase)

    def test_log_execution(self, test_tool):
        """Test execution logging."""
        # Should not raise any errors
        test_tool.log_execution("test_tool", {"param": "value"})

    def test_log_error(self, test_tool):
        """Test error logging."""
        error = ValueError("Test error")
        # Should not raise any errors
        test_tool.log_error("test_tool", error, {"param": "value"})

    @pytest.mark.asyncio
    async def test_get_from_cache_with_cache(self, test_tool, mock_cache):
        """Test cache retrieval when cache is available."""
        mock_cache.get.return_value = {"cached": True}
        result = await test_tool.get_from_cache("test_key")
        assert result == {"cached": True}
        mock_cache.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_from_cache_without_cache(self, mock_supabase):
        """Test cache retrieval when cache is not available."""
        tool = ConcreteTestTool(mock_supabase, cache_service=None)
        result = await tool.get_from_cache("test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_in_cache_with_cache(self, test_tool, mock_cache):
        """Test cache setting when cache is available."""
        await test_tool.set_in_cache("test_key", {"data": "value"}, ttl=300)
        mock_cache.set.assert_called_once_with("test_key", {"data": "value"}, ttl=300)

    @pytest.mark.asyncio
    async def test_set_in_cache_without_cache(self, mock_supabase):
        """Test cache setting when cache is not available."""
        tool = ConcreteTestTool(mock_supabase, cache_service=None)
        # Should not raise any errors
        await tool.set_in_cache("test_key", {"data": "value"})

    @pytest.mark.asyncio
    async def test_execute_implementation(self, test_tool):
        """Test concrete execute implementation."""
        result = await test_tool.execute("user_123", {"param": "value"})
        assert result == {"success": True, "user_id": "user_123"}
