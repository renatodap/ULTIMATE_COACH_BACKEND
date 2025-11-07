"""
Query Patterns - Standardized Database Query Builders

Eliminates query pattern duplication across the codebase.

Problem: Same JOIN patterns repeated 5+ times in different services
- N+1 query bugs when JOIN forgotten in one place
- Inconsistent query structure
- Hard to maintain

Solution: Centralized query pattern builders
- Single source of truth for each query pattern
- Type-safe query construction
- Easy to update in one place

Usage:
    from app.database.query_patterns import QueryPatterns

    # Instead of:
    # result = supabase.table("meals").select("*, meal_items(*, foods(name, brand_name))").execute()

    # Use:
    result = supabase.table("meals").select(
        QueryPatterns.meals_with_items_and_foods()
    ).execute()
"""

from typing import Dict, Any


class QueryPatterns:
    """
    Centralized query patterns for consistent database queries.

    All patterns return the SELECT clause string for use with Supabase.
    """

    # ==========================================================================
    # MEAL QUERIES
    # ==========================================================================

    @staticmethod
    def meals_with_items_and_foods() -> str:
        """
        Meals with nested meal items and food details.

        Returns meals with:
        - All meal fields
        - Nested meal_items with all fields
        - Nested foods with name and brand_name

        Usage:
            supabase.table("meals").select(
                QueryPatterns.meals_with_items_and_foods()
            ).execute()
        """
        return "*, meal_items(*, foods(name, brand_name))"

    @staticmethod
    def meals_basic() -> str:
        """
        Meals with basic fields only (no items).

        Returns:
            SELECT clause for meal summaries
        """
        return "id, name, meal_type, logged_at, total_calories, total_protein_g, total_carbs_g, total_fat_g, notes"

    @staticmethod
    def meal_items_with_food() -> str:
        """
        Meal items with food details.

        Usage:
            supabase.table("meal_items").select(
                QueryPatterns.meal_items_with_food()
            ).execute()
        """
        return "*, foods(name, brand_name, calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g)"

    # ==========================================================================
    # ACTIVITY QUERIES
    # ==========================================================================

    @staticmethod
    def activities_full() -> str:
        """
        Activities with all fields including metrics.

        Returns:
            SELECT clause for full activity data
        """
        return "*"

    @staticmethod
    def activities_summary() -> str:
        """
        Activities with summary fields only.

        Returns:
            SELECT clause for activity summaries
        """
        return "id, activity_name, category, start_time, end_time, duration_minutes, calories_burned, intensity_mets, notes"

    # ==========================================================================
    # BODY METRICS QUERIES
    # ==========================================================================

    @staticmethod
    def body_metrics_full() -> str:
        """
        Body metrics with all fields.

        Returns:
            SELECT clause for full body metrics
        """
        return "id, user_id, recorded_at, weight_kg, body_fat_percentage, notes, created_at"

    @staticmethod
    def body_metrics_summary() -> str:
        """
        Body metrics with essential fields.

        Returns:
            SELECT clause for body metrics summaries
        """
        return "id, recorded_at, weight_kg, body_fat_percentage"

    # ==========================================================================
    # COACH/CONVERSATION QUERIES
    # ==========================================================================

    @staticmethod
    def conversations_with_messages() -> str:
        """
        Conversations with nested messages.

        Returns:
            SELECT clause for conversations with full message history
        """
        return "*, coach_messages(id, role, content, created_at, metadata)"

    @staticmethod
    def messages_basic() -> str:
        """
        Messages with basic fields.

        Returns:
            SELECT clause for message list
        """
        return "id, conversation_id, role, content, created_at"

    # ==========================================================================
    # PROFILE QUERIES
    # ==========================================================================

    @staticmethod
    def profile_full() -> str:
        """
        Full user profile.

        Returns:
            SELECT clause for complete profile
        """
        return "*"

    @staticmethod
    def profile_essential() -> str:
        """
        Essential profile fields for coaching.

        Returns:
            SELECT clause for essential profile data
        """
        return """
            id, full_name, email, primary_goal, experience_level,
            daily_calorie_goal, daily_protein_goal, daily_carbs_goal, daily_fat_goal,
            unit_system, language, timezone
        """

    # ==========================================================================
    # PROGRAM QUERIES
    # ==========================================================================

    @staticmethod
    def programs_with_weeks() -> str:
        """
        Programs with nested weeks.

        Returns:
            SELECT clause for programs with week structure
        """
        return "*, program_weeks(id, week_number, status, week_start_date)"

    @staticmethod
    def programs_with_full_structure() -> str:
        """
        Programs with full nested structure (weeks + workouts).

        Returns:
            SELECT clause for complete program structure
        """
        return """
            *,
            program_weeks(
                id, week_number, status, week_start_date,
                program_workouts(id, day_of_week, workout_name, exercises)
            )
        """

    # ==========================================================================
    # TEMPLATE QUERIES
    # ==========================================================================

    @staticmethod
    def templates_with_weeks() -> str:
        """
        Templates with nested week templates.

        Returns:
            SELECT clause for templates with structure
        """
        return "*, template_weeks(id, week_number, template_workouts(*))"

    # ==========================================================================
    # QUICK MEAL QUERIES
    # ==========================================================================

    @staticmethod
    def quick_meals_with_items() -> str:
        """
        Quick meals with nested items.

        Returns:
            SELECT clause for quick meals with items
        """
        return "*, quick_meal_items(*, foods(name, brand_name))"


