"""
User Profile Tool

Gets user's profile including goals, body stats, macro targets,
dietary restrictions, and preferences.

Cached with 5min TTL (profiles change infrequently).
"""

from typing import Dict, Any
from app.services.tools.base_tool import BaseTool


class UserProfileTool(BaseTool):
    """Get user's profile data for personalized coaching."""

    def get_definition(self) -> Dict[str, Any]:
        """Return tool definition for LLM."""
        return {
            "name": "get_user_profile",
            "description": "Get user's profile including goals, body stats, macro targets, dietary restrictions, and preferences. Use this to personalize advice.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "include_goals": {
                        "type": "boolean",
                        "description": "Include user's fitness goals",
                        "default": True
                    }
                },
                "required": []
            }
        }

    async def execute(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get user profile with goals and preferences.

        Args:
            user_id: User UUID
            params: Tool parameters (include_goals optional)

        Returns:
            User profile data with goals and macro targets
        """
        self.log_execution("get_user_profile", params)

        # Check cache first (5min TTL)
        cache_key = f"user_profile:{user_id}"
        cached_result = await self.get_from_cache(cache_key)
        if cached_result:
            self.logger.debug("cache_hit", cache_key=cache_key)
            return cached_result

        try:
            # Query user profile from database
            result = self.supabase.table("profiles")\
                .select("*")\
                .eq("id", user_id)\
                .single()\
                .execute()

            if not result.data:
                return {"error": "Profile not found"}

            profile = result.data

            # Format response with relevant fields
            formatted_profile = {
                "full_name": profile.get("full_name"),
                "primary_goal": profile.get("primary_goal"),
                "experience_level": profile.get("experience_level"),
                "daily_calorie_goal": profile.get("daily_calorie_goal"),
                "daily_protein_goal": profile.get("daily_protein_goal"),
                "daily_carbs_goal": profile.get("daily_carbs_goal"),
                "daily_fat_goal": profile.get("daily_fat_goal"),
                "unit_system": profile.get("unit_system", "imperial"),
                "language": profile.get("language", "en")
            }

            # Cache for 5 minutes
            await self.set_in_cache(cache_key, formatted_profile, ttl=300)
            self.logger.debug("profile_cached", cache_key=cache_key, ttl=300)

            return formatted_profile

        except Exception as e:
            self.log_error("get_user_profile", e, params)
            return {"error": str(e)}
