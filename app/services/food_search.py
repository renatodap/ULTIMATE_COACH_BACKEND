"""
Food Search Service

Handles unified search across all food types:
- Simple ingredients
- Composed meal templates
- Branded products
- User's recent foods
- User's quick meals
"""

from typing import List, Dict, Optional
from supabase import Client
import structlog

logger = structlog.get_logger()


async def search_foods(
    supabase: Client,
    user_id: str,
    query: str,
    limit: int = 20,
    include_recent: bool = False,
) -> Dict:
    """
    Unified food search across all food types.

    Returns foods sorted by:
    1. User's quick meals (if query matches)
    2. Recent foods (if include_recent=True)
    3. Exact name matches
    4. Partial name matches (ranked by relevance)

    Args:
        supabase: Supabase client
        user_id: Current user ID
        query: Search query string
        limit: Maximum results to return (default: 20)
        include_recent: Include user's recent foods (default: False)

    Returns:
        Dict with keys:
        - quick_meals: List of matching quick meals
        - recent_foods: List of recent foods (if include_recent=True)
        - foods: List of matching foods from main database
    """
    results = {
        "quick_meals": [],
        "recent_foods": [],
        "foods": [],
    }

    # 1. Search user's quick meals (if query provided)
    if query:
        try:
            quick_meals_response = (
                supabase.table("quick_meals")
                .select("*, quick_meal_foods(*, food:foods(*))")
                .eq("user_id", user_id)
                .ilike("name", f"%{query}%")
                .order("usage_count", desc=True)
                .order("last_used_at", desc=True)
                .limit(5)
                .execute()
            )

            results["quick_meals"] = quick_meals_response.data or []
            logger.info(
                "quick_meals_search",
                user_id=user_id,
                query=query,
                count=len(results["quick_meals"]),
            )
        except Exception as e:
            logger.error("quick_meals_search_failed", error=str(e))

    # 2. Get recent foods (if requested)
    if include_recent and not query:
        try:
            # Get user's recent meal items to find frequently used foods
            recent_foods_response = (
                supabase.table("meal_items")
                .select("food_id, food:foods(*)")
                .eq("meals.user_id", user_id)  # Join with meals table
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            )

            # Deduplicate by food_id
            seen_food_ids = set()
            for item in recent_foods_response.data or []:
                food_id = item.get("food_id")
                if food_id and food_id not in seen_food_ids:
                    seen_food_ids.add(food_id)
                    if item.get("food"):
                        results["recent_foods"].append(item["food"])

            results["recent_foods"] = results["recent_foods"][:5]  # Limit to 5

            logger.info(
                "recent_foods_fetched",
                user_id=user_id,
                count=len(results["recent_foods"]),
            )
        except Exception as e:
            logger.error("recent_foods_fetch_failed", error=str(e))

    # 3. Search main foods database
    if query:
        try:
            # Use PostgreSQL full-text search for better ranking
            # Search across both English and Portuguese columns
            foods_response = (
                supabase.table("foods")
                .select("*, servings:food_servings(*)")
                .or_(
                    f"name.ilike.%{query}%,"
                    f"brand_name.ilike.%{query}%,"
                    f"name_pt.ilike.%{query}%,"
                    f"brand_name_pt.ilike.%{query}%"
                )
                .or_(f"is_public.eq.true,created_by.eq.{user_id}")  # Public or user's own
                .order("usage_count", desc=True)  # Popular foods first
                .limit(limit)
                .execute()
            )

            results["foods"] = foods_response.data or []

            logger.info(
                "foods_search",
                user_id=user_id,
                query=query,
                count=len(results["foods"]),
            )
        except Exception as e:
            logger.error("foods_search_failed", error=str(e))

    return results


async def get_food_by_id(
    supabase: Client,
    food_id: str,
    user_id: Optional[str] = None,
) -> Optional[Dict]:
    """
    Get a single food by ID with all servings.

    Args:
        supabase: Supabase client
        food_id: Food ID to fetch
        user_id: Current user ID (for permission check)

    Returns:
        Food data with servings, or None if not found/no permission
    """
    try:
        response = (
            supabase.table("foods")
            .select("*, servings:food_servings(*)")
            .eq("id", food_id)
            .maybe_single()
            .execute()
        )

        food = response.data

        if not food:
            return None

        # Check permissions
        if not food.get("is_public") and food.get("created_by") != user_id:
            logger.warning(
                "food_access_denied",
                food_id=food_id,
                user_id=user_id,
            )
            return None

        return food

    except Exception as e:
        logger.error("get_food_by_id_failed", food_id=food_id, error=str(e))
        return None


async def get_recent_foods(
    supabase: Client,
    user_id: str,
    limit: int = 10,
) -> List[Dict]:
    """
    Get user's recently used foods.

    Args:
        supabase: Supabase client
        user_id: Current user ID
        limit: Maximum results (default: 10)

    Returns:
        List of recent food objects
    """
    try:
        # Get recent meal items with food data
        response = (
            supabase.table("meal_items")
            .select("food_id, foods!inner(*)")
            .eq("meals.user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit * 2)  # Fetch more to account for duplicates
            .execute()
        )

        # Deduplicate by food_id
        seen_food_ids = set()
        recent_foods = []

        for item in response.data or []:
            food_id = item.get("food_id")
            if food_id and food_id not in seen_food_ids:
                seen_food_ids.add(food_id)
                recent_foods.append(item["foods"])

                if len(recent_foods) >= limit:
                    break

        logger.info(
            "recent_foods_fetched",
            user_id=user_id,
            count=len(recent_foods),
        )

        return recent_foods

    except Exception as e:
        logger.error("get_recent_foods_failed", user_id=user_id, error=str(e))
        return []


async def increment_food_usage(
    supabase: Client,
    food_id: str,
) -> None:
    """
    Increment usage count for a food (for ranking popular foods).

    Args:
        supabase: Supabase client
        food_id: Food ID to increment
    """
    try:
        # Use RPC for atomic increment
        supabase.rpc(
            "increment_food_usage",
            {"food_id_param": food_id}
        ).execute()

        logger.info("food_usage_incremented", food_id=food_id)

    except Exception as e:
        # Non-critical error, just log
        logger.warning("increment_food_usage_failed", food_id=food_id, error=str(e))
