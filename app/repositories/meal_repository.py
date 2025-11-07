"""
Meal Repository

Handles all meal-related database operations.

Responsibilities:
- Meal CRUD operations
- Meal queries with items and foods
- Daily nutrition summaries
- Recent meals queries

Usage:
    repo = MealRepository(supabase)
    meals = await repo.get_recent_meals(user_id, days=7)
    meal = await repo.create_meal(user_id, meal_data)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, time, timedelta
from app.repositories.base_repository import BaseRepository
from app.database.query_patterns import QueryPatterns, FilterPatterns


class MealRepository(BaseRepository):
    """Repository for meal operations."""

    async def get_meal(self, meal_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get meal by ID with items and foods.

        Args:
            meal_id: Meal UUID
            user_id: User UUID (for ownership verification)

        Returns:
            Meal with items and foods
        """
        return await self.get_one(
            "meals",
            {"id": meal_id, "user_id": user_id, "deleted_at": None},
            select=QueryPatterns.meals_with_items_and_foods()
        )

    async def get_recent_meals(
        self,
        user_id: str,
        days: int = 7,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent meals for user.

        Args:
            user_id: User UUID
            days: Number of days to look back
            limit: Maximum number of meals

        Returns:
            List of meals
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        query = self.supabase.table("meals")\
            .select(QueryPatterns.meals_basic())\
            .eq("user_id", user_id)\
            .is_("deleted_at", None)\
            .gte("logged_at", cutoff_date)\
            .order("logged_at", desc=True)\
            .limit(limit)

        result = query.execute()
        return result.data if result.data else []

    async def get_meals_for_date(
        self,
        user_id: str,
        target_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get all meals for a specific date.

        Args:
            user_id: User UUID
            target_date: Date to query

        Returns:
            List of meals for that date
        """
        start_of_day = datetime.combine(target_date, time.min)
        end_of_day = datetime.combine(target_date, time.max)

        query = self.supabase.table("meals")\
            .select(QueryPatterns.meals_with_items_and_foods())\
            .eq("user_id", user_id)\
            .is_("deleted_at", None)\
            .gte("logged_at", start_of_day.isoformat())\
            .lte("logged_at", end_of_day.isoformat())\
            .order("logged_at", desc=False)

        result = query.execute()
        return result.data if result.data else []

    async def create_meal(
        self,
        user_id: str,
        meal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new meal.

        Args:
            user_id: User UUID
            meal_data: Meal data

        Returns:
            Created meal
        """
        meal_data["user_id"] = user_id
        return await self.create("meals", meal_data)

    async def update_meal(
        self,
        meal_id: str,
        user_id: str,
        meal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a meal.

        Args:
            meal_id: Meal UUID
            user_id: User UUID (for ownership verification)
            meal_data: Update data

        Returns:
            Updated meal
        """
        return await self.update(
            "meals",
            {"id": meal_id, "user_id": user_id},
            meal_data
        )

    async def delete_meal(self, meal_id: str, user_id: str) -> bool:
        """
        Soft delete a meal.

        Args:
            meal_id: Meal UUID
            user_id: User UUID (for ownership verification)

        Returns:
            True if successful
        """
        return await self.delete(
            "meals",
            {"id": meal_id, "user_id": user_id},
            soft=True
        )

    async def calculate_daily_totals(
        self,
        user_id: str,
        target_date: date
    ) -> Dict[str, float]:
        """
        Calculate nutrition totals for a specific date.

        Args:
            user_id: User UUID
            target_date: Date to calculate

        Returns:
            Dict with calories, protein, carbs, fat totals
        """
        meals = await self.get_meals_for_date(user_id, target_date)

        total_calories = sum(float(m.get("total_calories") or 0) for m in meals)
        total_protein = sum(float(m.get("total_protein_g") or 0) for m in meals)
        total_carbs = sum(float(m.get("total_carbs_g") or 0) for m in meals)
        total_fat = sum(float(m.get("total_fat_g") or 0) for m in meals)

        return {
            "calories": round(total_calories),
            "protein_g": round(total_protein, 1),
            "carbs_g": round(total_carbs, 1),
            "fat_g": round(total_fat, 1),
            "meal_count": len(meals)
        }
