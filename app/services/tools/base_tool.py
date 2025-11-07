"""
Base Tool Class for Plugin Architecture

All tools inherit from BaseTool and implement:
- get_definition(): Returns tool schema for LLM
- execute(): Runs the tool logic

Benefits:
- Each tool is independently testable
- Tools can be added/removed without modifying core service
- Clear separation of concerns
- Easier maintenance and debugging
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()


class BaseTool(ABC):
    """
    Abstract base class for all AI coaching tools.

    Each tool must implement:
    - get_definition(): Tool schema for LLM
    - execute(): Tool execution logic
    """

    def __init__(self, supabase_client, cache_service=None):
        """
        Initialize tool with dependencies.

        Args:
            supabase_client: Supabase client for database access
            cache_service: Optional cache service for performance
        """
        self.supabase = supabase_client
        self.cache = cache_service
        self.logger = logger

    @abstractmethod
    def get_definition(self) -> Dict[str, Any]:
        """
        Return tool definition for LLM (Claude/OpenAI format).

        Returns:
            Dict with name, description, and input_schema

        Example:
            {
                "name": "get_user_profile",
                "description": "Get user's profile data",
                "input_schema": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }
        """
        pass

    @abstractmethod
    async def execute(self, user_id: str, params: Dict[str, Any]) -> Any:
        """
        Execute the tool with given parameters.

        Args:
            user_id: User UUID for data access
            params: Tool input parameters

        Returns:
            Tool result (any type - dict, list, str, etc.)

        Raises:
            ValueError: For invalid parameters
            Exception: For execution errors
        """
        pass

    @property
    def name(self) -> str:
        """Get tool name from definition."""
        return self.get_definition()["name"]

    def log_execution(self, tool_name: str, params: Optional[Dict] = None):
        """Log tool execution with structured logging."""
        self.logger.info(
            "tool_execution",
            tool_name=tool_name,
            params=params
        )

    def log_error(self, tool_name: str, error: Exception, params: Optional[Dict] = None):
        """Log tool errors with structured logging."""
        self.logger.error(
            "tool_execution_error",
            tool_name=tool_name,
            error=str(error),
            error_type=type(error).__name__,
            params=params,
            exc_info=True
        )

    async def get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get value from cache if cache service is available."""
        if self.cache:
            return self.cache.get(cache_key)
        return None

    async def set_in_cache(self, cache_key: str, value: Any, ttl: int = 300):
        """Set value in cache if cache service is available."""
        if self.cache:
            self.cache.set(cache_key, value, ttl=ttl)
