"""
Tool Registry - Plugin Management System

Manages registration and discovery of all AI coaching tools.

Benefits:
- Central tool management
- Easy to add/remove tools
- Automatic tool definition generation
- Type-safe tool execution

Usage:
    registry = ToolRegistry(supabase_client, cache_service)
    tools = registry.get_all_definitions()  # For LLM
    result = await registry.execute("get_user_profile", params, user_id)
"""

from typing import Dict, Any, List, Optional
import structlog
from app.services.tools.base_tool import BaseTool

logger = structlog.get_logger()


class ToolRegistry:
    """
    Central registry for all AI coaching tools.

    Handles tool registration, discovery, and execution.
    """

    def __init__(self, supabase_client, cache_service=None):
        """
        Initialize registry with dependencies.

        Args:
            supabase_client: Supabase client for database access
            cache_service: Optional cache service for performance
        """
        self.supabase = supabase_client
        self.cache = cache_service
        self._tools: Dict[str, BaseTool] = {}
        self.logger = logger

    def register(self, tool: BaseTool):
        """
        Register a tool in the registry.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If tool with same name already registered
        """
        tool_name = tool.name
        if tool_name in self._tools:
            raise ValueError(f"Tool '{tool_name}' is already registered")

        self._tools[tool_name] = tool
        self.logger.debug("tool_registered", tool_name=tool_name)

    def register_all(self, tools: List[BaseTool]):
        """
        Register multiple tools at once.

        Args:
            tools: List of tool instances to register
        """
        for tool in tools:
            self.register(tool)

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.

        Args:
            tool_name: Name of tool to retrieve

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(tool_name)

    def get_all_definitions(self) -> List[Dict[str, Any]]:
        """
        Get all tool definitions for LLM.

        Returns:
            List of tool definitions in Claude/OpenAI format
        """
        return [tool.get_definition() for tool in self._tools.values()]

    def get_all_tool_names(self) -> List[str]:
        """
        Get names of all registered tools.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    async def execute(
        self,
        tool_name: str,
        user_id: str,
        params: Dict[str, Any]
    ) -> Any:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of tool to execute
            user_id: User UUID for data access
            params: Tool input parameters

        Returns:
            Tool result

        Raises:
            ValueError: If tool not found
        """
        tool = self.get_tool(tool_name)
        if not tool:
            self.logger.error("tool_not_found", tool_name=tool_name)
            raise ValueError(f"Unknown tool: {tool_name}")

        self.logger.info("tool_executing", tool_name=tool_name, user_id=user_id)

        try:
            result = await tool.execute(user_id, params)
            self.logger.info("tool_executed", tool_name=tool_name, user_id=user_id)
            return result
        except Exception as e:
            self.logger.error(
                "tool_execution_failed",
                tool_name=tool_name,
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            raise

    def __len__(self) -> int:
        """Return number of registered tools."""
        return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        """Check if tool is registered."""
        return tool_name in self._tools

    def __repr__(self) -> str:
        """Return string representation."""
        tools = ", ".join(self._tools.keys())
        return f"ToolRegistry({len(self)} tools: {tools})"
