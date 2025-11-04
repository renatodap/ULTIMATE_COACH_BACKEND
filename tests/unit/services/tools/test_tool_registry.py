"""
Tests for ToolRegistry.

Tests the tool registration, discovery, and execution system.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from app.services.tools.tool_registry import ToolRegistry
from app.services.tools.base_tool import BaseTool


class MockTool(BaseTool):
    """Mock tool for testing."""

    def __init__(self, name: str, supabase_client, cache_service=None):
        super().__init__(supabase_client, cache_service)
        self._name = name

    def get_definition(self):
        return {
            "name": self._name,
            "description": f"Mock tool {self._name}",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

    async def execute(self, user_id: str, params: dict):
        return {"tool": self._name, "user_id": user_id, "params": params}


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    return Mock()


@pytest.fixture
def registry(mock_supabase):
    """Create empty registry."""
    return ToolRegistry(mock_supabase)


@pytest.fixture
def tool1(mock_supabase):
    """Create first mock tool."""
    return MockTool("tool_one", mock_supabase)


@pytest.fixture
def tool2(mock_supabase):
    """Create second mock tool."""
    return MockTool("tool_two", mock_supabase)


class TestToolRegistry:
    """Tests for ToolRegistry class."""

    def test_initialization(self, registry, mock_supabase):
        """Test registry initializes correctly."""
        assert registry.supabase == mock_supabase
        assert len(registry) == 0

    def test_register_tool(self, registry, tool1):
        """Test registering a single tool."""
        registry.register(tool1)
        assert len(registry) == 1
        assert "tool_one" in registry
        assert registry.get_tool("tool_one") == tool1

    def test_register_duplicate_raises_error(self, registry, tool1, mock_supabase):
        """Test registering duplicate tool raises ValueError."""
        registry.register(tool1)
        duplicate_tool = MockTool("tool_one", mock_supabase)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(duplicate_tool)

    def test_register_all(self, registry, tool1, tool2):
        """Test registering multiple tools at once."""
        registry.register_all([tool1, tool2])
        assert len(registry) == 2
        assert "tool_one" in registry
        assert "tool_two" in registry

    def test_get_tool_exists(self, registry, tool1):
        """Test getting existing tool."""
        registry.register(tool1)
        retrieved = registry.get_tool("tool_one")
        assert retrieved == tool1

    def test_get_tool_not_exists(self, registry):
        """Test getting non-existent tool returns None."""
        result = registry.get_tool("nonexistent")
        assert result is None

    def test_get_all_definitions(self, registry, tool1, tool2):
        """Test getting all tool definitions."""
        registry.register_all([tool1, tool2])
        definitions = registry.get_all_definitions()

        assert len(definitions) == 2
        assert definitions[0]["name"] == "tool_one"
        assert definitions[1]["name"] == "tool_two"

    def test_get_all_tool_names(self, registry, tool1, tool2):
        """Test getting all tool names."""
        registry.register_all([tool1, tool2])
        names = registry.get_all_tool_names()

        assert len(names) == 2
        assert "tool_one" in names
        assert "tool_two" in names

    @pytest.mark.asyncio
    async def test_execute_existing_tool(self, registry, tool1):
        """Test executing registered tool."""
        registry.register(tool1)
        result = await registry.execute("tool_one", "user_123", {"param": "value"})

        assert result == {
            "tool": "tool_one",
            "user_id": "user_123",
            "params": {"param": "value"}
        }

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self, registry):
        """Test executing non-existent tool raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await registry.execute("nonexistent", "user_123", {})

    @pytest.mark.asyncio
    async def test_execute_tool_error_propagates(self, registry, mock_supabase):
        """Test tool execution errors are propagated."""
        class ErrorTool(BaseTool):
            def get_definition(self):
                return {"name": "error_tool", "description": "Fails"}

            async def execute(self, user_id, params):
                raise RuntimeError("Tool failed")

        error_tool = ErrorTool(mock_supabase)
        registry.register(error_tool)

        with pytest.raises(RuntimeError, match="Tool failed"):
            await registry.execute("error_tool", "user_123", {})

    def test_len(self, registry, tool1, tool2):
        """Test __len__ returns tool count."""
        assert len(registry) == 0
        registry.register(tool1)
        assert len(registry) == 1
        registry.register(tool2)
        assert len(registry) == 2

    def test_contains(self, registry, tool1):
        """Test __contains__ checks tool existence."""
        assert "tool_one" not in registry
        registry.register(tool1)
        assert "tool_one" in registry

    def test_repr(self, registry, tool1, tool2):
        """Test __repr__ shows tool count and names."""
        registry.register_all([tool1, tool2])
        repr_str = repr(registry)

        assert "ToolRegistry" in repr_str
        assert "2 tools" in repr_str
        assert "tool_one" in repr_str
        assert "tool_two" in repr_str
