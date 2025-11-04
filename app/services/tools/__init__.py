"""
Tools Package - AI Coaching Tool Plugin System

Provides modular, testable tools for AI coaching.

Architecture:
- BaseTool: Abstract base class for all tools
- ToolRegistry: Central tool management and execution
- Individual tool classes: One file per tool

Benefits:
- Independent testing of each tool
- Easy to add/remove tools
- Clear separation of concerns
- Better maintainability

Usage:
    from app.services.tools import create_tool_registry

    registry = create_tool_registry(supabase_client, cache_service)
    result = await registry.execute("get_user_profile", user_id, params)
"""

from app.services.tools.base_tool import BaseTool
from app.services.tools.tool_registry import ToolRegistry
from app.services.tools.user_profile_tool import UserProfileTool
from app.services.tools.daily_nutrition_summary_tool import DailyNutritionSummaryTool
from app.services.tools.recent_meals_tool import RecentMealsTool
from app.services.tools.recent_activities_tool import RecentActivitiesTool
from app.services.tools.body_measurements_tool import BodyMeasurementsTool
from app.services.tools.progress_trend_tool import ProgressTrendTool

__all__ = [
    "BaseTool",
    "ToolRegistry",
    "UserProfileTool",
    "DailyNutritionSummaryTool",
    "RecentMealsTool",
    "RecentActivitiesTool",
    "BodyMeasurementsTool",
    "ProgressTrendTool",
    "create_tool_registry",
]


def create_tool_registry(supabase_client, cache_service=None) -> ToolRegistry:
    """
    Create and initialize tool registry with all available tools.

    This factory function instantiates all tools and registers them
    in a single registry for easy access.

    Args:
        supabase_client: Supabase client for database access
        cache_service: Optional cache service for performance

    Returns:
        Initialized ToolRegistry with all tools registered

    Example:
        >>> registry = create_tool_registry(supabase, cache)
        >>> tools = registry.get_all_definitions()  # For LLM
        >>> result = await registry.execute("get_user_profile", user_id, {})
    """
    registry = ToolRegistry(supabase_client, cache_service)

    # Register all core tools (extracted from monolithic tool_service.py)
    tools = [
        # User & Profile
        UserProfileTool(supabase_client, cache_service),

        # Nutrition
        DailyNutritionSummaryTool(supabase_client, cache_service),
        RecentMealsTool(supabase_client, cache_service),

        # Activity & Progress
        RecentActivitiesTool(supabase_client, cache_service),
        BodyMeasurementsTool(supabase_client, cache_service),
        ProgressTrendTool(supabase_client, cache_service),

        # TODO: Remaining tools to extract from original tool_service.py:
        # TrainingVolumeTool(supabase_client, cache_service),
        # FoodSearchTool(supabase_client, cache_service),
        # MealNutritionCalculatorTool(supabase_client, cache_service),
        # MealAdjustmentsTool(supabase_client, cache_service),
        # ActivityCaloriesTool(supabase_client, cache_service),
        # QuickMealLogTool(supabase_client, cache_service),
        # SemanticSearchTool(supabase_client, cache_service),
        # UpdateMealTool, DeleteMealTool, etc. (8 more action tools)
    ]

    registry.register_all(tools)

    return registry
