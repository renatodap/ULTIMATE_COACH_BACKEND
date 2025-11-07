"""
Progress Trend Tool

Calculates progress trends for metrics over time (weight, calories, protein, etc.).
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from app.services.tools.base_tool import BaseTool


class ProgressTrendTool(BaseTool):
    """Calculate progress trends for metrics."""

    def get_definition(self) -> Dict[str, Any]:
        """Return tool definition for LLM."""
        return {
            "name": "calculate_progress_trend",
            "description": "Calculate progress trend for weight, calories, or protein over time. Analyzes historical data to show first vs last value, absolute change, percentage change, and trend direction (increasing/decreasing/stable). Requires at least 2 data points.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "description": "Metric to analyze (e.g., 'weight', 'calories', 'protein')"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to analyze",
                        "default": 30
                    }
                },
                "required": ["metric"]
            }
        }

    async def execute(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate trend for specified metric."""
        self.log_execution("calculate_progress_trend", params)

        try:
            metric = params.get("metric", "").lower()
            days = params.get("days", 30)

            if metric == "weight":
                return await self._calculate_weight_trend(user_id, days)
            elif metric in ["calories", "protein"]:
                return await self._calculate_nutrition_trend(user_id, metric, days)
            else:
                return {"error": f"Unknown metric: {metric}. Supported: weight, calories, protein"}

        except Exception as e:
            self.log_error("calculate_progress_trend", e, params)
            return {"error": str(e)}

    async def _calculate_weight_trend(self, user_id: str, days: int) -> Dict[str, Any]:
        """Calculate weight trend."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        result = self.supabase.table("body_metrics")\
            .select("recorded_at, weight_kg")\
            .eq("user_id", user_id)\
            .gte("recorded_at", cutoff_date)\
            .order("recorded_at", desc=False)\
            .execute()

        if not result.data or len(result.data) < 2:
            return {"error": "Need at least 2 weight measurements for trend analysis"}

        first = result.data[0]
        last = result.data[-1]

        first_weight = float(first["weight_kg"])
        last_weight = float(last["weight_kg"])

        change = last_weight - first_weight
        percent_change = (change / first_weight * 100) if first_weight > 0 else 0

        direction = "stable"
        if abs(percent_change) > 2:
            direction = "decreasing" if change < 0 else "increasing"

        return {
            "metric": "weight",
            "days_analyzed": days,
            "data_points": len(result.data),
            "first_value": round(first_weight, 1),
            "last_value": round(last_weight, 1),
            "change": round(change, 1),
            "percent_change": round(percent_change, 1),
            "direction": direction,
            "first_date": first["recorded_at"],
            "last_date": last["recorded_at"]
        }

    async def _calculate_nutrition_trend(self, user_id: str, metric: str, days: int) -> Dict[str, Any]:
        """Calculate nutrition metric trend."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        result = self.supabase.table("meals")\
            .select("logged_at, total_calories, total_protein_g")\
            .eq("user_id", user_id)\
            .gte("logged_at", cutoff_date)\
            .order("logged_at", desc=False)\
            .execute()

        if not result.data or len(result.data) < 2:
            return {"error": f"Need at least 2 meals for {metric} trend analysis"}

        # Group by date and sum
        from collections import defaultdict
        daily_values = defaultdict(float)

        for meal in result.data:
            date = meal["logged_at"][:10]
            value = float(meal.get(f"total_{metric}" if metric != "calories" else "total_calories", 0))
            daily_values[date] += value

        dates = sorted(daily_values.keys())
        if len(dates) < 2:
            return {"error": f"Need at least 2 days of data for {metric} trend"}

        first_value = daily_values[dates[0]]
        last_value = daily_values[dates[-1]]

        change = last_value - first_value
        percent_change = (change / first_value * 100) if first_value > 0 else 0

        direction = "stable"
        if abs(percent_change) > 5:
            direction = "decreasing" if change < 0 else "increasing"

        return {
            "metric": metric,
            "days_analyzed": days,
            "data_points": len(dates),
            "first_value": round(first_value, 1),
            "last_value": round(last_value, 1),
            "change": round(change, 1),
            "percent_change": round(percent_change, 1),
            "direction": direction,
            "first_date": dates[0],
            "last_date": dates[-1]
        }
