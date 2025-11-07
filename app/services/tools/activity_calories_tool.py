"""
Activity Calories Estimation Tool

Estimates calories burned for activities using METs (Metabolic Equivalent of Task).
"""

from typing import Dict, Any
from app.services.tools.base_tool import BaseTool


class ActivityCaloriesTool(BaseTool):
    """Estimate calories burned for activities."""

    def get_definition(self) -> Dict[str, Any]:
        """Return tool definition for LLM."""
        return {
            "name": "estimate_activity_calories",
            "description": "Estimate calories burned for an activity using METs (Metabolic Equivalent of Task). Requires activity type, duration, and user weight. Returns estimated calories burned.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "activity_type": {
                        "type": "string",
                        "description": "Type of activity (e.g., 'running', 'cycling', 'swimming')"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Duration in minutes"
                    },
                    "intensity": {
                        "type": "string",
                        "description": "Intensity level: 'light', 'moderate', 'vigorous'",
                        "default": "moderate"
                    }
                },
                "required": ["activity_type", "duration_minutes"]
            }
        }

    # METs database (common activities)
    METS_DATABASE = {
        "walking": {"light": 2.5, "moderate": 3.5, "vigorous": 4.5},
        "running": {"light": 6.0, "moderate": 8.0, "vigorous": 10.0},
        "cycling": {"light": 4.0, "moderate": 6.0, "vigorous": 8.0},
        "swimming": {"light": 5.0, "moderate": 7.0, "vigorous": 9.0},
        "weightlifting": {"light": 3.0, "moderate": 5.0, "vigorous": 6.0},
        "yoga": {"light": 2.0, "moderate": 3.0, "vigorous": 4.0},
        "hiit": {"light": 8.0, "moderate": 10.0, "vigorous": 12.0},
        "basketball": {"light": 4.5, "moderate": 6.5, "vigorous": 8.0},
        "tennis": {"light": 5.0, "moderate": 7.0, "vigorous": 8.0},
        "soccer": {"light": 5.0, "moderate": 7.0, "vigorous": 10.0},
    }

    async def execute(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate calories burned."""
        self.log_execution("estimate_activity_calories", params)

        try:
            activity_type = params.get("activity_type", "").lower()
            duration_minutes = params.get("duration_minutes", 0)
            intensity = params.get("intensity", "moderate").lower()

            if duration_minutes <= 0:
                return {"error": "Duration must be greater than 0"}

            # Get user weight
            profile = await self._get_user_weight(user_id)
            weight_kg = profile.get("weight_kg", 70)  # Default 70kg if not found

            # Find METs value
            mets = self._get_mets(activity_type, intensity)

            if not mets:
                return {
                    "error": f"Unknown activity: {activity_type}. Try: running, cycling, swimming, walking, etc."
                }

            # Calculate calories: METs × weight (kg) × duration (hours)
            duration_hours = duration_minutes / 60
            calories_burned = mets * weight_kg * duration_hours

            return {
                "activity_type": activity_type,
                "duration_minutes": duration_minutes,
                "intensity": intensity,
                "mets": mets,
                "weight_kg": weight_kg,
                "calories_burned": round(calories_burned),
                "formula": f"{mets} METs × {weight_kg}kg × {duration_hours:.2f}h = {round(calories_burned)} cal"
            }

        except Exception as e:
            self.log_error("estimate_activity_calories", e, params)
            return {"error": str(e)}

    def _get_mets(self, activity_type: str, intensity: str) -> float:
        """Get METs value for activity."""
        # Try exact match
        if activity_type in self.METS_DATABASE:
            return self.METS_DATABASE[activity_type].get(intensity,
                self.METS_DATABASE[activity_type]["moderate"])

        # Try partial match
        for activity, intensities in self.METS_DATABASE.items():
            if activity in activity_type or activity_type in activity:
                return intensities.get(intensity, intensities["moderate"])

        return None

    async def _get_user_weight(self, user_id: str) -> Dict[str, Any]:
        """Get user's latest weight."""
        try:
            # Try to get latest body measurement
            result = self.supabase.table("body_metrics")\
                .select("weight_kg")\
                .eq("user_id", user_id)\
                .order("recorded_at", desc=True)\
                .limit(1)\
                .execute()

            if result.data and len(result.data) > 0:
                return {"weight_kg": float(result.data[0].get("weight_kg", 70))}

            # Fallback to profile
            profile = self.supabase.table("profiles")\
                .select("weight_kg")\
                .eq("id", user_id)\
                .single()\
                .execute()

            if profile.data:
                return {"weight_kg": float(profile.data.get("weight_kg", 70))}

            return {"weight_kg": 70}  # Default

        except Exception:
            return {"weight_kg": 70}  # Default on error
