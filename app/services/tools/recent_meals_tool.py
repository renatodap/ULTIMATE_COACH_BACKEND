"""
Recent Meals Tool

Gets user's recent meal history with full nutrition breakdown.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from app.services.tools.base_tool import BaseTool


class RecentMealsTool(BaseTool):
    """Get user's recent meal history."""

    def get_definition(self) -> Dict[str, Any]:
        """Return tool definition for LLM."""
        return {
            "name": "get_recent_meals",
            "description": "Get user's recent meal history with full nutrition breakdown. Returns meals from the past N days with name, meal type, nutrition totals, and notes.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back",
                        "default": 7
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of meals to return",
                        "default": 20
                    }
                },
                "required": []
            }
        }

    async def execute(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get recent meals for user.

        Args:
            user_id: User UUID
            params: days (int), limit (int)

        Returns:
            Recent meals with nutrition data
        """
        self.log_execution("get_recent_meals", params)

        try:
            days = params.get("days", 7)
            limit = min(params.get("limit", 20), 50)  # Max 50

            # Query recent meals
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            result = self.supabase.table("meals")\
                .select("id, name, meal_type, logged_at, total_calories, total_protein_g, total_carbs_g, total_fat_g, notes")\
                .eq("user_id", user_id)\
                .gte("logged_at", cutoff_date)\
                .order("logged_at", desc=True)\
                .limit(limit)\
                .execute()

            if not result.data:
                return {
                    "days_searched": days,
                    "meal_count": 0,
                    "meals": [],
                    "message": f"No meals logged in the past {days} days."
                }

            # Format meals
            meals = []
            for meal in result.data:
                meals.append({
                    "id": meal["id"],
                    "name": meal.get("name"),
                    "meal_type": meal["meal_type"],
                    "logged_at": meal["logged_at"],
                    "nutrition": {
                        "calories": round(float(meal.get("total_calories") or 0)),
                        "protein_g": round(float(meal.get("total_protein_g") or 0), 1),
                        "carbs_g": round(float(meal.get("total_carbs_g") or 0), 1),
                        "fat_g": round(float(meal.get("total_fat_g") or 0), 1)
                    },
                    "notes": meal.get("notes")
                })

            return {
                "days_searched": days,
                "meal_count": len(meals),
                "meals": meals
            }

        except Exception as e:
            self.log_error("get_recent_meals", e, params)
            return {"error": str(e)}
