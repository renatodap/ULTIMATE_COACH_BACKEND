"""
Daily Nutrition Summary Tool

Gets nutrition totals for a specific date with time-aware progress analysis.

Cached with 1min TTL (nutrition changes frequently throughout the day).
"""

from typing import Dict, Any
from datetime import date, datetime, time
from app.services.tools.base_tool import BaseTool


class DailyNutritionSummaryTool(BaseTool):
    """Get daily nutrition totals with goal progress tracking."""

    def get_definition(self) -> Dict[str, Any]:
        """Return tool definition for LLM."""
        return {
            "name": "get_daily_nutrition_summary",
            "description": "Get nutrition totals for a specific date (calories, protein, carbs, fats) with goal progress. Includes meal count, totals, and percentage progress toward daily goals.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format (default: today)"
                    }
                },
                "required": []
            }
        }

    async def execute(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get today's nutrition totals with TIME-AWARE PROGRESS.

        Args:
            user_id: User UUID
            params: Tool parameters (date optional)

        Returns:
            Nutrition summary with totals, goals, and progress
        """
        self.log_execution("get_daily_nutrition_summary", params)

        # Get target date (default: today)
        target_date_str = params.get("date")
        if target_date_str:
            target_date = datetime.fromisoformat(target_date_str).date()
        else:
            target_date = date.today()

        # Check cache first (1min TTL - nutrition changes frequently)
        cache_key = f"daily_nutrition:{user_id}:{target_date.isoformat()}"
        cached_result = await self.get_from_cache(cache_key)
        if cached_result:
            self.logger.debug("cache_hit", cache_key=cache_key)
            return cached_result

        try:
            # Query meals for this date
            start_of_day = datetime.combine(target_date, time.min)
            end_of_day = datetime.combine(target_date, time.max)

            result = self.supabase.table("meals")\
                .select("id, name, meal_type, logged_at, total_calories, total_protein_g, total_carbs_g, total_fat_g")\
                .eq("user_id", user_id)\
                .gte("logged_at", start_of_day.isoformat())\
                .lte("logged_at", end_of_day.isoformat())\
                .order("logged_at", desc=False)\
                .execute()

            # Calculate totals
            total_calories = sum(float(m.get("total_calories") or 0) for m in result.data) if result.data else 0
            total_protein = sum(float(m.get("total_protein_g") or 0) for m in result.data) if result.data else 0
            total_carbs = sum(float(m.get("total_carbs_g") or 0) for m in result.data) if result.data else 0
            total_fat = sum(float(m.get("total_fat_g") or 0) for m in result.data) if result.data else 0

            # Get user's goals (using basic query, not recursive tool call)
            profile_result = self.supabase.table("profiles")\
                .select("daily_calorie_goal, daily_protein_goal, timezone")\
                .eq("id", user_id)\
                .single()\
                .execute()

            profile = profile_result.data if profile_result.data else {}
            daily_cal_goal = profile.get("daily_calorie_goal", 2000)
            daily_protein_goal = profile.get("daily_protein_goal", 150)

            # Calculate progress
            calories_percent = round((total_calories / daily_cal_goal * 100) if daily_cal_goal else 0)
            protein_percent = round((total_protein / daily_protein_goal * 100) if daily_protein_goal else 0)

            response = {
                "date": target_date.isoformat(),
                "meal_count": len(result.data) if result.data else 0,
                "totals": {
                    "calories": round(total_calories),
                    "protein_g": round(total_protein, 1),
                    "carbs_g": round(total_carbs, 1),
                    "fat_g": round(total_fat, 1)
                },
                "goals": {
                    "calories": daily_cal_goal,
                    "protein_g": daily_protein_goal
                },
                "progress": {
                    "calories_percent": calories_percent,
                    "protein_percent": protein_percent
                },
                "message": "No meals logged for this date yet." if not result.data else f"{len(result.data)} meals logged"
            }

            # Cache for 1 minute
            await self.set_in_cache(cache_key, response, ttl=60)
            self.logger.debug("nutrition_summary_cached", cache_key=cache_key, ttl=60)

            return response

        except Exception as e:
            self.log_error("get_daily_nutrition_summary", e, params)
            return {"error": str(e)}