class FilterPatterns:
    """
    Common filter patterns for queries.

    Provides standardized filters that are used across multiple services.
    """

    @staticmethod
    def active_only() -> Dict[str, Any]:
        """
        Filter for active records (not deleted).

        Usage:
            .match(FilterPatterns.active_only())
        """
        return {"deleted_at": None}

    @staticmethod
    def user_owned(user_id: str) -> Dict[str, Any]:
        """
        Filter for user-owned records.

        Args:
            user_id: User UUID

        Usage:
            .match(FilterPatterns.user_owned(user_id))
        """
        return {"user_id": user_id, "deleted_at": None}

    @staticmethod
    def date_range(start_field: str = "created_at") -> dict:
        """
        Get field names for date range filtering.

        Args:
            start_field: Field name for date comparison

        Returns:
            Dict with field names for gte/lte operations

        Usage:
            range_fields = FilterPatterns.date_range("logged_at")
            .gte(range_fields["gte"], start_date)
            .lte(range_fields["lte"], end_date)
        """
        return {"gte": start_field, "lte": start_field}


class OrderPatterns:
    """
    Common ordering patterns.

    Provides standardized ordering that's used across services.
    """

    @staticmethod
    def newest_first(field: str = "created_at") -> Dict[str, Any]:
        """
        Order by newest first.

        Args:
            field: Field to order by

        Returns:
            Dict for order() call
        """
        return {"column": field, "desc": True}

    @staticmethod
    def oldest_first(field: str = "created_at") -> Dict[str, Any]:
        """
        Order by oldest first.

        Args:
            field: Field to order by

        Returns:
            Dict for order() call
        """
        return {"column": field, "desc": False}


# ==========================================================================
# EXAMPLE USAGE
# ==========================================================================

"""
# Before (Duplicated across 5+ files):
result = supabase.table("meals")\
    .select("*, meal_items(*, foods(name, brand_name))")\
    .eq("user_id", user_id)\
    .is_("deleted_at", None)\
    .order("logged_at", desc=True)\
    .execute()

# After (Standardized):
from app.database.query_patterns import QueryPatterns, FilterPatterns, OrderPatterns

result = supabase.table("meals")\
    .select(QueryPatterns.meals_with_items_and_foods())\
    .match(FilterPatterns.user_owned(user_id))\
    .order("logged_at", desc=True)\
    .execute()

# Benefits:
# 1. Single source of truth - change once, updates everywhere
# 2. Type-safe - IDE autocomplete
# 3. No N+1 bugs - JOIN pattern always correct
# 4. Easy to test - mock QueryPatterns for different scenarios
# 5. Self-documenting - clear intent from method names
"""
