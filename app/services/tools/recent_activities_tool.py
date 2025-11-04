"""
Recent Activities Tool

Gets user's recent workout/activity history with metrics.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from app.services.tools.base_tool import BaseTool


class RecentActivitiesTool(BaseTool):
    """Get user's recent activities."""

    def get_definition(self) -> Dict[str, Any]:
        """Return tool definition for LLM."""
        return {
            "name": "get_recent_activities",
            "description": "Get user's recent workouts and activities history. Returns activities from past N days with category, duration, calories burned, intensity (METs), and category-specific metrics.",
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
                        "description": "Max number of activities to return",
                        "default": 20
                    }
                },
                "required": []
            }
        }

    async def execute(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get recent activities for user."""
        self.log_execution("get_recent_activities", params)

        try:
            days = params.get("days", 7)
            limit = min(params.get("limit", 20), 50)

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            result = self.supabase.table("activities")\
                .select("*")\
                .eq("user_id", user_id)\
                .gte("start_time", cutoff_date)\
                .order("start_time", desc=True)\
                .limit(limit)\
                .execute()

            if not result.data:
                return {
                    "days_searched": days,
                    "activity_count": 0,
                    "activities": [],
                    "message": f"No activities logged in the past {days} days."
                }

            activities = []
            for activity in result.data:
                activities.append({
                    "id": activity["id"],
                    "activity_name": activity["activity_name"],
                    "category": activity["category"],
                    "start_time": activity["start_time"],
                    "duration_minutes": activity.get("duration_minutes"),
                    "calories_burned": activity.get("calories_burned"),
                    "intensity_mets": float(activity.get("intensity_mets") or 0),
                    "metrics": activity.get("metrics", {}),
                    "notes": activity.get("notes")
                })

            return {
                "days_searched": days,
                "activity_count": len(activities),
                "activities": activities
            }

        except Exception as e:
            self.log_error("get_recent_activities", e, params)
            return {"error": str(e)}
