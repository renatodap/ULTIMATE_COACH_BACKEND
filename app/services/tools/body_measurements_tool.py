"""
Body Measurements Tool

Gets user's body measurement history (weight, body fat, etc.).
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from app.services.tools.base_tool import BaseTool


class BodyMeasurementsTool(BaseTool):
    """Get user's body measurements history."""

    def get_definition(self) -> Dict[str, Any]:
        """Return tool definition for LLM."""
        return {
            "name": "get_body_measurements",
            "description": "Get user's body measurements history including weight (kg), body fat percentage, and notes. Returns measurements from past N days ordered by date, including latest weight.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back",
                        "default": 30
                    }
                },
                "required": []
            }
        }

    async def execute(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get body measurements for user."""
        self.log_execution("get_body_measurements", params)

        try:
            days = params.get("days", 30)
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            result = self.supabase.table("body_metrics")\
                .select("id, recorded_at, weight_kg, body_fat_percentage, notes")\
                .eq("user_id", user_id)\
                .gte("recorded_at", cutoff_date)\
                .order("recorded_at", desc=True)\
                .execute()

            if not result.data:
                return {
                    "days_searched": days,
                    "measurement_count": 0,
                    "measurements": [],
                    "latest_weight": None,
                    "message": f"No measurements recorded in the past {days} days."
                }

            measurements = []
            for measurement in result.data:
                measurements.append({
                    "id": measurement["id"],
                    "recorded_at": measurement["recorded_at"],
                    "weight_kg": float(measurement.get("weight_kg") or 0),
                    "body_fat_percentage": float(measurement.get("body_fat_percentage") or 0) if measurement.get("body_fat_percentage") else None,
                    "notes": measurement.get("notes")
                })

            latest_weight = measurements[0]["weight_kg"] if measurements else None

            return {
                "days_searched": days,
                "measurement_count": len(measurements),
                "measurements": measurements,
                "latest_weight": latest_weight
            }

        except Exception as e:
            self.log_error("get_body_measurements", e, params)
            return {"error": str(e)}
