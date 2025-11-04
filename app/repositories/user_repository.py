"""
User Repository

Handles all user and profile database operations.

Responsibilities:
- User profile queries
- User settings
- User preferences
- Authentication-related queries

Usage:
    repo = UserRepository(supabase)
    profile = await repo.get_profile(user_id)
    await repo.update_language(user_id, "es")
"""

from typing import Dict, Any, Optional
from app.repositories.base_repository import BaseRepository
from app.database.query_patterns import QueryPatterns


class UserRepository(BaseRepository):
    """Repository for user and profile operations."""

    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile.

        Args:
            user_id: User UUID

        Returns:
            User profile dict or None
        """
        return await self.get_one(
            "profiles",
            {"id": user_id},
            select=QueryPatterns.profile_full()
        )

    async def get_profile_essential(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get essential profile fields (for coaching).

        Args:
            user_id: User UUID

        Returns:
            Essential profile fields
        """
        return await self.get_one(
            "profiles",
            {"id": user_id},
            select=QueryPatterns.profile_essential()
        )

    async def update_profile(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user profile.

        Args:
            user_id: User UUID
            data: Update data

        Returns:
            Updated profile
        """
        return await self.update(
            "profiles",
            {"id": user_id},
            data
        )

    async def update_language(self, user_id: str, language: str) -> Dict[str, Any]:
        """
        Update user's language preference.

        Args:
            user_id: User UUID
            language: Language code (e.g., "en", "es")

        Returns:
            Updated profile
        """
        return await self.update(
            "profiles",
            {"id": user_id},
            {"language": language}
        )

    async def update_goals(
        self,
        user_id: str,
        calorie_goal: Optional[int] = None,
        protein_goal: Optional[int] = None,
        carbs_goal: Optional[int] = None,
        fat_goal: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update user's macro goals.

        Args:
            user_id: User UUID
            calorie_goal: Daily calorie goal
            protein_goal: Daily protein goal (g)
            carbs_goal: Daily carbs goal (g)
            fat_goal: Daily fat goal (g)

        Returns:
            Updated profile
        """
        data = {}
        if calorie_goal is not None:
            data["daily_calorie_goal"] = calorie_goal
        if protein_goal is not None:
            data["daily_protein_goal"] = protein_goal
        if carbs_goal is not None:
            data["daily_carbs_goal"] = carbs_goal
        if fat_goal is not None:
            data["daily_fat_goal"] = fat_goal

        return await self.update(
            "profiles",
            {"id": user_id},
            data
        )

    async def get_timezone(self, user_id: str) -> str:
        """
        Get user's timezone.

        Args:
            user_id: User UUID

        Returns:
            Timezone string (e.g., "America/New_York")
        """
        profile = await self.get_one(
            "profiles",
            {"id": user_id},
            select="timezone"
        )

        return profile.get("timezone", "UTC") if profile else "UTC"

    async def get_unit_system(self, user_id: str) -> str:
        """
        Get user's unit system preference.

        Args:
            user_id: User UUID

        Returns:
            Unit system ("metric" or "imperial")
        """
        profile = await self.get_one(
            "profiles",
            {"id": user_id},
            select="unit_system"
        )

        return profile.get("unit_system", "imperial") if profile else "imperial"
